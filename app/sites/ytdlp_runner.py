import os
from typing import Optional
from yt_dlp import YoutubeDL

def _base_without_ext(path: str) -> str:
    base, _ext = os.path.splitext(path)
    return base

def download_with_ytdlp(
    media_url: str,
    dest_path: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """
    Uses yt-dlp to lawfully download media_url to dest_path (mp4).
    Returns the final file path on disk.

    This function is intended for sources/domains you have authorization to download from.
    Do not use on DRM-protected or ToS-restricted services.
    """
    base = _base_without_ext(dest_path)
    final_path = base + ".mp4"
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
        "outtmpl": base + ".%(ext)s",
        "merge_output_format": "mp4",
        "prefer_ffmpeg": True,
        "postprocessors": [
            {"key": "FFmpegVideoConvertor", "preferedformat": "mp4"},
        ],
        # Best video+audio, fallback to best single
        "format": "bv*+ba/b",
        # Avoid unplayable formats
        "allow_unplayable_formats": False,
    }
    if username:
        ydl_opts["username"] = username
    if password:
        ydl_opts["password"] = password

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(media_url, download=True)
        # Try to resolve the post-processed path
        # Newer yt-dlp sets requested_downloads[i]['filepath']
        try:
            reqs = info.get("requested_downloads") or []
            for r in reqs:
                fp = r.get("filepath")
                if fp and os.path.exists(fp):
                    # If not mp4, prefer final_path produced by postprocessor
                    pass
        except Exception:
            pass

    # Prefer the known final mp4 path
    if os.path.exists(final_path):
        return final_path

    # Fallback: scan for any file starting with base.*
    directory = os.path.dirname(base) or "."
    for fname in os.listdir(directory):
        fpath = os.path.join(directory, fname)
        if os.path.isfile(fpath) and fname.startswith(os.path.basename(base) + "."):
            return fpath

    # Last resort: return dest_path even if not found; caller may handle error
    return final_path
