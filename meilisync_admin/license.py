import datetime
import os

import aiofiles
from cryptography.fernet import Fernet
from loguru import logger
from pydantic import BaseModel

from meilisync_admin.settings import settings

ENCRYPT_KEY = b"AAFCOToFiXipuZIx0MDaUohmS3IVisALfmE_ylk9zRI="


class License(BaseModel):
    expire: datetime.date
    name: str

    @property
    def is_expired(self):
        return self.expire < datetime.date.today()


LICENSE = None


async def load_license():
    global LICENSE
    if not os.path.exists(settings.LICENSE):
        raise RuntimeError("License file not found")
    async with aiofiles.open(settings.LICENSE, "r") as f:
        content = await f.read()
        try:
            content = Fernet(ENCRYPT_KEY).decrypt(content).decode()
            LICENSE = License.parse_raw(content)
        except Exception as e:
            raise RuntimeError(f"Invalid license file: {e}")
        if LICENSE.is_expired:
            raise RuntimeError("License expired")
        logger.info(
            f"License loaded, expire at: {LICENSE.expire}, license to: {LICENSE.name}"
        )
