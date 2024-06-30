from typing import Optional

base_endpoint = "https://pd.{shard}.a.pvp.net"
base_endpoint_glz = "https://glz-{region}-1.{shard}.a.pvp.net"
base_endpoint_shared = "https://shared.{shard}.a.pvp.net"

regions: list = ["na", "eu", "latam", "br", "ap", "kr", "pbe"]
region_shard_override = {
    "latam": "na",
    "br": "na",
}
shard_region_override = {"pbe": "na"}

tiers = {
    '0cebb8be-46d7-c12a-d306-e9907bfc5a25': {
        'name': 'DeluxeTier',
        'emoji': '<:Deluxe:950372823048814632>',
        'color': 0x009587,
    },
    'e046854e-406c-37f4-6607-19a9ba8426fc': {
        'name': 'ExclusiveTier',
        'emoji': '<:Exclusive:950372911036915762>',
        'color': 0xF1B82D,
    },
    '60bca009-4182-7998-dee7-b8a2558dc369': {
        'name': 'PremiumTier',
        'emoji': '<:Premium:950376774620049489>',
        'color': 0xD1548D,
    },
    '12683d76-48d7-84a3-4e09-6985794f0445': {
        'name': 'SelectTier',
        'emoji': '<:Select:950376833982021662>',
        'color': 0x5A9FE2,
    },
    '411e4a55-4e59-7757-41f0-86a53f101bb5': {'name': 'UltraTier', 'emoji': '<:Ultra:950376896745586719>', 'color': 0xEFEB65},
}

def get_item_type(uuid: str) -> Optional[str]:
    """Get item type"""
    item_type = {
        '01bb38e1-da47-4e6a-9b3d-945fe4655707': 'Agents',
        'f85cb6f7-33e5-4dc8-b609-ec7212301948': 'Contracts',
        'd5f120f8-ff8c-4aac-92ea-f2b5acbe9475': 'Sprays',
        'dd3bf334-87f3-40bd-b043-682a57a8dc3a': 'Gun Buddies',
        '3f296c07-64c3-494c-923b-fe692a4fa1bd': 'Player Cards',
        'e7c63390-eda7-46e0-bb7a-a6abdacd2433': 'Skins',
        '3ad1b2b2-acdb-4524-852f-954a76ddae0a': 'Skins chroma',
        'de7caa6b-adf7-4588-bbd1-143831e786c6': 'Player titles',
    }
    return item_type.get(uuid, None)
