from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_ID: int
    API_HASH: str
    ADMIN_USER_IDS: List[int] = []
    DUMP_CHANNEL_ID: int  # Channel for storing raw / processed files
    PUBLISH_CHANNEL_ID: int  # Channel where posts are published
    DATABASE_URL: str = "sqlite:///./data/db.sqlite3"
    REDIS_URL: Optional[str] = None
    MAX_INLINE_BUTTONS: int = 5
    REQUEST_TIMEOUT: int = 30
    SHORTENER_PRIMARY: str = "tinyurl"
    SHORTENER_FALLBACKS: List[str] = ["isgd"]
    STORAGE_BACKENDS: List[str] = ["telegram"]
    EXTERNAL_LARGE_FILE_THRESHOLD_BYTES: int = 4 * 1024 * 1024 * 1024  # 4GB
    WATERMARK_ENABLED: bool = False
    WATERMARK_IMAGE_PATH: Optional[str] = None
    WATERMARK_TEXT: Optional[str] = None
    NAME_PREFIX: str = ""
    NAME_SUFFIX: str = ""
    META_TAGS: List[str] = []
    ENABLE_AUTO_SCHEDULER: bool = True
    AUTO_POLL_INTERVAL_MIN: int = 30
    VALID_VIDEO_RESOLUTIONS: List[str] = ["480p", "720p", "1080p", "original"]
    TARGET_RES_MAP: dict = {
        "480p": {"width": 854, "height": 480},
        "720p": {"width": 1280, "height": 720},
        "1080p": {"width": 1920, "height": 1080},
    }
    AUDIO_LANGUAGES_ALLOWED: List[str] = ["en"]
    SUBTITLE_LANGUAGES_ALLOWED: List[str] = ["en"]
    FFMPEG_LOGLEVEL: str = "error"
    ENCRYPTION_KEY: str  # Fernet key (base64 urlsafe)

    # New: yt-dlp global toggle (disabled by default)
    YTDLP_ENABLED: bool = False

    class Config:
        env_file = ".env"

settings = Settings()