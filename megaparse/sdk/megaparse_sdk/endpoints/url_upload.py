import asyncio

import httpx
from httpx import Response

from megaparse.sdk.megaparse_sdk.client import MegaParseClient


class URLUpload:
    def __init__(self, client: MegaParseClient):
        self.client = client

    async def upload(self, url: str, max_retries: int = 3) -> Response:
        endpoint = f"/v1/url?url={url}"
        headers = {"accept": "application/json"}
        response = await self.client.request("POST", endpoint, headers=headers, data="")
        return response
