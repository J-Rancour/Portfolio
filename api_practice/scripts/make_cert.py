"""Create a self-signed certificate for local HTTPS/WSS (tutorial step 10).

    python scripts/make_cert.py
    uvicorn app.main:app --port 8443 --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem

The OpenSSL one-liner that does the same thing:
    openssl req -x509 -newkey rsa:2048 -nodes -days 30 -keyout certs/key.pem -out certs/cert.pem \
        -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
"""

import datetime as dt
import ipaddress
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

out = Path(__file__).resolve().parent.parent / "certs"
out.mkdir(exist_ok=True)

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
now = dt.datetime.now(dt.UTC)
cert = (
    x509.CertificateBuilder()
    .subject_name(name)
    .issuer_name(name)  # issuer == subject: that's what "self-signed" means
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(now - dt.timedelta(minutes=5))
    .not_valid_after(now + dt.timedelta(days=30))
    # Clients match the hostname against the SAN, not the CN.
    .add_extension(
        x509.SubjectAlternativeName([x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]),
        critical=False,
    )
    # CA=True so it can act as its own trust anchor when passed as --cafile.
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .sign(key, hashes.SHA256())
)

(out / "key.pem").write_bytes(
    key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
)
(out / "cert.pem").write_bytes(cert.public_bytes(serialization.Encoding.PEM))
print(f"Wrote {out / 'cert.pem'} and {out / 'key.pem'} (valid 30 days, localhost + 127.0.0.1)")
