"""Loopback-only, test-domain-only SMTP sink. Messages remain in memory."""
import socketserver
import ssl


class _Handler(socketserver.StreamRequestHandler):
    def reply(self, line):
        self.wfile.write(line + b'\r\n')
        self.wfile.flush()

    def handle(self):
        self.reply(b'220 local-test-sink ESMTP')
        recipient = None
        tls_active = False
        while True:
            raw = self.rfile.readline(8192)
            if not raw:
                return
            cmd = raw.strip()
            upper = cmd.upper()
            if upper.startswith((b'EHLO ', b'HELO ')):
                self.wfile.write(b'250-local-test-sink\r\n250-STARTTLS\r\n250 SIZE 1048576\r\n')
                self.wfile.flush()
            elif upper == b'STARTTLS':
                self.reply(b'220 Ready for TLS')
                self.connection = self.server.tls_context.wrap_socket(self.connection, server_side=True)
                self.rfile = self.connection.makefile('rb')
                self.wfile = self.connection.makefile('wb')
                tls_active = True
            elif upper.startswith(b'MAIL FROM:'):
                recipient = None
                self.reply(b'250 OK' if tls_active else b'530 STARTTLS required')
            elif upper.startswith(b'RCPT TO:'):
                address = cmd[8:].strip().strip(b'<>').lower()
                if not address.endswith(b'@example.test'):
                    self.reply(b'550 Test domain only')
                else:
                    recipient = address
                    self.reply(b'250 OK')
            elif upper == b'DATA' and recipient:
                self.reply(b'354 End with dot')
                lines = []
                while True:
                    line = self.rfile.readline(8192)
                    if line in (b'.\r\n', b''):
                        break
                    lines.append(line)
                self.server.messages.append((recipient, b''.join(lines)))
                self.reply(b'250 Accepted locally')
            elif upper == b'QUIT':
                self.reply(b'221 Bye')
                return
            else:
                self.reply(b'502 Unsupported')


class CaptureServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, certificate, key):
        super().__init__(('127.0.0.1', 0), _Handler)
        self.messages = []
        self.tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.tls_context.load_cert_chain(certificate, key)
