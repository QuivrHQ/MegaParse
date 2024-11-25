import ssl

from megaparse_sdk.config import SSLConfig


def load_ssl_cxt(ssl_config: SSLConfig):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    if ssl_config.ca_cert_file:
        context.load_verify_locations(cafile=ssl_config.ca_cert_file)
    context.load_cert_chain(
        certfile=ssl_config.ssl_cert_file, keyfile=ssl_config.ssl_key_file
    )
    return context
