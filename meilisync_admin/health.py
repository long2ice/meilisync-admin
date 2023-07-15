from loguru import logger
from tortoise import Tortoise


async def is_database_online():
    try:
        await Tortoise.get_connection("default").execute_query("SELECT 1")
    except Exception as e:
        logger.exception(f"Database is not online: {e}")
        return False
    return {"database": "online"}
