import email
import imaplib
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailClient:

    def __init__(self):
        self.smtp_server = None
        self.imap_server = None
        self.smtp_port = 587
        self.imap_port = 993
        self.username = None
        self.password = None

    def configure(self, username, password, smtp_server, smtp_port=587,
                  imap_server=None, imap_port=993):
        self.username = username
        self.password = password
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server or smtp_server
        self.imap_port = imap_port
        return {'configured': True}

    def send(self, recipient, subject, body, attachments=None):
        if not self.smtp_server:
            return {'error': 'SMTP not configured'}
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        if attachments:
            for path in attachments:
                with open(path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename="{path.split(chr(92))[-1]}"')
                    msg.attach(part)
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as s:
                s.starttls()
                s.login(self.username, self.password)
                s.send_message(msg)
            return {'sent': True, 'to': recipient, 'subject': subject}
        except Exception as e:
            return {'error': str(e)}

    def inbox(self, folder="INBOX", limit=20):
        if not self.imap_server:
            return {'error': 'IMAP not configured'}
        try:
            with imaplib.IMAP4_SSL(self.imap_server,
                                   self.imap_port) as m:
                m.login(self.username, self.password)
                m.select(folder)
                _, data = m.search(None, 'ALL')
                messages = []
                for num in data[0].split()[-limit:]:
                    _, msg_data = m.fetch(num, '(RFC822)')
                    msg = email.message_from_bytes(msg_data[0][1])
                    messages.append({
                        'id': num.decode(),
                        'from': msg['From'],
                        'subject': msg['Subject'],
                        'date': msg['Date']
                    })
                return messages
        except Exception as e:
            return {'error': str(e)}

    def search(self, query):
        return {'error': 'Search requires IMAP SEARCH implementation'}


def run(action, **kwargs):
    ec = EmailClient()
    method = getattr(ec, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
