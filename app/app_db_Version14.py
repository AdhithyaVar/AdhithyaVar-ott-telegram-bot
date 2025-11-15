from pymongo import MongoClient
import os
from datetime import datetime

# Get MongoDB connection string (example: use .env for actual application)
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DBNAME = os.getenv("DBNAME", "ottbotdb")

client = MongoClient(MONGODB_URI)
db = client[DBNAME]

# --- Example utility functions and collection access ---

def episode_find_one(series_id, episode_number):
    return db.episodes.find_one({"series_id": series_id, "episode_number": episode_number})

def episode_insert(series_id, episode_number, source_url, processed=False, publish_channel_id=None, storage_profile_name=None, meta=None):
    doc = {
        "series_id": series_id,
        "episode_number": episode_number,
        "source_url": source_url,
        "processed": processed,
        "publish_channel_id": publish_channel_id,
        "storage_profile_name": storage_profile_name,
        "meta": meta if meta else {},
        "created_at": datetime.utcnow()
    }
    db.episodes.insert_one(doc)
    return doc

def episode_update(series_id, episode_number, fields):
    db.episodes.update_one(
        {"series_id": series_id, "episode_number": episode_number},
        {"$set": fields}
    )

def episode_find_all(processed=None):
    query = {}
    if processed is not None:
        query["processed"] = processed
    return list(db.episodes.find(query))

def job_insert(job_type, payload, status="pending", result=None):
    doc = {
        "job_type": job_type,
        "status": status,
        "payload": payload,
        "result": result if result else {},
        "created_at": datetime.utcnow()
    }
    db.jobs.insert_one(doc)
    return doc

def job_find_by_status(status):
    return list(db.jobs.find({"status": status}))

def account_insert(provider, user_id, password_enc):
    doc = {
        "provider": provider,
        "user_id": user_id,
        "password_enc": password_enc,
        "created_at": datetime.utcnow()
    }
    db.accounts.replace_one(
        {"provider": provider, "user_id": user_id},
        doc,
        upsert=True
    )
    return doc

def account_find_all():
    return list(db.accounts.find({}))

def account_delete(provider, user_id):
    db.accounts.delete_one({"provider": provider, "user_id": user_id})

def site_credential_insert(domain, user_id, password_enc):
    doc = {
        "domain": domain,
        "user_id": user_id,
        "password_enc": password_enc,
        "created_at": datetime.utcnow()
    }
    db.site_credentials.replace_one(
        {"domain": domain, "user_id": user_id},
        doc,
        upsert=True
    )
    return doc

def site_credential_find_all():
    return list(db.site_credentials.find({}))

def site_credential_delete(domain, user_id):
    db.site_credentials.delete_one({"domain": domain, "user_id": user_id})

def storage_profile_insert(name, backend, config, telegram_bot_token_enc=None):
    doc = {
        "name": name,
        "backend": backend,
        "config": config,
        "telegram_bot_token_enc": telegram_bot_token_enc,
        "created_at": datetime.utcnow()
    }
    db.storage_profiles.replace_one(
        {"name": name},
        doc,
        upsert=True
    )
    return doc

def storage_profile_find_all():
    return list(db.storage_profiles.find({}))

def storage_profile_find_one(name):
    return db.storage_profiles.find_one({"name": name})

def storage_profile_delete(name):
    db.storage_profiles.delete_one({"name": name})

def channel_config_insert_or_update(publish_channel_id, **kwargs):
    doc = kwargs.copy()
    doc["publish_channel_id"] = publish_channel_id
    doc.setdefault("created_at", datetime.utcnow())
    db.channel_configs.replace_one(
        {"publish_channel_id": publish_channel_id},
        doc,
        upsert=True
    )
    return doc

def channel_config_find_one(publish_channel_id):
    return db.channel_configs.find_one({"publish_channel_id": publish_channel_id})

def channel_config_find_all():
    return list(db.channel_configs.find({}))

def ytdlp_allow_domain(domain):
    doc = {
        "domain": domain.lower(),
        "created_at": datetime.utcnow()
    }
    db.ytdlp_allowed_domains.replace_one(
        {"domain": domain.lower()},
        doc,
        upsert=True
    )
    return doc

def ytdlp_disallow_domain(domain):
    db.ytdlp_allowed_domains.delete_one({"domain": domain.lower()})

def ytdlp_list_domains():
    return [d["domain"] for d in db.ytdlp_allowed_domains.find({})]

# --- No "init_db" needed for MongoDB ---