import asyncio
import io
import os
from typing import Optional

import httpx
import nats
import psutil
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders.url_playwright import (
    UnstructuredHtmlEvaluator,
)
from langchain_openai import ChatOpenAI
from loguru import logger
from megaparse import MegaParse
from megaparse.parser.builder import ParserBuilder
from megaparse.parser.unstructured_parser import UnstructuredParser
from megaparse_schema.extensions import FileExtension
from megaparse_schema.mp_exceptions import ModelNotSupported, ParsingException
from megaparse_schema.mp_inputs import (
    FileInput,
    MPInput,
    ParseFileConfig,
    ParseFileInput,
    ParseUrlInput,
)
from megaparse_schema.mp_outputs import MPErrorType, MPOutput, MPOutputType, ParseError
from megaparse_schema.parser_config import StrategyEnum
from nats.aio.client import Client
from nats.aio.msg import Msg
from playwright.async_api import Browser, async_playwright

from api.utils.load_ssl import load_ssl_cxt


def _check_free_memory() -> bool:
    """Reject traffic when free memory is below minimum (default 2GB)."""
    mem = psutil.virtual_memory()
    memory_free_minimum = int(os.environ.get("MEMORY_FREE_MINIMUM_MB", 2048))

    if mem.available <= memory_free_minimum * 1024 * 1024:
        return False
    return True


class MegaParseService:
    def __init__(
        self, browser: Browser, html_remove_selectors: Optional[list[str]] = None
    ) -> None:
        self.parser_builder = ParserBuilder()
        self.browser = browser
        self.httpx_client = None
        self.html_evaluator = UnstructuredHtmlEvaluator(html_remove_selectors)

    def _init_model(self, model_name: str) -> ChatOpenAI | ChatAnthropic:
        if model_name.startswith("gpt"):
            model = ChatOpenAI(model=model_name, api_key=os.getenv("OPENAI_API_KEY"))  # type: ignore
        elif model_name.startswith("claude"):
            model = ChatAnthropic(
                model_name=model_name,
                api_key=os.getenv("ANTHROPIC_API_KEY"),  # type: ignore
                timeout=60,
                stop=None,
            )
        else:
            raise ModelNotSupported
        return model

    async def parse_file(
        self, file: FileInput, parser_config: ParseFileConfig
    ) -> MPOutput:
        logger.info(f"Parsing file {file.file_name} using config {parser_config}")
        if not _check_free_memory():
            return MPOutput(
                output_type=MPOutputType.PARSE_ERR,
                err=ParseError(
                    mp_err_code=MPErrorType.MEMORY_LIMIT,
                    message="high memory pressure on server",
                ),
                result=None,
            )
        try:
            if parser_config.llm_model_name and parser_config.check_table:
                model = self._init_model(parser_config.llm_model_name)

            parser = self.parser_builder.build(parser_config)
            megaparse = MegaParse(parser=parser)
            _, extension = os.path.splitext(file.file_name)
            file_stream = io.BytesIO(file.data)
            result = await megaparse.aload(file=file_stream, file_extension=extension)
            return MPOutput(output_type=MPOutputType.PARSE_OK, result=result)
        except ParsingException as e:
            return MPOutput(
                output_type=MPOutputType.PARSE_ERR,
                err=ParseError(
                    mp_err_code=MPErrorType.PARSING_ERROR,
                    message=str(e),
                ),
                result=None,
            )

        except Exception as e:
            return MPOutput(
                output_type=MPOutputType.PARSE_ERR,
                err=ParseError(
                    mp_err_code=MPErrorType.INTERNAL_SERVER_ERROR,
                    message=str(e),
                ),
                result=None,
            )

    async def parse_url(
        self,
        url: str,
    ):
        assert self.browser
        if url.endswith(".pdf"):
            # TODO: don't have multiple clients'
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
            if response.status_code != 200:
                raise Exception("Failed to download the file")

            try:
                megaparse = MegaParse(
                    parser=UnstructuredParser(strategy=StrategyEnum.AUTO)
                )
                file_stream = io.BytesIO(response.content)
                result = await megaparse.aload(
                    file=file_stream, file_extension=FileExtension.PDF
                )
                return {"message": "File parsed successfully", "result": result}
            except Exception as e:
                raise Exception(str(e))
        else:
            page = await self.browser.new_page()
            response = await page.goto(url)
            if response is None:
                # TODO
                return
            text = await self.html_evaluator.evaluate_async(
                page, self.browser, response
            )
            # doc = Document(page_content=text, metadata={"source": url})


async def handle_msg(nc: Client, mp_service: MegaParseService, msg: Msg):
    parsed_input = MPInput.model_validate_json(msg.data.decode("utf-8")).input
    if isinstance(parsed_input, ParseFileInput):
        parse_result = await mp_service.parse_file(
            parsed_input.file_input, parsed_input.parse_config
        )
    elif isinstance(parsed_input, ParseUrlInput):
        pass
    else:
        raise ValueError(f"Unknown parse_type in msg {msg.sid}")

    await nc.publish(msg.reply, parse_result.model_dump_json().encode("utf-8"))


async def main():
    TOKEN = "test"
    NATS_URL = f"nats://{TOKEN}@localhost:4222"  # GET FROM ENV
    NATS_SUBJECT = "parse.*"
    QUEUE_NAME = "MEGAPARSE-QUEUE-1"
    SSL_CERT_FILE = "./libs/megaparse/tests/certs/client-cert.pem"
    SSL_KEY_FILE = "./libs/megaparse/tests/certs/client-key.pem"
    CA_CERT_FILE = "/Users/amine/Library/Application Support/mkcert/rootCA.pem"
    context = load_ssl_cxt(
        cert_file=SSL_CERT_FILE, ca_cert_file=CA_CERT_FILE, key_file=SSL_KEY_FILE
    )
    nc = await nats.connect(NATS_URL, tls=context)
    sub = await nc.subscribe(NATS_SUBJECT, QUEUE_NAME)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, proxy=None)
        service = MegaParseService(browser)
        logger.info(f"Started megaparse_service listening on '{NATS_SUBJECT}'")
        async for msg in sub.messages:
            try:
                await handle_msg(nc, service, msg)
            except Exception as e:
                logger.error(
                    f"Error handling msg : {msg.sid} from megaparse_service: {e}"
                )


if __name__ == "__main__":
    # TODO: graceful shutdowns
    asyncio.run(main())
