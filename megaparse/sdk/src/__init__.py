from .client import MegaParseClient
from .endpoints.file_upload import FileUpload
from .endpoints.url_upload import URLUpload


class MegaParseSDK:
    def __init__(self, api_key: str):
        self.client = MegaParseClient(api_key)
        self.file = FileUpload(self.client)
        self.url = URLUpload(self.client)

    async def close(self):
        await self.client.close()
