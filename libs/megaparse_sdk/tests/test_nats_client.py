import asyncio
import logging
from pathlib import Path

import nats
import pytest
import pytest_asyncio
from megaparse_sdk.client import ClientState, MegaParseNATSClient
from megaparse_sdk.config import ClientNATSConfig, SSLConfig
from megaparse_sdk.schema.mp_exceptions import (
    DownloadError,
    InternalServiceError,
    MemoryLimitExceeded,
    ModelNotSupported,
    ParsingException,
)
from megaparse_sdk.schema.mp_inputs import MPInput, ParseFileInput, ParseUrlInput
from megaparse_sdk.schema.mp_outputs import (
    MPErrorType,
    MPOutput,
    MPOutputType,
    ParseError,
)
from nats.aio.client import Client

logger = logging.getLogger(__name__)

NATS_URL = "nats://test@127.0.0.1:4222"
NATS_SUBJECT = "parsing"
SSL_CERT_FILE = "./tests/certs/client-cert.pem"
SSL_KEY_FILE = "./tests/certs/client-key.pem"
CA_CERT_FILE = "./tests/certs/rootCA.pem"


@pytest.fixture(scope="session")
def ssl_config() -> SSLConfig:
    return SSLConfig(
        ca_cert_file=CA_CERT_FILE,
        ssl_key_file=SSL_KEY_FILE,
        ssl_cert_file=SSL_CERT_FILE,
    )


@pytest.fixture(scope="session")
def nc_config(ssl_config: SSLConfig) -> ClientNATSConfig:
    config = ClientNATSConfig(
        subject=NATS_SUBJECT,
        endpoint=NATS_URL,
        ssl_config=ssl_config,
        timeout=0.5,
        max_retries=1,
        backoff=-1,
        connect_timeout=1,
        reconnect_time_wait=1,
        max_reconnect_attempts=1,
    )
    return config


@pytest_asyncio.fixture(scope="function")
async def nats_service(nc_config: ClientNATSConfig):
    # TODO: fix TLS handshake to work in CI
    # ssl_config = load_ssl_cxt(nc_config.ssl_config)
    nc = await nats.connect(
        nc_config.endpoint,
        tls=ssl_config,
        connect_timeout=nc_config.connect_timeout,
        reconnect_time_wait=nc_config.reconnect_time_wait,
        max_reconnect_attempts=nc_config.max_reconnect_attempts,
    )
    yield nc
    await nc.drain()


@pytest.mark.asyncio
async def test_client_state_transition(nc_config: ClientNATSConfig):
    mpc = MegaParseNATSClient(nc_config)
    assert mpc._state == ClientState.UNOPENED
    async with mpc:
        assert mpc._state == ClientState.OPENED
    assert mpc._state == ClientState.CLOSED

    with pytest.raises(RuntimeError):
        async with mpc:
            pass


@pytest.mark.asyncio(loop_scope="session")
async def test_client_parse_file(nats_service: Client, nc_config: ClientNATSConfig):
    async def message_handler(msg):
        parsed_input = MPInput.model_validate_json(msg.data.decode("utf-8")).input
        assert isinstance(parsed_input, ParseFileInput)
        output = MPOutput(output_type=MPOutputType.PARSE_OK, result="test")
        await nats_service.publish(msg.reply, output.model_dump_json().encode("utf-8"))

    await nats_service.subscribe(NATS_SUBJECT, "worker", cb=message_handler)

    file_path = Path("./tests/pdf/sample_table.pdf")
    async with MegaParseNATSClient(nc_config) as mp_client:
        resp = await mp_client.parse_file(file=file_path)
        assert resp == "test"


@pytest.mark.asyncio(loop_scope="session")
async def test_client_parse_url(nats_service: Client, nc_config: ClientNATSConfig):
    async def message_handler(msg):
        parsed_input = MPInput.model_validate_json(msg.data.decode("utf-8")).input
        assert isinstance(parsed_input, ParseUrlInput)
        output = MPOutput(output_type=MPOutputType.PARSE_OK, result="url")
        await nats_service.publish(msg.reply, output.model_dump_json().encode("utf-8"))

    await nats_service.subscribe(NATS_SUBJECT, "worker", cb=message_handler)

    async with MegaParseNATSClient(nc_config) as mp_client:
        resp = await mp_client.parse_url(url="this://this")
        assert resp == "url"


@pytest.mark.asyncio(loop_scope="session")
async def test_client_parse_timeout(nats_service: Client, ssl_config: SSLConfig):
    nc_config = ClientNATSConfig(
        subject=NATS_SUBJECT,
        endpoint=NATS_URL,
        ssl_config=ssl_config,
        timeout=0.1,
        max_retries=1,
        backoff=1,
    )

    async def service(msg):
        await asyncio.sleep(2 * nc_config.timeout)

    await nats_service.subscribe(NATS_SUBJECT, "worker", cb=service)

    file_path = Path("./tests/pdf/sample_table.pdf")
    with pytest.raises(ParsingException):
        async with MegaParseNATSClient(nc_config) as mp_client:
            await mp_client.parse_file(file=file_path)


@pytest.mark.asyncio(loop_scope="session")
async def test_client_parse_timeout_retry(nats_service: Client, ssl_config: SSLConfig):
    nc_config = ClientNATSConfig(
        subject=NATS_SUBJECT,
        endpoint=NATS_URL,
        ssl_config=ssl_config,
        timeout=0.1,
        max_retries=2,
        backoff=-5,
    )

    msgs = []

    async def service(msg):
        msgs.append(msg)
        await asyncio.sleep(2 * nc_config.timeout)

    await nats_service.subscribe(NATS_SUBJECT, "worker", cb=service)

    file_path = Path("./tests/pdf/sample_table.pdf")
    with pytest.raises(ParsingException):
        async with MegaParseNATSClient(nc_config) as mp_client:
            await mp_client.parse_file(file=file_path)
    assert len(msgs) == 2


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize(
    "mp_error_type, exception_class",
    [
        ("MEMORY_LIMIT", MemoryLimitExceeded),
        ("INTERNAL_SERVER_ERROR", InternalServiceError),
        ("MODEL_NOT_SUPPORTED", ModelNotSupported),
        ("DOWNLOAD_ERROR", DownloadError),
        ("PARSING_ERROR", ParsingException),
    ],
)
async def test_client_parse_file_excp(
    nats_service: Client, nc_config: ClientNATSConfig, mp_error_type, exception_class
):
    async def message_handler(msg):
        parsed_input = MPInput.model_validate_json(msg.data.decode("utf-8")).input
        assert isinstance(parsed_input, ParseFileInput)
        err = ParseError(mp_err_code=MPErrorType[mp_error_type], message="")
        output = MPOutput(
            output_type=MPOutputType.PARSE_ERR,
            err=err,
            result=None,
        )
        await nats_service.publish(msg.reply, output.model_dump_json().encode("utf-8"))

    await nats_service.subscribe(NATS_SUBJECT, "worker", cb=message_handler)

    file_path = Path("./tests/pdf/sample_table.pdf")
    with pytest.raises(exception_class):
        async with MegaParseNATSClient(nc_config) as mp_client:
            await mp_client.parse_file(file=file_path)
