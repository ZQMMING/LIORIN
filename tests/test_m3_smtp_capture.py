from datetime import datetime, timedelta, timezone
from email import message_from_bytes, policy
import ipaddress
import smtplib
import threading
from unittest.mock import patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from tests.m3_smtp_capture import CaptureServer
from tongshu.services.email_auth import send_login_code


def test_actual_smtp_delivery_stays_in_loopback_sink(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost')])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(subject)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=1)).not_valid_after(now + timedelta(days=1))
            .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
            .sign(key, hashes.SHA256()))
    cert_path, key_path = tmp_path / 'cert.pem', tmp_path / 'key.pem'
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(key.private_bytes(serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    issued = []

    class Store:
        def can_send(self, email): return True
        def issue(self, email, code): issued.append((email, code))
        def revoke(self, email, code): issued.clear()

    with CaptureServer(str(cert_path), str(key_path)) as sink:
        thread = threading.Thread(target=sink.serve_forever, daemon=True)
        thread.start()
        try:
            config = {'TONGSHU_SMTP_HOST': '127.0.0.1', 'TONGSHU_SMTP_PORT': str(sink.server_address[1]),
                      'TONGSHU_SMTP_FROM': 'service@example.test', 'TONGSHU_EMAIL_AUTH_SECRET': 'x' * 32}
            with patch.dict('os.environ', config, clear=True):
                send_login_code(Store(), 'person@example.test')
            assert len(sink.messages) == len(issued) == 1
            message = message_from_bytes(sink.messages[0][1], policy=policy.default)
            if issued[0][1] not in message.get_body(preferencelist=('plain',)).get_content():
                raise AssertionError('captured message did not contain the issued test code')
            with smtplib.SMTP('127.0.0.1', sink.server_address[1], timeout=3) as smtp:
                smtp.starttls()
                smtp.mail('service@example.test')
                assert smtp.rcpt('someone@external.invalid')[0] == 550
            assert len(sink.messages) == 1
        finally:
            sink.shutdown()
            thread.join(timeout=5)
