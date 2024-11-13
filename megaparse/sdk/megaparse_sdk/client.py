from typing import Any

import httpx

from .config import MegaparseConfig


class MegaParseClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
    ):
        config = MegaparseConfig()
        self.base_url = base_url or config.url
        self.api_key = api_key or config.api_key
        if self.api_key:
            self.session = httpx.AsyncClient(
                headers={"x-api-key": self.api_key}, timeout=config.timeout
            )
        else:
            self.session = httpx.AsyncClient(timeout=config.timeout)

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        client = self.session
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.session.aclose()
