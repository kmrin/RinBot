import aiohttp, asyncio, requests, os
from PIL import Image, ImageFont, ImageDraw
from dotenv import load_dotenv

load_dotenv()
API = os.getenv("FNBR_API_KEY")

async def get_shop() -> dict:
    response = requests.get("https://fnbr.co/api/shop", headers={"x-api-key": API})
    response = response.json()
    
    types = ["glider", "outfit", "pickaxe", "bundle", "backpack"]
    rarities = ["common", "uncommon", "rare", "epic", "legendary", "exotic", "mythic", 
                "icon_series", "dc_series", "frozen_series", "gaming_legends", "handmade",
                "lava_series", "marvel_series", "shadow", "slurp", "star_wars", "transcendent"]

    items = []

    for i in response["data"]["featured"]:
        if i["type"] in types and i["rarity"] in rarities:
            items.append({"name": i["name"], "type": i["type"], "price": i["price"], "rarity": i["rarity"], "image": i["images"]["icon"] if not i["images"]["featured"] else i["images"]["featured"]})
    
    async def get_image(url, item_name):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/images/fortnite/downloaded/{item_name}.png", "wb") as f:
                        f.write(await response.read())
    
    async def composite_image(item_name, item_rarity, item_price):
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