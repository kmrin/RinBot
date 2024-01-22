import aiohttp, asyncio, requests, os, discord
from PIL import Image, ImageFont, ImageDraw
from discord import Webhook
from discord.ext.commands import Bot
from rinbot.base.logger import logger
from rinbot.base.helpers import load_lang, format_date
from rinbot.base.db_man import *
from rinbot.base.colors import *

text = load_lang()

# Downloads the images from the shop
async def get_shop(api:str) -> dict:
    logger.info(text['FN_FS_GETTING'])
    response = requests.get("https://fnbr.co/api/shop", headers={"x-api-key": api})
    response = response.json()
    
    types = ["glider", "outfit", "pickaxe", "bundle", "backpack"]
    rarities = ["common", "uncommon", "rare", "epic", "legendary", "exotic", "mythic", 
                "icon_series", "dc_series", "frozen_series", "gaming_legends", "handmade",
                "lava_series", "marvel_series", "shadow", "slurp", "star_wars", "transcendent"]

    items = []

    for i in response["data"]["featured"]:
        if i["type"] in types and i["rarity"] in rarities:
            items.append({"name": i["name"], "type": i["type"], "price": i["price"], "rarity": i["rarity"], "image": i["images"]["icon"] if not i["images"]["featured"] else i["images"]["featured"]})
    logger.info("Items gathered")
    
    async def get_image(url, item_name):
        logger.info(f"{text['FN_FS_IMG_GET']} {item_name}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/downloaded/{item_name}.png", "wb") as f:
                        f.write(await response.read())
    
    async def composite_image(item_name, item_rarity, item_price):
        logger.info(f"{text['FN_FS_IMG_GEN']} {item_name}")
        async def add_name(draw):
            if len(item_name) > 18: font_size = 55
            if len(item_name) <= 18: font_size = 75
            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf", font_size)
            draw.text((333, 585), item_name, fill=(255, 255, 255), anchor="mm", font=font)
        async def add_currency(draw):
            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf", 80)
            draw.text((85, 50), item_price, fill=(255, 255, 255), anchor="lm", font=font)

        # Create new image obj
        image = Image.new("RGBA", (650, 650))
        
        # Load images
        item_image = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/downloaded/{item_name}.png")
        rarity_bg = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/borders/{item_rarity}.png")
        bottom_banner = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/borders/bottom_banner.png")
        rarity_border = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/borders/{item_rarity}_border.png")
        vbuck = Image.open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/composite/vbuck.png")
        
        # Resize all to fit
        item_image = item_image.resize(image.size, Image.LANCZOS)
        rarity_bg = rarity_bg.resize(image.size, Image.LANCZOS)
        rarity_border = rarity_border.resize(image.size, Image.LANCZOS)
        bottom_banner = bottom_banner.resize(image.size, Image.LANCZOS)
        vbuck = vbuck.resize((70, 70), Image.LANCZOS)
        _, _, _, vbuck_mask = vbuck.split()
        
        # Composite base structure together
        final = Image.alpha_composite(rarity_bg.convert("RGBA"), item_image.convert("RGBA"))
        final = Image.alpha_composite(final.convert("RGBA"), bottom_banner.convert("RGBA"))
        final = Image.alpha_composite(final.convert("RGBA"), rarity_border.convert("RGBA"))
        final.paste(vbuck, (15, 15), vbuck_mask)
        
        # Add text
        draw = ImageDraw.Draw(final)
        await add_name(draw)
        await add_currency(draw)
        
        # Save
        final.save(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/images/{item_name}.png")
        
        # Delete original image
        await asyncio.sleep(0.2)
        path = f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/downloaded/{item_name}.png"
        if os.path.isfile(path): os.remove(path)
    
    async def generate_images(items):
        download_tasks = []
        composite_tasks = []
        for i in items:
            download_tasks.append(get_image(i["image"], i["name"]))
            composite_tasks.append(composite_image(i["name"], i["rarity"], i["price"]))
        await asyncio.gather(*download_tasks)
        await asyncio.gather(*composite_tasks)
    
    await generate_images(items)
    return {"date": response["data"]["date"], "count": len(response["data"]["featured"])}

# Shows the daily shop
async def show_fn_daily_shop(client:Bot, key:str) -> None:
    """
    #### Show Fortnite Daily Shop
    This function iterates through each guild the bot is in
    checks if they have an active channel for the daily shop
    and if so, shows the daily shop on that channel
    """
    # Grab shop data
    logger.info(text['DAILY_SHOP_UPDATING'])
    shop = await get_shop(api=key)
    
    # Vals
    img_dir = f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/images"
    img_files = [f for f in os.listdir(img_dir) if f.endswith(".png")]
    embed = discord.Embed(
        title=f"{text['DAILY_SHOP_EMBED'][0]} **{format_date(shop['date'])}**",
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
        logger.info(f"{text['FN_FS_BATCH_GEN']} {guild}")
        return batches
    
    # Sends all batches to their respective channels
    async def send_batches(hook:Webhook):
        batches = await generate_batches(hook.guild.name)
        await hook.send(embed=embed)
        for i, batch in enumerate(batches):
            await hook.send(files=batch)
            logger.info(f"{text['FN_FS_BATCH_SEND'][0]} {i} {text['FN_FS_BATCH_SEND'][1]} {hook.channel.name} (ID: {hook.channel.id})")

    # Generate the batches
    send_batch_tasks = []
    for guild in client.guilds:
        shop_channels = await get_table("daily_shop_channels")
        if str(guild.id) in shop_channels:
            if shop_channels[str(guild.id)]["active"]:
                channel = client.get_channel(shop_channels[str(guild.id)]["channel_id"]) or await client.fetch_channel(shop_channels[str(guild.id)]["channel_id"])
                channel_hooks = await channel.webhooks()
                if not channel_hooks:
                    channel_hook = await channel.create_webhook(name=text['FN_FS_HOOK_NAME'])
                else:
                    channel_hook = channel_hooks[0]
                await channel_hook.edit(name=text['FN_FS_HOOK_NAME'], avatar=await client.user.avatar.read())
                send_batch_tasks.append(asyncio.create_task(send_batches(channel_hook)))
    await asyncio.gather(*send_batch_tasks)
    
    # Delete images to prevent cache buildup and mixing with other shop rotations
    for file in os.listdir(img_dir):
        os.remove(os.path.join(img_dir, file))
    logger.info(text['DAILY_SHOP_UPDATED'])