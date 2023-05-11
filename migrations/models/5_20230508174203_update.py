from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `admin` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `nickname` VARCHAR(255) NOT NULL,
    `email` VARCHAR(255) NOT NULL UNIQUE,
    `last_login_at` DATETIME(6),
    `password` VARCHAR(255) NOT NULL,
    `is_superuser` BOOL NOT NULL  DEFAULT 0,
    `is_active` BOOL NOT NULL  DEFAULT 1
) CHARACTER SET utf8mb4;
        CREATE TABLE IF NOT EXISTS `actionlog` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `ip` VARCHAR(255) NOT NULL,
    `content` JSON NOT NULL,
    `path` VARCHAR(255) NOT NULL,
    `method` VARCHAR(10) NOT NULL,
    `admin_id` INT NOT NULL,
    CONSTRAINT `fk_actionlo_admin_d6fe934d` FOREIGN KEY (`admin_id`) REFERENCES `admin` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `actionlog`;
        DROP TABLE IF EXISTS `admin`;"""
