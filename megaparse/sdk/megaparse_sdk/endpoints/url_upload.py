from megaparse.sdk.megaparse_sdk.client import MegaParseClient


class URLUpload:
    def __init__(self, client: MegaParseClient):
        self.client = client

    async def upload(self, url: str):
        endpoint = f"/v1/url?url={url}"
        headers = {"accept": "application/json"}
        return await self.client.request("POST", endpoint, headers=headers, data="")
