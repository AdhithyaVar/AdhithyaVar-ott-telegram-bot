from urllib.parse import urlparse
from typing import Optional
from ..db import get_session, SiteCredential
from ..security.crypto import decrypt_str

def normalize_domain(site_url: str) -> str:
    if "://" not in site_url:
        site_url = "https://" + site_url
    parsed = urlparse(site_url)
    return parsed.netloc.lower()

def fetch_site_credential_for_url(media_url: str) -> Optional[SiteCredential]:
    domain = normalize_domain(media_url)
    session = get_session()
    cred = session.query(SiteCredential).filter_by(domain=domain).first()
    session.close()
    return cred

def get_plain_password(site_cred: SiteCredential) -> str:
    return decrypt_str(site_cred.password_enc)
