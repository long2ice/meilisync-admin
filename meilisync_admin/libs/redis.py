import redis.asyncio as redis

from meilisync_admin.settings import settings

r = redis.from_url(settings.REDIS_URL)


class Key:
    refresh_lock = "meilisync:refresh_lock:{sync_id}"
