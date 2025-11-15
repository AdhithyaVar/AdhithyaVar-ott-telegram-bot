import asyncio, logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .config import settings
from .db import init_db, get_session, Episode, Job, Account, SiteCredential
from .storage.base import build_backends
from .shorteners.base import shorten_url
from .media.ffmpeg_wrapper import apply_watermark_and_metadata, build_all_variants
from .naming import build_filename
from .security.crypto import encrypt_str
from .accounts.site_credentials import normalize_domain, fetch_site_credential_for_url, get_plain_password
from .sites.registry import init_registry, find_adapter_for_domain

logger = logging.getLogger("bot")

app = Client(
    "media-bot",
    api_id=settings.API_ID,
    api_hash=settings.API_HASH,
    bot_token=settings.BOT_TOKEN
)

storage_backends = {}

def _is_admin(user_id: int) -> bool:
    return user_id in set(settings.ADMIN_USER_IDS or [])

def _mask_user_id(uid: str) -> str:
    if not uid:
        return "N/A"
    if "@" in uid:
        local, domain = uid.split("@", 1)
        mask_local = (local[:1] + "***" + (local[-1:] if len(local) > 1 else ""))
        return f"{mask_local}@{domain}"
    if len(uid) <= 2:
        return "***"
    return uid[:1] + "***" + uid[-1:]

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text("Welcome. Send /help for commands.")

@app.on_message(filters.command("help"))
async def help_handler(client, message):
    await message.reply_text(
        "/upload <title> <url>\n"
        "/episode_add <series_id> <ep_number> <url>\n"
        "/process_pending\n"
        "/status\n"
        "/settings_show\n\n"
        "Accounts (admin):\n"
        "/account_add <provider> <user_id> <password>\n"
        "/account_list\n"
        "/account_delete <provider> <user_id>\n\n"
        "Site credentials (admin):\n"
        "/site_cred_add <site_url> <user_id> <password>\n"
        "/site_cred_list\n"
        "/site_cred_delete <site_url> <user_id>\n"
    )

@app.on_message(filters.command("settings_show"))
async def settings_show(client, message):
    text = (
        f"Prefix: {settings.NAME_PREFIX}\n"
        f"Suffix: {settings.NAME_SUFFIX}\n"
        f"Meta Tags: {settings.META_TAGS}\n"
        f"Audio Allowed: {settings.AUDIO_LANGUAGES_ALLOWED}\n"
        f"Subs Allowed: {settings.SUBTITLE_LANGUAGES_ALLOWED}\n"
        f"WM Enabled: {settings.WATERMARK_ENABLED}"
    )
    await message.reply_text(text)

@app.on_message(filters.command("upload"))
async def upload_handler(client, message):
    if len(message.command) < 3:
        return await message.reply_text("Usage: /upload <title> <direct_media_url>")
    title = message.command[1]
    source_url = message.command[2]
    job_session = get_session()
    job = Job(job_type="single_upload", status="pending", payload={"title": title, "source_url": source_url})
    job_session.add(job)
    job_session.commit()
    job_session.refresh(job)
    job_session.close()
    await message.reply_text(f"Queued job id={job.id}")

@app.on_message(filters.command("episode_add"))
async def episode_add(client, message):
    if len(message.command) < 4:
        return await message.reply_text("Usage: /episode_add <series_id> <ep_number> <media_url>")
    series_id = message.command[1]
    try:
        ep_number = int(message.command[2])
    except ValueError:
        return await message.reply_text("ep_number must be an integer")
    source_url = message.command[3]
    session = get_session()
    existing = session.query(Episode).filter_by(series_id=series_id, episode_number=ep_number).first()
    if existing:
        session.close()
        return await message.reply_text("Episode already exists.")
    ep = Episode(series_id=series_id, episode_number=ep_number, source_url=source_url, processed=False)
    session.add(ep)
    session.commit()
    session.close()
    await message.reply_text("Episode added.")

@app.on_message(filters.command("process_pending"))
async def process_pending(client, message):
    session = get_session()
    eps = session.query(Episode).filter_by(processed=False).all()
    count = len(eps)
    session.close()
    asyncio.create_task(process_episode_queue())
    await message.reply_text(f"Processing {count} pending episodes...")

async def _http_stream_to_file(url: str, dest_path: str, headers=None, cookies=None):
    import httpx
    async with httpx.AsyncClient(timeout=None, headers=headers or {}, cookies=cookies or {}, follow_redirects=True) as client:
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                async for chunk in r.aiter_bytes():
                    f.write(chunk)
    return dest_path

async def download_source(url: str, dest_path: str):
    domain = normalize_domain(url)
    adapter = find_adapter_for_domain(domain)
    headers = {}
    cookies = {}
    direct_url = url
    if adapter:
        site_cred = fetch_site_credential_for_url(url)
        user_id = site_cred.user_id if site_cred else None
        password = get_plain_password(site_cred) if site_cred else None
        task = await adapter.prepare_download(media_url=url, user_id=user_id, password=password)
        direct_url = task.direct_url
        headers = task.headers or {}
        cookies = task.cookies or {}
    return await _http_stream_to_file(direct_url, dest_path, headers=headers, cookies=cookies)

async def process_episode_queue():
    session = get_session()
    unprocessed = session.query(Episode).filter_by(processed=False).all()
    for ep in unprocessed:
        try:
            temp_dir = "work_tmp"
            import os
            os.makedirs(temp_dir, exist_ok=True)
            raw_path = f"{temp_dir}/raw_{ep.series_id}_{ep.episode_number}.mp4"
            await download_source(ep.source_url, raw_path)
            meta = {"title": f"{ep.series_id} Episode {ep.episode_number}"}
            if settings.WATERMARK_ENABLED:
                wm_image = settings.WATERMARK_IMAGE_PATH if settings.WATERMARK_IMAGE_PATH else None
                wm_text = settings.WATERMARK_TEXT if settings.WATERMARK_TEXT else None
                orig_processed = f"{temp_dir}/original_{ep.series_id}_{ep.episode_number}.mp4"
                await apply_watermark_and_metadata(raw_path, orig_processed, meta, img=wm_image, text=wm_text)
                original_for_variants = orig_processed
            else:
                original_for_variants = raw_path
            variants = await build_all_variants(
                original_for_variants, temp_dir, settings.AUDIO_LANGUAGES_ALLOWED, settings.SUBTITLE_LANGUAGES_ALLOWED
            )
            file_links = {}
            for quality, path in variants.items():
                fname = build_filename(f"{ep.series_id}_E{ep.episode_number}", quality, settings.META_TAGS)
                backend = storage_backends.get("telegram")
                link_id = await backend.store_file(path, fname)
                short_link = await shorten_url(link_id, settings.SHORTENER_PRIMARY, settings.SHORTENER_FALLBACKS)
                file_links[quality] = short_link
            buttons = []
            for q, lnk in file_links.items():
                buttons.append([InlineKeyboardButton(q, url=lnk)])
            msg = await app.send_message(
                chat_id=settings.PUBLISH_CHANNEL_ID,
                text=f"{ep.series_id} Episode {ep.episode_number}",
                reply_markup=InlineKeyboardMarkup(buttons[:settings.MAX_INLINE_BUTTONS])
            )
            ep.processed = True
            ep.published_message_id = msg.id
            session.add(ep)
            session.commit()
        except Exception as e:
            logger.error("Error processing episode %s %s: %s", ep.series_id, ep.episode_number, e)
    session.close()

@app.on_message(filters.command("account_add"))
async def account_add_handler(client, message):
    if not message.from_user or not _is_admin(message.from_user.id):
        return await message.reply_text("Unauthorized.")
    if len(message.command) < 4:
        return await message.reply_text("Usage: /account_add <provider> <user_id> <password>")
    provider = message.command[1]
    user_id = message.command[2]
    password = " ".join(message.command[3:])
    enc = encrypt_str(password)
    session = get_session()
    existing = session.query(Account).filter_by(provider=provider, user_id=user_id).first()
    if existing:
        existing.password_enc = enc
        session.add(existing)
        session.commit()
        session.close()
        return await message.reply_text(f"Account updated: {provider} / {_mask_user_id(user_id)}")
    acc = Account(provider=provider, user_id=user_id, password_enc=enc)
    session.add(acc)
    session.commit()
    session.close()
    await message.reply_text(f"Account added: {provider} / {_mask_user_id(user_id)}")

@app.on_message(filters.command("account_list"))
async def account_list_handler(client, message):
    if not message.from_user or not _is_admin(message.from_user.id):
        return await message.reply_text("Unauthorized.")
    session = get_session()
    accounts = session.query(Account).order_by(Account.provider.asc(), Account.user_id.asc()).all()
    session.close()
    if not accounts:
        return await message.reply_text("No accounts stored.")
    lines = ["Accounts:"]
    for a in accounts:
        lines.append(f"- {a.provider}: {_mask_user_id(a.user_id)}")
    await message.reply_text("\n".join(lines))

@app.on_message(filters.command("account_delete"))
async def account_delete_handler(client, message):
    if not message.from_user or not _is_admin(message.from_user.id):
        return await message.reply_text("Unauthorized.")
    if len(message.command) < 3:
        return await message.reply_text("Usage: /account_delete <provider> <user_id>")
    provider = message.command[1]
    user_id = " ".join(message.command[2:])
    session = get_session()
    acc = session.query(Account).filter_by(provider=provider, user_id=user_id).first()
    if not acc:
        session.close()
        return await message.reply_text("Account not found.")
    session.delete(acc)
    session.commit()
    session.close()
    await message.reply_text(f"Deleted account: {provider} / {_mask_user_id(user_id)}")

@app.on_message(filters.command("site_cred_add"))
async def site_cred_add_handler(client, message):
    if not message.from_user or not _is_admin(message.from_user.id):
        return await message.reply_text("Unauthorized.")
    if len(message.command) < 4:
        return await message.reply_text("Usage: /site_cred_add <site_url> <user_id> <password>")
    site_url = message.command[1]
    user_id = message.command[2]
    password = " ".join(message.command[3:])
    domain = normalize_domain(site_url)
    enc = encrypt_str(password)
    session = get_session()
    existing = session.query(SiteCredential).filter_by(domain=domain, user_id=user_id).first()
    if existing:
        existing.password_enc = enc
        session.add(existing)
        session.commit()
        session.close()
        return await message.reply_text(f"Site credential updated: {domain} / {_mask_user_id(user_id)}")
    cred = SiteCredential(domain=domain, user_id=user_id, password_enc=enc)
    session.add(cred)
    session.commit()
    session.close()
    await message.reply_text(f"Site credential added: {domain} / {_mask_user_id(user_id)}")

@app.on_message(filters.command("site_cred_list"))
async def site_cred_list_handler(client, message):
    if not message.from_user or not _is_admin(message.from_user.id):
        return await message.reply_text("Unauthorized.")
    session = get_session()
    creds = session.query(SiteCredential).order_by(SiteCredential.domain.asc(), SiteCredential.user_id.asc()).all()
    session.close()
    if not creds:
        return await message.reply_text("No site credentials stored.")
    lines = ["Site credentials:"]
    for c in creds:
        lines.append(f"- {c.domain}: {_mask_user_id(c.user_id)}")
    await message.reply_text("\n".join(lines))

@app.on_message(filters.command("site_cred_delete"))
async def site_cred_delete_handler(client, message):
    if not message.from_user or not _is_admin(message.from_user.id):
        return await message.reply_text("Unauthorized.")
    if len(message.command) < 3:
        return await message.reply_text("Usage: /site_cred_delete <site_url> <user_id>")
    site_url = message.command[1]
    user_id = " ".join(message.command[2:])
    domain = normalize_domain(site_url)
    session = get_session()
    cred = session.query(SiteCredential).filter_by(domain=domain, user_id=user_id).first()
    if not cred:
        session.close()
        return await message.reply_text("Site credential not found.")
    session.delete(cred)
    session.commit()
    session.close()
    await message.reply_text(f"Deleted site credential: {domain} / {_mask_user_id(user_id)}")

@app.on_message(filters.command("status"))
async def status_handler(client, message):
    session = get_session()
    total = session.query(Episode).count()
    done = session.query(Episode).filter_by(processed=True).count()
    session.close()
    await message.reply_text(f"Episodes total={total}, processed={done}")

async def startup():
    init_db()
    init_registry()
    global storage_backends
    storage_backends = build_backends(app, settings)
    logger.info("Bot started with lawful adapter registry initialized.")

def main():
    app.add_handler  # placeholder
    app.run()

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(startup())
    main()
