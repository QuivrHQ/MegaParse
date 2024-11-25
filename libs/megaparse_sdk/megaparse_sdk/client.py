import asyncio
import enum
import logging
import os
from io import BytesIO
from pathlib import Path
from types import TracebackType
from typing import Any, Self

import httpx
import nats
from nats.errors import NoRespondersError, TimeoutError

from megaparse_sdk.config import ClientNATSConfig, MegaParseConfig
from megaparse_sdk.schema.mp_exceptions import (
    DownloadError,
    InternalServiceError,
    MemoryLimitExceeded,
    ModelNotSupported,
    ParsingException,
)
from megaparse_sdk.schema.mp_inputs import (
    FileInput,
    MPInput,
    ParseFileConfig,
    ParseFileInput,
    ParseUrlInput,
)
from megaparse_sdk.schema.mp_outputs import (
    MPErrorType,
    MPOutput,
    MPOutputType,
)
from megaparse_sdk.utils.load_ssl import load_ssl_cxt

logger = logging.getLogger("megparse_sdk")


class MegaParseClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        config = MegaParseConfig()
        self.base_url = base_url or config.url
        self.api_key = api_key or config.api_key
        self.max_retries = config.max_retries
        if self.api_key:
            self.session = httpx.AsyncClient(
                headers={"x-api-key": self.api_key}, timeout=config.timeout
            )
        else:
            self.session = httpx.AsyncClient(timeout=config.timeout)

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        client = self.session
        for attempt in range(self.max_retries):
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError):
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        raise RuntimeError(f"Can't send request to the server: {url}")

    async def close(self):
        await self.session.aclose()


class ClientState(enum.Enum):
    # First state of the client
    UNOPENED = 1
    #   Client has either sent a request, or is within a `with` block.
    OPENED = 2
    #   Client has either exited the `with` block, or `close()` called.
    CLOSED = 3


class MegaParseNATSClient:
    def __init__(self, config: ClientNATSConfig):
        self.nc_config = config
        self.max_retries = self.nc_config.max_retries
        self.backoff = self.nc_config.backoff
        if self.nc_config.ssl_config:
            self.ssl_ctx = load_ssl_cxt(self.nc_config.ssl_config)
        else:
            self.ssl_ctx = None
        # Client connection
        self._state = ClientState.UNOPENED
        self._nc = None

    async def _get_nc(self):
        if self._nc is None:
            self._nc = await nats.connect(
                self.nc_config.endpoint,
                tls=self.ssl_ctx,
                connect_timeout=self.nc_config.connect_timeout,
                reconnect_time_wait=self.nc_config.reconnect_time_wait,
                max_reconnect_attempts=self.nc_config.max_reconnect_attempts,
            )
            return self._nc
        return self._nc

    async def __aenter__(self: Self) -> Self:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, client was closed."
                ),
            }[self._state]
            raise RuntimeError(msg)

        self._state = ClientState.OPENED

        await self._get_nc()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ) -> None:
        self._state = ClientState.CLOSED
        await self.aclose()

    async def parse_url(self, url: str):
        url_inp = ParseUrlInput(url=url)
        return await self._send_req(MPInput(input=url_inp))

    async def parse_file(
        self, file: Path | BytesIO, file_name: str | None = None
    ) -> str:
        if isinstance(file, Path):
            with open(file, "rb") as f:
                data = f.read()
            file_name = os.path.basename(file)
        else:
            file.seek(0)
            data = file.read()
            if file_name is None:
                raise ValueError("please provide file_name if passing ByteIO stream")

        file_input = ParseFileInput(
            file_input=FileInput(file_name=file_name, file_size=len(data), data=data),
            parse_config=ParseFileConfig(),
        )

        inp = MPInput(input=file_input)
        return await self._send_req(inp)

    async def _send_req(self, inp: MPInput) -> str:
        logger.debug(f"Sending {inp} to megaparse service.")

        for attempt in range(self.max_retries):
            try:
                return await self._send_req_inner(inp)
            except (TimeoutError, NoRespondersError) as e:
                logger.error(f"Sending req error: {e}. Retrying for {attempt} time")
                if attempt < self.max_retries - 1:
                    logger.debug(f"Backoff for {2**self.backoff}s")
                    await asyncio.sleep(2**self.backoff)
        raise ParsingException

    async def _send_req_inner(self, inp: MPInput):
        nc = await self._get_nc()
        raw_response = await nc.request(
            self.nc_config.subject,
            inp.model_dump_json().encode("utf-8"),
            timeout=self.nc_config.timeout,
        )
        response = MPOutput.model_validate_json(raw_response.data.decode("utf-8"))
        return self._handle_mp_output(response)

    def _handle_mp_output(self, response: MPOutput) -> str:
        if response.output_type == MPOutputType.PARSE_OK:
            assert response.result, "Parsing OK but response is None"
            return response.result
        elif response.output_type == MPOutputType.PARSE_ERR:
            assert response.err, "Parsing OK but response is None"
            match response.err.mp_err_code:
                case MPErrorType.MEMORY_LIMIT:
                    raise MemoryLimitExceeded
                case MPErrorType.INTERNAL_SERVER_ERROR:
                    raise InternalServiceError
                case MPErrorType.MODEL_NOT_SUPPORTED:
                    raise ModelNotSupported
                case MPErrorType.DOWNLOAD_ERROR:
                    raise DownloadError
                case MPErrorType.PARSING_ERROR:
                    raise ParsingException
        raise ValueError(f"unknown service response type: {response}")

    async def aclose(self):
        nc = await self._get_nc()
        await nc.close()
