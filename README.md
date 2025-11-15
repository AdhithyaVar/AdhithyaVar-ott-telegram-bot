# Media Processing Telegram Bot (Legitimate Use Only)

## Legal Notice
Use this project only for media you have rights to process and download. Do **not** add code that bypasses DRM, violates Terms of Service, or accesses protected content unlawfully. The included adapter system is for providers that offer official, lawful APIs/SDKs for authorized downloads.

## Features
- Multi-quality transcoding (480p/720p/1080p/original)
- Selective audio & subtitle language inclusion (skip if missing)
- Watermark (image/text) + metadata embedding (original only)
- Inline button post creation with shortened links
- Storage abstraction (Telegram dump channel; extensible for external backends)
- Episodic queue to avoid duplicate uploads
- Encrypted credentials for providers and per-site/domain
- Lawful OTT adapter plugin system (official APIs only)
- URL shortening with fallback chain
- Dockerized deployment (Heroku/Railway/Render/VPS compatible)

## Architecture
1. Bot (Pyrogram) handles commands & posting.
2. Media processing (FFmpeg wrapper) for variants & watermark.
3. Storage backends for file persistence.
4. Shortener interface with fallback.
5. Database (SQLAlchemy) for episodes, jobs, accounts, site credentials.
6. Security (Fernet) for credential encryption.
7. Site adapters for lawful API-based resolution of download URLs.

## Lawful Adapter System
Create adapters in `app/sites/` implementing `SiteAdapter` and register them in `registry.py`. Each adapter obtains an authorized direct URL using official APIs (e.g., OAuth + signed URL). No scraping or DRM circumvention.

## Commands
General:
- `/upload <title> <url>` queue a single media job.
- `/episode_add <series_id> <ep_number> <url>` add episode.
- `/process_pending` process all unprocessed episodes.
- `/status` show counts.
- `/settings_show` display current config.

Accounts (admin):
- `/account_add <provider> <user_id> <password>`
- `/account_list`
- `/account_delete <provider> <user_id>`

Site Credentials (admin):
- `/site_cred_add <site_url> <user_id> <password>`
- `/site_cred_list`
- `/site_cred_delete <site_url> <user_id>`

## Environment (.env example)
```
BOT_TOKEN=your_bot_token
API_ID=12345
API_HASH=your_api_hash
DUMP_CHANNEL_ID=-100123456789
PUBLISH_CHANNEL_ID=-100987654321
ADMIN_USER_IDS=[123456789]
ENCRYPTION_KEY=your_fernet_key_here
```
Generate a Fernet key:
```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Deployment
```
docker build -t ott-bot .
docker run --env-file .env ott-bot
```
Heroku (example):
- Add buildpack for Python
- Set config vars from `.env`
- Use `Procfile`

## Extending
- Add new storage backends in `app/storage/base.py`.
- Add adapters in `app/sites/` with official API flows.
- Implement job queue (Celery/RQ) for scalability.
- Add dynamic settings update commands (persist to DB).

## Disclaimer
No DRM circumvention logic is included; do not add any.
