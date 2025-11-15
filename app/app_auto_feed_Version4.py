import asyncio, logging
from .db import get_session, Episode
from .config import settings

logger = logging.getLogger("auto_feed")

async def poll_feed(fetch_function):
    items = await fetch_function()
    session = get_session()
    for item in items:
        existing = session.query(Episode).filter_by(
            series_id=item["series_id"],
            episode_number=item["episode_number"]
        ).first()
        if existing:
            continue
        ep = Episode(
            series_id=item["series_id"],
            episode_number=item["episode_number"],
            source_url=item["source_url"],
            processed=False
        )
        session.add(ep)
    session.commit()
    session.close()

async def scheduler_loop(fetch_function, interval_min: int):
    while settings.ENABLE_AUTO_SCHEDULER:
        try:
            await poll_feed(fetch_function)
        except Exception as e:
            logger.error("Feed polling error: %s", e)
        await asyncio.sleep(interval_min * 60)