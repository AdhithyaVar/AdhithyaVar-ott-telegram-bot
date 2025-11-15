from typing import Dict, Optional, List
from .base import SiteAdapter
from .example_public_api import ExamplePublicAPIAdapter

_registry: Dict[str, SiteAdapter] = {}

def register_adapter(adapter: SiteAdapter):
    for d in adapter.domains:
        _registry[d.lower()] = adapter

def init_registry():
    register_adapter(ExamplePublicAPIAdapter())

def find_adapter_for_domain(domain: str) -> Optional[SiteAdapter]:
    return _registry.get(domain.lower())

def list_registered_adapters() -> List[str]:
    return [f"{dom} -> {_registry[dom].name}" for dom in sorted(_registry.keys())]