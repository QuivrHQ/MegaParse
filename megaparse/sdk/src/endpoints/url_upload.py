from .client import MegaParseClient
import asyncio


class URLUpload:
    def __init__(self, client: MegaParseClient):
        self.client = client

    async def aupload(self, url: str):
        data = {"url": url}
        return self.client.request("POST", "/url", json=data)

    def upload(self, url: str):
        return asyncio.run(self.aupload(url))
