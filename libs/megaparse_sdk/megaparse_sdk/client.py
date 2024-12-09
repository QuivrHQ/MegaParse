import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import Any

import httpx
import nats
from nats.errors import TimeoutError

from megaparse_sdk.config import ClientNATSConfig, MegaParseConfig
from megaparse_sdk.schema.mp_exceptions import (
    DownloadError,
    InternalServiceError,
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


class MegaParseNATSClient:
    def __init__(self, config: ClientNATSConfig = ClientNATSConfig()):
        self.nc_config = config
        self.max_retries = self.nc_config.max_retries
        self.backoff = self.nc_config.backoff
        if self.nc_config.ssl_config:
            self.ssl_ctx = load_ssl_cxt(self.nc_config.ssl_config)

    async def _get_nc(self):
        if self._nc is None:
            self._nc = await nats.connect(
                self.nc_config.nats_endpoint, tls=self.ssl_ctx
            )
            return self._nc
        return self._nc

    async def parse_url(self, url: str):
        url_inp = ParseUrlInput(url=url)
        await self._send_req(MPInput(input=url_inp))

    async def parse_file(self, file: Path | BytesIO) -> str:
        if isinstance(file, Path):
            with open(file, "rb") as f:
                data = f.read()
        else:
            file.seek(0)
            data = file.read()
        file_input = ParseFileInput(
            file_input=FileInput(file_name="test.pdf", file_size=len(data), data=data),
            parse_config=ParseFileConfig(),
        )

        inp = MPInput(input=file_input)
        return await self._send_req(inp)

    async def _send_req(self, inp: MPInput) -> str:
        logger.debug(f"Sending {inp} to megaparse service.")

        for attempt in range(self.max_retries):
            try:
                return await self._send_req_inner(inp)
            except TimeoutError:
                logger.error(f"Timeout error parsing. Retrying {attempt} time")
                if attempt < self.max_retries - 1:
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
        if response.output_type == MPOutputType.PARSE_OK:
            assert response.result, "Parsing OK but response is None"
            return response.result
        elif response.output_type == MPOutputType.PARSE_ERR:
            assert response.err, "Parsing OK but response is None"

            match response.err.mp_err_code:
                case MPErrorType.MEMORY_LIMIT:
                    raise ModelNotSupported
                case MPErrorType.INTERNAL_SERVER_ERROR:
                    raise InternalServiceError
                case MPErrorType.MODEL_NOT_SUPPORTED:
                    raise ModelNotSupported
                case MPErrorType.DOWNLOAD_ERROR:
                    raise DownloadError
                case MPErrorType.PARSING_ERROR:
                    raise ParsingException
        else:
            raise ValueError(f"unknown service response type: {response}")

    async def close(self):
        nc = await self._get_nc()
        await nc.close()
