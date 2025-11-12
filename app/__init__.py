from .config import settings
from .logging_conf import configure_logging

configure_logging()
__all__ = ["settings"]