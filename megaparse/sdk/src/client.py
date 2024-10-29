from typing import Any
import httpx


class MegaParseClient:
    def __init__(self, api_key: str):
        self.base_url = "https://api.example.com"  # to define once in production
        self.api_key = api_key
        self.session = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )

    async def request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with self.session as client:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def close(self):
        await self.session.aclose()
