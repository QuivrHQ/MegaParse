from megaparse.sdk.src.client import MegaParseClient


class URLUpload:
    def __init__(self, client: MegaParseClient):
        self.client = client

    async def upload(self, url: str):
        data = {"url": url}
        return await self.client.request("POST", "/url", json=data)
