import abc
from dataclasses import dataclass
from typing import Dict, Optional, List

@dataclass
class DownloadTask:
    direct_url: str
    headers: Dict[str, str]
    cookies: Dict[str, str]

class SiteAdapter(abc.ABC):
    name: str
    domains: List[str]

    @abc.abstractmethod
    async def prepare_download(self, media_url: str, user_id: Optional[str], password: Optional[str]) -> DownloadTask:
        ...
