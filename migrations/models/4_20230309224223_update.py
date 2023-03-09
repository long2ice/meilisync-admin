from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `meilisearch` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `label` VARCHAR(255) NOT NULL,
    `api_url` VARCHAR(255) NOT NULL UNIQUE,
    `api_key` VARCHAR(255) NOT NULL,
    `insert_size` INT,
    `insert_interval` INT
) CHARACTER SET utf8mb4;
        INSERT INTO `meilisearch` (`label`, `api_url`, `api_key`) VALUES ('localhost', 'http://localhost:7700', '');
        ALTER TABLE `sync` ADD `meilisearch_id` INT NOT NULL DEFAULT 1;
        ALTER TABLE `sync` ADD UNIQUE INDEX `uid_sync_meilise_43d222` (`meilisearch_id`, `source_id`, `table`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `sync` DROP FOREIGN KEY `fk_sync_meilisea_34716076`;
        ALTER TABLE `sync` DROP INDEX `uid_sync_meilise_43d222`;
        ALTER TABLE `sync` DROP COLUMN `meilisearch_id`;
        DROP TABLE IF EXISTS `meilisearch`;
        ALTER TABLE `sync` ADD UNIQUE INDEX `uid_sync_source__5e331e` (`source_id`, `table`);"""
