import ssl
from pathlib import Path


def load_ssl_cxt(cert_file: str | Path, key_file: str | Path, ca_cert_file: str | Path):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.load_verify_locations(cafile=ca_cert_file)
    context.load_cert_chain(certfile=cert_file, keyfile=key_file)
    return context
