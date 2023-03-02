from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `source` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `label` VARCHAR(255) NOT NULL,
    `type` VARCHAR(8) NOT NULL  COMMENT 'mongo: mongo\nmysql: mysql\npostgres: postgres',
    `connection` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `sync` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `label` VARCHAR(255) NOT NULL,
    `full_sync` BOOL NOT NULL  DEFAULT 0,
    `table` VARCHAR(255) NOT NULL UNIQUE,
    `index` VARCHAR(255) NOT NULL,
    `primary_key` VARCHAR(255) NOT NULL  DEFAULT 'id',
    `enabled` BOOL NOT NULL  DEFAULT 1,
    `fields` JSON,
    `source_id` INT NOT NULL,
    CONSTRAINT `fk_sync_source_365ef51f` FOREIGN KEY (`source_id`) REFERENCES `source` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
