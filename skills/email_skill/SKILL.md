---
name: email
description: Send, read, search, and manage emails via SMTP/IMAP with attachment support
version: 1.0.0
---

# Email Skill

## Description
Full email client capability supporting SMTP for sending and IMAP for reading. Handles attachments, folder navigation, and email search.

## Triggers
- send email
- check inbox
- read emails
- email search
- compose email

## Usage
Use send(recipient, subject, body, attachments=None) to send, inbox(folder="INBOX", limit=20) to read, and search(query) to find messages. SMTP and IMAP servers must be configured.
