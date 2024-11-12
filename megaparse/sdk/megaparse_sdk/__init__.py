from .client import MegaParseClient
from .endpoints.file_upload import FileUpload
from .endpoints.url_upload import URLUpload


class MegaParseSDK:
    def __init__(self, api_key: str, base_url: str | None = None, timeout: int = 600):
        self.client = MegaParseClient(api_key, base_url, timeout)
        self.file = FileUpload(self.client)
        self.url = URLUpload(self.client)

    async def close(self):
        await self.client.close()
