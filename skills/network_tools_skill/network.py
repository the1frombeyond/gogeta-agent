import socket
import subprocess


class NetworkTools:

    def ping(self, host):
        try:
            result = subprocess.run(['ping', '-n', '4', host],
                                    capture_output=True, text=True,
                                    timeout=60)
            return {'stdout': result.stdout,
                    'returncode': result.returncode}
        except subprocess.TimeoutExpired:
            return {'error': 'Ping timed out'}
        except FileNotFoundError:
            return {'error': 'ping not available'}

    def traceroute(self, host):
        try:
            result = subprocess.run(['tracert', host],
                                    capture_output=True, text=True,
                                    timeout=120)
            return {'stdout': result.stdout,
                    'returncode': result.returncode}
        except FileNotFoundError:
            return {'error': 'tracert not available'}

    def dns_lookup(self, domain):
        try:
            ips = socket.getaddrinfo(domain, None)
            return {'ips': list(set(i[4][0] for i in ips))}
        except socket.gaierror as e:
            return {'error': str(e)}

    def port_scan(self, host, ports):
        results = {}
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            results[port] = sock.connect_ex((host, port)) == 0
            sock.close()
        return results

    def http_check(self, url):
        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=10) as r:
                return {'status': r.status, 'headers': dict(r.headers)}
        except Exception as e:
            return {'error': str(e)}


def run(action, **kwargs):
    nt = NetworkTools()
    method = getattr(nt, action, None)
    if method:
        return method(**kwargs)
    return {'error': f'Unknown action: {action}'}
