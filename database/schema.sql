CREATE TABLE IF NOT EXISTS `blacklist` (
    `user_id` varchar(20) NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS `admins` (
    `user_id` varchar(20) NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS `owners` (
    `user_id` varchar(20) NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS `joined_on` (
    `guild_id` varchar(20) NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS `currency` (
    `user_id` INTEGER NOT NULL,
    `server_id` varchar(20) NOT NULL,
    `wallet` INTEGER NOT NULL DEFAULT 500,
    `messages` INTEGER NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS `warns` (
    `id` int(11) NOT NULL,
    `user_id` varchar(20) NOT NULL,
    `server_id` varchar(20) NOT NULL,
    `moderator_id` varchar(20) NOT NULL,
    `reason` varchar(255) NOT NULL,
    `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS `favorites` (
    `user_id` varchar(20) NOT NULL,
    `data` JSON);

CREATE TABLE IF NOT EXISTS `histories` (
    `server_id` varchar(20) NOT NULL,
    `data` JSON);

CREATE TABLE IF NOT EXISTS `images` (
    `name` varchar(255) NOT NULL,
    `data` BLOB);

CREATE TABLE IF NOT EXISTS `store` (
    `id` int(11) NOT NULL,
    `data` JSON);