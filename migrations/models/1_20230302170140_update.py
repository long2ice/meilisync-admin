from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        alter table sync drop key `table`;
        ALTER TABLE `sync` ADD UNIQUE INDEX `uid_sync_source__5e331e` (`source_id`, `table`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `sync` DROP INDEX `uid_sync_source__5e331e`;
        ALTER TABLE `sync` ADD UNIQUE INDEX `uid_sync_table_70d76c` (`table`);"""
