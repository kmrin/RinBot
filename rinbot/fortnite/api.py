"""
Fortnite API wrapper for rinbot's daily shop and player stats
"""

import os
import aiohttp
import asyncio
import requests

from PIL import ImageFont, ImageDraw, Image
from typing import Union
from datetime import datetime

from rinbot.core.startup_checks import check_cache

from rinbot.core.loggers import Loggers, log_exception
from rinbot.core.paths import get_os_path

logger = Loggers.FORTNITE

class FortniteAPI:
    # __types__ = ['outfit', 'pickaxe', 'backpack']
    
    def __init__(self, language: str='en', api_key: str=None):
        self.language = language
        self.api_key = api_key
    
    @staticmethod
    def __format_playtime(mins: int) -> str:
        return f'{mins // 60:02d}h'
    
    @staticmethod
    async def __shop_get_image(url, item_name):
        logger.info(f'Getting image for "{item_name}"')
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return

                    image_bytes = await response.read()

                    with open(get_os_path(f'../instance/cache/fortnite/downloads/{item_name}.webp'), 'wb') as f:
                        f.write(image_bytes)
        except Exception as e:
            log_exception(e, logger)
    
    @staticmethod
    async def __shop_composite_image(item_name, item_price):
        try:
            logger.info(f'Generating composite for "{item_name}"')

            async def add_name(draw):
                font_size = 30

                if len(item_name) >= 15: font_size = 55
                if len(item_name) >= 22: font_size = 40
                if len(item_name) >= 28: font_size = 30
                if len(item_name) <= 14: font_size = 75

                font = ImageFont.truetype(
                    f"{get_os_path('assets/fonts/fortnite.ttf')}", font_size)

                draw.text((333, 595), item_name, fill=(255, 255, 255), anchor="mm", font=font)

            async def add_currency(draw):
                font = ImageFont.truetype(get_os_path('assets/fonts/fortnite.ttf'), 70)

                draw.text((85, 55), str(item_price), fill=(255, 255, 255), anchor="lm", font=font)

            image = Image.new('RGBA', (650, 650))

            item_image = Image.open(f'{get_os_path(f"../instance/cache/fortnite/downloads/{item_name}.webp")}')
            bottom_banner = Image.open(f'{get_os_path("assets/images/fortnite/composite/bottom_banner.png")}')
            vbuck = Image.open(f'{get_os_path("assets/images/fortnite/composite/vbuck.png")}')

            item_image = item_image.resize(image.size, Image.LANCZOS)
            bottom_banner = bottom_banner.resize(image.size, Image.LANCZOS)
            vbuck = vbuck.resize((70, 70), Image.LANCZOS)
            _, _, _, vbuck_mask = vbuck.split()

            final = Image.alpha_composite(item_image.convert("RGBA"), bottom_banner.convert("RGBA"))
            final.paste(vbuck, (15, 15), vbuck_mask)

            pen = ImageDraw.Draw(final)

            await add_name(pen)
            await add_currency(pen)

            final.save(get_os_path(f'../instance/cache/fortnite/composites/{item_name}.png'))

            await asyncio.sleep(0.2)

            path = f'{get_os_path(f"../instance/cache/fortnite/downloads/{item_name}.webp")}'

            if os.path.isfile(path):
                os.remove(path)
        except Exception as e:
            log_exception(e, logger)
    
    async def __shop_generate_images(self, items):
        try:
            downloads = []
            composites = []

            for i in items:
                print(i)
                downloads.append(self.__shop_get_image(i["image"], i["name"]))
                composites.append(self.__shop_composite_image(i["name"], i["price"]))

            await asyncio.gather(*downloads)
            await asyncio.gather(*composites)
        except Exception as e:
            log_exception(e, logger)

    def __shop_format(self, data) -> dict:        
        try:
            data = data['data']
            shop = {
                'date': None,
                'count': len(data['featured']['entries']),
                'entries': []
            }
            
            date: datetime = datetime.strptime(data['date'], '%Y-%m-%dT%H:%M:%SZ')
            shop['date'] = date.strftime('%d/%m/%y')
            
            for entry in data['featured']['entries']:
                item = {}
                
                try:
                    if entry['bundle']:
                        item['name'] = entry['bundle']['name']
                        item['price'] = entry['finalPrice']
                        item['rarity'] = None
                        
                        try:
                            item['image'] = entry['newDisplayAsset']['materialInstances'][0]['images']['Background']
                        except KeyError:
                            item['image'] = entry['newDisplayAsset']['materialInstances'][0]['images']['OfferImage']
                    elif entry['newDisplayAsset']:
                        try:
                            item['name'] = entry['items'][0]['name']
                            item['price'] = entry['finalPrice']
                            item['rarity'] = entry['items'][0]['rarity']['value']
                            item['image'] = entry['newDisplayAsset']['materialInstances'][0]['images']['Background']
                        except (TypeError, KeyError):
                            try:
                                item['image'] = entry['newDisplayAsset']['materialInstances'][0]['images']['OfferImage']
                            except (TypeError, KeyError):
                                continue
                except (TypeError, KeyError):
                    continue
                
                if item:
                    shop['entries'].append(item)

            return shop
        except Exception as e:
            log_exception(e, logger)
    
    def __stats_composite(self, data) -> Union[str, None]:
        try:
            try:
                template = Image.open(get_os_path(f'assets/images/fortnite/composite/stats-{self.language.lower()}.png'))
            except FileNotFoundError:
                template = Image.open(get_os_path(f'assets/images/fortnite/composite/stats-en.png'))

            font = ImageFont.truetype(f"{os.path.realpath(os.path.dirname(__file__))}/../assets/fonts/fortnite.ttf",
                                      size=35)
            image = template.convert("RGBA")
            draw = ImageDraw.Draw(image)

            draw.text((1002, 56), str(data["name"]), fill=(50, 50, 50), anchor="mm", font=font)
            draw.text((1000, 54), str(data["name"]), fill=(255, 255, 255), anchor="mm", font=font)

            font = ImageFont.truetype(get_os_path('assets/fonts/fortnite.ttf'), size=25)

            draw.text((1202, 97), str(data["level"]), fill=(50, 50, 50), anchor="mm", font=font)
            draw.text((1200, 95), str(data["level"]), fill=(255, 255, 255), anchor="mm", font=font)

            font = ImageFont.truetype(get_os_path('assets/fonts/fortnite.ttf'), size=30)

            positions = {key: 105 + 200 * i for i, key in enumerate(data["stats"].keys())}
            
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

            for item_type, info in data["stats"].items():
                if item_type == 'ltm':
                    continue
                
                for key, val in info.items():
                    draw.text((positions[key] + 2, heights[item_type] + 2), str(val), fill=(50, 50, 50), anchor="mm",
                              font=font)
                    draw.text((positions[key], heights[item_type]), str(val), fill=(255, 255, 255), anchor="mm",
                              font=font)

            img_path = get_os_path(f"../instance/cache/fortnite/stats/{data['name']}.png")

            image.save(img_path)

            return img_path
        except Exception as e:
            log_exception(e, logger)
            return None
    
    def __stats_format(self, stats) -> dict:
        try:
            data = stats["data"]
            formatted = {
                "name": data["account"]["name"],
                "level": data["battlePass"]["level"],
                "stats": {}
            }

            for mode, mode_data in data["stats"]["all"].items():
                if mode_data is not None:
                    formatted["stats"][mode] = {
                        "games": mode_data["matches"],
                        "wins": mode_data["wins"],
                        "kills": mode_data["kills"],
                        "deaths": mode_data["deaths"],
                        "kpm": f'{mode_data["killsPerMatch"]:.2f}',
                        "kd": f'{mode_data["kd"]:.2f}',
                        "winrate": f'{mode_data["winRate"]:.2f}',
                        "gametime": self.__format_playtime(mode_data["minutesPlayed"])
                    }
            return formatted
        except Exception as e:
            log_exception(e, logger)
    
    async def get_shop(self) -> Union[dict, None]:
        # Make sure cache exists
        check_cache()

        logger.info('Getting daily shop')

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://fortnite-api.com/v2/shop/br',
                                    params={'language': self.language}) as response:
                    if response.status != 200:
                        return None

                    shop = await response.json()
                    shop = self.__shop_format(shop)
                try:
                   await self.__shop_generate_images(shop["entries"])
                except Exception as e:
                    img_dir = get_os_path(f'../instance/cache/fortnite/downloads')

                    for f in os.listdir(img_dir):
                        f_path = os.path.join(img_dir, f)

                        if os.path.isfile(f_path):
                            os.remove(f_path)

                    log_exception(e, logger)

            return shop
        except Exception as e:
            log_exception(e, logger)
            return None

    def get_stats(self, player: str=None, lifetime: bool=True) -> Union[dict, list]:
        # Make sure cache exists
        check_cache()

        if not self.api_key:
            return {"error": "no_api_key"}

        params = {"name": player, "timeWindow": "lifetime" if lifetime else "season"}
        headers = {"Authorization": self.api_key}

        try:
            response = requests.get('https://fortnite-api.com/v2/stats/br/v2', params=params, headers=headers)
            if response.status_code != 200:
                return response.json()

            data = response.json()
            stats = self.__stats_format(data)
                        
            img_path = self.__stats_composite(stats)

            return [stats, img_path]
        except Exception as e:
            log_exception(e, logger)
            return None
