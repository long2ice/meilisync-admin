from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `meilisearch` MODIFY COLUMN `api_key` VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `meilisearch` MODIFY COLUMN `api_key` VARCHAR(255) NOT NULL;"""
