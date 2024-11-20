import nats
import pytest
from api.utils.load_ssl import load_ssl_cxt
from megaparse_sdk.schema.mp_inputs import (
    FileInput,
    MPInput,
    ParseFileConfig,
    ParseFileInput,
)
from megaparse_sdk.schema.mp_outputs import MPOutput, MPOutputType


@pytest.mark.asyncio
async def test_parse_file_nats():
    NATS_URL = "nats://test@localhost:4222"
    NATS_SUBJECT = "parse.file"

    SSL_CERT_FILE = "./tests/certs/client-cert.pem"
    SSL_KEY_FILE = "./tests/certs/client-key.pem"
    CA_CERT_FILE = "/Users/amine/Library/Application Support/mkcert/rootCA.pem"
    ctx = load_ssl_cxt(
        cert_file=SSL_CERT_FILE, ca_cert_file=CA_CERT_FILE, key_file=SSL_KEY_FILE
    )
    nc = await nats.connect(NATS_URL, tls=ctx)

    with open("./tests/pdf/sample_table.pdf", "rb") as f:
        data = f.read()
        file_input = ParseFileInput(
            file_input=FileInput(file_name="test.pdf", file_size=len(data), data=data),
            parse_config=ParseFileConfig(),
        )
        file = MPInput(input=file_input)

        raw_response = await nc.request(
            NATS_SUBJECT, file.model_dump_json().encode("utf-8"), timeout=300
        )
        response = MPOutput.model_validate_json(raw_response.data.decode("utf-8"))
        assert response.output_type == MPOutputType.PARSE_OK

    await nc.close()
