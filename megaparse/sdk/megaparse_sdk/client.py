from typing import Any

import httpx


class MegaParseClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 600,
    ):
        self.base_url = base_url
        self.api_key = api_key
        if self.api_key:
            self.session = httpx.AsyncClient(
                headers={"x-api-key": self.api_key}, timeout=timeout
            )
        else:
            self.session = httpx.AsyncClient(timeout=timeout)

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        client = self.session
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.session.aclose()
