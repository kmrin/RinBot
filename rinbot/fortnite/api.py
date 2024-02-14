import aiohttp, asyncio, os, discord
from PIL import Image, ImageFont, ImageDraw
from datetime import datetime
from discord import Webhook
from discord.ext.commands import Bot
from rinbot.base.logger import logger
from rinbot.base.helpers import load_lang, format_date
from rinbot.base.db_man import *
from rinbot.base.colors import *

text = load_lang()

class FortniteAPI():
    __types__ = ["outfit", "pickaxe", "backpack"]

    def __init__(self, language="en", api_key:str=None):
        self.language = language
        self.api_key = api_key
    
    @staticmethod
    def format_playtime(mins:int) -> str:
        return f"{mins // 60:02d}h"
    
    async def format_shop(self, data) -> dict:
        data = data["data"]
        shop = {"date": None, "count": 0, "entries": []}
        
        # Format date
        date:datetime = datetime.strptime(data["date"], "%Y-%m-%dT%H:%M:%SZ")
        shop["date"] = date.strftime("%d/%m/%y")
        
        # Format and append items to the list
        for entry in data["featured"]["entries"]:
            
            # Skip unwanted items
            if entry["bundle"]: continue
            if entry["items"][0]["type"]["value"] not in self.__types__: continue
            
            # Format item
            try:
                item = {
                    "name": entry["items"][0]["name"],
                    "price": entry["finalPrice"],
                    "rarity": entry["items"][0]["rarity"]["value"],
                    "image": entry["newDisplayAsset"]["materialInstances"][0]["images"]["Background"]}
            except KeyError:
                item["image"] = entry["newDisplayAsset"]["materialInstances"][0]["images"]["OfferImage"]
            shop["entries"].append(item)
        
        # Get num of items
        shop["count"] = len(shop["entries"])

        return shop

    async def get_image(self, url, item_name):
        logger.info(f"{text['FN_DS_IMG_GET']} '{item_name}'")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/downloads/{item_name}.webp", "wb") as f:
                        f.write(await response.read())
    
    async def composite_image(self, item_name, item_price):
        logger.info(f"{text['FN_DS_IMG_GEN']} '{item_name}'")
        async def add_name(draw):
            if len(item_name) >= 15: font_size = 55
            if len(item_name) >= 22: font_size = 40
            if len(item_name) >= 28: font_size = 30
            if len(item_name) <= 14: font_size = 75
            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf", font_size)
            draw.text((333, 595), item_name, fill=(255, 255, 255), anchor="mm", font=font)
        async def add_currency(draw):
            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf", 70)
            draw.text((85, 55), str(item_price), fill=(255, 255, 255), anchor="lm", font=font)
        
        # Create img obj
        image = Image.new("RGBA", (650, 650))
        
        # Load images
        item_image = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/downloads/{item_name}.webp")
        bottom_banner = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/composite/bottom_banner.png")
        vbuck = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/composite/vbuck.png")
        
        # Resize all to fit
        item_image = item_image.resize(image.size, Image.LANCZOS)
        bottom_banner = bottom_banner.resize(image.size, Image.LANCZOS)
        vbuck = vbuck.resize((70, 70), Image.LANCZOS)
        _, _, _, vbuck_mask = vbuck.split()
        
        # Composite base structure
        final = Image.alpha_composite(item_image.convert("RGBA"), bottom_banner.convert("RGBA"))
        final.paste(vbuck, (15, 15), vbuck_mask)
        
        # Add text
        draw = ImageDraw.Draw(final)
        await add_name(draw)
        await add_currency(draw)
        
        # Save
        final.save(f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/composites/{item_name}.png")
        
        # Delete original image
        await asyncio.sleep(0.2)
        path = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/downloads/{item_name}.webp"
        if os.path.isfile(path): os.remove(path)

    async def generate_images(self, items):
        downloads = []
        composites = []
        for i in items:
            downloads.append(self.get_image(i["image"], i["name"]))
            composites.append(self.composite_image(i["name"], i["price"]))
        await asyncio.gather(*downloads)
        await asyncio.gather(*composites)
    
    async def get_shop(self) -> dict:
        logger.info(text['FN_DS_GETTING'])
        shop = None
        async with aiohttp.ClientSession() as session:
            async with session.get("https://fortnite-api.com/v2/shop/br", params={"language": self.language}) as response:
                if response.status == 200:
                    shop = await self.format_shop(await response.json())
        if not shop: return None
        try:
            await self.generate_images(shop["entries"])
        except Exception as e:
            img_dir = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/downloads/"
            for f in os.listdir(img_dir):
                f_path = os.path.join(img_dir, f)
                if os.path.isfile(f_path):
                    os.remove(f_path)
            print(e)
            return None
        return shop
    
    async def composite_stats(self, data):
        try:
            try:
                template = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/composite/stats-{self.language.lower()}.png")
            except FileNotFoundError:
                template = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/composite/stats-en.png")
            
            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf", size=35)
            image = template.convert("RGBA")
            draw = ImageDraw.Draw(image)
            
            # Name
            draw.text((1002, 56), str(data["name"]), fill=(50, 50, 50), anchor="mm", font=font)
            draw.text((1000, 54), str(data["name"]), fill=(255, 255, 255), anchor="mm", font=font)

            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf", size=25)
            
            # Level
            draw.text((1202, 97), str(data["level"]), fill=(50, 50, 50), anchor="mm", font=font)
            draw.text((1200, 95), str(data["level"]), fill=(255, 255, 255), anchor="mm", font=font)
            
            # Stats
            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf", size=30)

            positions = {
                "games": 105, 
                "wins": 255, 
                "kills": 455,
                "deaths": 635,
                "kpm": 762, 
                "kd": 862, 
                "winrate": 980, 
                "gametime": 1130}
            heights = {
                "overall": 190, 
                "solo": 355, 
                "duo": 510, 
                "squad": 665}
            
            for type, info in data["stats"].items():
                for key, val in info.items():
                    draw.text((positions[key] + 2, heights[type] + 2), str(val), fill=(50, 50, 50), anchor="mm", font=font)
                    draw.text((positions[key], heights[type]), str(val), fill=(255, 255, 255), anchor="mm", font=font)

            img_path = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/stats/{data['name']}.png"
            image.save(img_path)
            
            return img_path
        except:
            return None

    async def format_stats(self, stats) -> dict:
        data = stats["data"]
        formatted = {
            "name": data["account"]["name"],
            "level": data["battlePass"]["level"],
            "stats": {"overall": {}, "solo": {}, "duo": {}, "squad": {}}}
        
        modes = ["overall", "solo", "duo", "squad"]
        for mode in modes:
            mode_data = data["stats"]["all"][mode]
            formatted["stats"][mode]["games"] = mode_data["matches"]
            formatted["stats"][mode]["wins"] = mode_data["wins"]
            formatted["stats"][mode]["kills"] = mode_data["kills"]
            formatted["stats"][mode]["deaths"] = mode_data["deaths"]
            formatted["stats"][mode]["kpm"] = f'{mode_data["killsPerMatch"]:.2f}'
            formatted["stats"][mode]["kd"] = f'{mode_data["kd"]:.2f}'
            formatted["stats"][mode]["winrate"] = f'{mode_data["winRate"]:.2f}'
            formatted["stats"][mode]["gametime"] = self.format_playtime(mode_data["minutesPlayed"])

        return formatted
    
    async def get_stats(self, player:str=None, lifetime:bool=True) -> dict:
        if not self.api_key: return {"error": "no_api_key"}
        params = {
            "name": player, "timeWindow": "lifetime" if lifetime else "season"}
        async with aiohttp.ClientSession(headers={"Authorization": self.api_key}) as session:
            async with session.get("https://fortnite-api.com/v2/stats/br/v2", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return await self.format_stats(data)
                else:
                    return await response.json()

# Shows the daily shop
async def show_fn_daily_shop(client:Bot) -> None:
    """
    #### Show Fortnite Daily Shop
    This function iterates through each guild the bot is in
    checks if they have an active channel for the daily shop
    and if so, shows the daily shop on that channel
    """
    # Grab shop data
    logger.info(text['DAILY_SHOP_UPDATING'])
    api = FortniteAPI(client.fn_language)
    shop = await api.get_shop()
    
    # Vals
    img_dir = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/fortnite/composites"
    img_files = [f for f in os.listdir(img_dir) if f.endswith(".png")]
    embed = discord.Embed(
        title=f"{text['DAILY_SHOP_EMBED'][0]} **{shop['date']}**",
        description=f"{text['DAILY_SHOP_EMBED'][1]} **{len(img_files)}** {text['DAILY_SHOP_EMBED'][2]} **{shop['count']}** {text['DAILY_SHOP_EMBED'][3]}",
        color=PURPLE)
    
    # Returns a file obj
    async def generate_file(img_name) -> discord.File:
        path = os.path.join(img_dir, img_name)
        return discord.File(path, filename=img_name)
    
    # Generates a list of image batches
    async def generate_batches(guild) -> list:
        batches = []
        for i in range(0, len(img_files), 6):
            batch = []
            img_names = img_files[i:i+6]
            tasks = [generate_file(img) for img in img_names]
            results = await asyncio.gather(*tasks)
            batch.extend(results)
            batches.append(batch)
        logger.info(f"{text['FN_DS_BATCH_GEN']} {guild}")
        return batches
    
    # Sends all batches to their respective channels
    async def send_batches(hook:Webhook):
        batches = await generate_batches(hook.guild.name)
        await hook.send(embed=embed)
        for i, batch in enumerate(batches):
            await hook.send(files=batch)
            logger.info(f"{text['FN_DS_BATCH_SEND'][0]} {i} {text['FN_DS_BATCH_SEND'][1]} {hook.channel.name} (ID: {hook.channel.id})")

    # Generate the batches
    send_batch_tasks = []
    for guild in client.guilds:
        shop_channels = await get_table("daily_shop_channels")
        if str(guild.id) in shop_channels:
            if shop_channels[str(guild.id)]["active"]:
                channel = client.get_channel(shop_channels[str(guild.id)]["channel_id"]) or await client.fetch_channel(shop_channels[str(guild.id)]["channel_id"])
                channel_hooks = await channel.webhooks()
                if not channel_hooks:
                    channel_hook = await channel.create_webhook(name=text['FN_DS_HOOK_NAME'])
                else:
                    channel_hook = channel_hooks[0]
                await channel_hook.edit(name=text['FN_DS_HOOK_NAME'], avatar=await client.user.avatar.read())
                send_batch_tasks.append(asyncio.create_task(send_batches(channel_hook)))
    await asyncio.gather(*send_batch_tasks)
    
    # Delete images to prevent cache buildup and mixing with other shop rotations
    for file in os.listdir(img_dir):
        os.remove(os.path.join(img_dir, file))
    logger.info(text['DAILY_SHOP_UPDATED'])