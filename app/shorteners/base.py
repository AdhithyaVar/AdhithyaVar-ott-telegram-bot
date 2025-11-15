import abc
import httpx

class Shortener(abc.ABC):
    name: str
    @abc.abstractmethod
    async def shorten(self, url: str) -> str:
        ...

class TinyUrlShortener(Shortener):
    name = "tinyurl"
    async def shorten(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get("https://tinyurl.com/api-create.php", params={"url": url})
            r.raise_for_status()
            return r.text.strip()

class IsGdShortener(Shortener):
    name = "isgd"
    async def shorten(self, url: str) -> str:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get("https://is.gd/create.php", params={"format":"simple","url": url})
            r.raise_for_status()
            return r.text.strip()

SHORTENER_MAP = {
    "tinyurl": TinyUrlShortener(),
    "isgd": IsGdShortener()
}

async def shorten_url(url: str, preferred: str, fallbacks: list):
    ordered = [preferred] + [x for x in fallbacks if x != preferred]
    for name in ordered:
        shortener = SHORTENER_MAP.get(name)
        if not shortener: continue
        try:
            return await shortener.shorten(url)
        except Exception:
            continue
    return url
