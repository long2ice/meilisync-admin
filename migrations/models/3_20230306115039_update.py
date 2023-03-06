from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `synclog` ADD `type` VARCHAR(6) NOT NULL  COMMENT 'create: create\nupdate: update\ndelete: delete' DEFAULT 'create';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `synclog` DROP COLUMN `type`;"""
