BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "bot" (
	"token"	TEXT
);
CREATE TABLE IF NOT EXISTS "owners" (
	"user_id"	INTEGER
);
CREATE TABLE IF NOT EXISTS "admins" (
	"guild_id"	INTEGER,
	"user_id"	INTEGER
);
CREATE TABLE IF NOT EXISTS "blacklist" (
	"guild_id"	INTEGER,
	"user_id"	INTEGER
);
CREATE TABLE IF NOT EXISTS "guilds" (
	"guild_id"	INTEGER,
	"currency_emoji" TEXT
);
CREATE TABLE IF NOT EXISTS "currency" (
	"guild_id"	INTEGER,
	"user_id"	INTEGER,
	"wallet"	INTEGER DEFAULT 500,
	"messages"	INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS "store" (
	"guild_id"	INTEGER,
	"id"	INTEGER,
	"name"	TEXT,
	"price"	INTEGER,
	"type"	INTEGER
);
CREATE TABLE IF NOT EXISTS "history_guilds" (
    "guild_id" INTEGER,
	"title"	TEXT,
	"url"	TEXT
);
CREATE TABLE IF NOT EXISTS "warns" (
	"guild_id"	INTEGER,
	"user_id"	INTEGER,
	"moderator_id"	INTEGER,
	"warn"	TEXT,
	"id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "history_individual" (
    "user_id" INTEGER,
	"title"	TEXT,
	"url"	TEXT
);
CREATE TABLE IF NOT EXISTS "daily_shop_channels" (
	"guild_id"	INTEGER,
	"fortnite_active"	INTEGER DEFAULT 0,
	"fortnite_channel_id"	INTEGER,
	"valorant_active"	INTEGER DEFAULT 0,
	"valorant_channel_id"	INTEGER
);
CREATE TABLE IF NOT EXISTS "valorant" (
	"user_id"	INTEGER,
	"active"	INTEGER DEFAULT 0,
	"type"	INTEGER DEFAULT 0,
	"target_guild"	INTEGER
);
CREATE TABLE IF NOT EXISTS "welcome_channels" (
	"guild_id"	INTEGER,
	"active"	INTEGER DEFAULT 0,
	"channel_id"	INTEGER,
	"custom_msg"    TEXT
);
CREATE TABLE IF NOT EXISTS "tts" (
	"guild_id"	INTEGER,
	"active"	INTEGER DEFAULT 0,
	"channel_id"	INTEGER,
	"say_user"	INTEGER DEFAULT 0,
	"language"	TEXT
);
COMMIT;
