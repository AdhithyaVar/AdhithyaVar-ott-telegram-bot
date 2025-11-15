from .config import settings
import re

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9._\\- ]+', '_', name).strip()

def build_filename(base_title: str, quality: str, meta_tags=None):
    meta_part = ""
    if meta_tags:
        meta_part = "." + ".".join([sanitize_filename(t) for t in meta_tags])
    full = f"{settings.NAME_PREFIX}{sanitize_filename(base_title)}{meta_part}.{quality}{settings.NAME_SUFFIX}.mp4"
    return sanitize_filename(full)
