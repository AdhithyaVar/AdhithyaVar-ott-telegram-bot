import httpx
from typing import Optional, Dict
from .base import SiteAdapter, DownloadTask

class ExamplePublicAPIAdapter(SiteAdapter):
    name = "example_public_api"
    domains = ["media.example.org"]

    async def _login_and_get_token(self, user_id: str, password: str) -> str:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://media.example.org/oauth/token",
                data={
                    "grant_type": "password",
                    "username": user_id,
                    "password": password,
                    "client_id": "your-client-id",
                    "client_secret": "your-client-secret"
                }
            )
            r.raise_for_status()
            return r.json()["access_token"]

    async def _resolve_media(self, token: str, media_url: str) -> str:
        async with httpx.AsyncClient(timeout=30, headers={"Authorization": f"Bearer {token}"}) as client:
            r = await client.get("https://media.example.org/api/v1/resolve", params={"url": media_url})
            r.raise_for_status()
            return r.json()["download_url"]

    async def prepare_download(self, media_url: str, user_id: Optional[str], password: Optional[str]) -> DownloadTask:
        token = None
        if user_id and password:
            token = await self._login_and_get_token(user_id, password)
        download_url = await self._resolve_media(token, media_url)
        headers: Dict[str, str] = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return DownloadTask(direct_url=download_url, headers=headers, cookies={})