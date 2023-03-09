from typing import Optional

import sentry_sdk
from pydantic import BaseSettings
from sentry_sdk.integrations.redis import RedisIntegration


class Settings(BaseSettings):
    DEBUG: bool = False
    DB_URL: str
    REDIS_URL: str
    API_SECRET: str
    ENV = "production"
    MEILI_API_KEY: Optional[str]
    MEILI_API_URL: str
    SENTRY_DSN: Optional[str]
    INSERT_SIZE: Optional[int]
    INSERT_INTERVAL: Optional[int]

    class Config:
        env_file = ".env"


settings = Settings()
TORTOISE_ORM = {
    "apps": {
        "models": {
            "models": ["meilisync_admin.models", "aerich.models"],
            "default_connection": "default",
        },
    },
    "connections": {"default": settings.DB_URL},
}
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENV,
        integrations=[RedisIntegration()],
        traces_sample_rate=1.0,
    )
