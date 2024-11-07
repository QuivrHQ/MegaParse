from typing import Any

import httpx


class MegaParseClient:
    def __init__(self, api_key: str | None = None):
        self.base_url = "http://localhost:8000"  # "https://megaparse.tooling.quivr.app"  # to define once in production  # to define once in production

        self.api_key = api_key
        if self.api_key:
            self.session = httpx.AsyncClient(
                headers={"x-api-key": self.api_key}, timeout=60
            )
        else:
            self.session = httpx.AsyncClient(timeout=60)

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        client = self.session
        response = await client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.session.aclose()
