import os
import json
import uuid
import contextlib

from datetime import datetime, UTC
from typing import Optional, Dict, Any
from .resources import get_item_type

from rinbot.core.paths import Path
from rinbot.core.json_manager import read

current_season_id = '99ac9283-4dd3-5248-2e01-8baf778affb4'
current_season_end = datetime(2022, 8, 24, 17, 0, 0)
final_directory = Path.valorant

def join_path(p: str) -> str:
    return os.path.join(Path.valorant, f'{p}.json')

def timestamp_utc() -> float:
    return datetime.timestamp(datetime.now(UTC))

def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False

def iso_to_time(iso: datetime) -> datetime:
    timestamp = datetime.strptime(iso, '%Y-%m-%dT%H:%M:%S%z').timestamp()
    time = datetime.fromtimestamp(timestamp, UTC)
    return time

def data_folder() -> None:
    if not os.path.exists(final_directory):
        os.makedirs(final_directory)

class GetItems:
    @classmethod
    def get_item_by_type(cls, ItemType: str, uuid: str) -> Dict[str, Any]:
        item_type = get_item_type(ItemType)
        
        if item_type == 'Agents':
            ...
        elif item_type == 'Sprays':
            return cls.get_spray(uuid)
        elif item_type == 'Gun Buddies':
            return cls.get_buddie(uuid)
        elif item_type == 'Player Cards':
            return cls.get_playercard(uuid)
        elif item_type == 'Skins':
            return cls.get_skin(uuid)
        elif item_type == 'Player titles':
            return cls.get_title(uuid)
    
    def get_skin(uuid: str) -> Dict[str, Any]:
        try:
            skin_data = read(join_path('cache'))
            skin = skin_data["skins"][uuid]
        except KeyError:
            pass
        return skin

    def get_skin_price(uuid: str) -> str:
        data = read(join_path('cache'))
        price = data["prices"]
        try:
            cost = price[uuid]
        except:
            cost = '-'
        return cost

    def get_skin_tier_icon(skin: str) -> str:
        skindata = read(join_path('cache'))
        tier_uuid = skindata["skins"][skin]['tier']
        tier = skindata['tiers'][tier_uuid]["icon"]
        return tier

    def get_spray(uuid: str) -> Dict[str, Any]:
        data = read(join_path('cache'))
        spray = None
        with contextlib.suppress(Exception):
            spray = data["sprays"][uuid]
        return spray

    def get_title(uuid: str) -> Dict[str, Any]:
        data = read(join_path('cache'))
        title = None
        with contextlib.suppress(Exception):
            title = data["titles"][uuid]
        return title
    
    def get_playercard(uuid: str) -> Dict[str, Any]:
        data = read(join_path('cache'))
        title = None
        with contextlib.suppress(Exception):
            title = data["playercards"][uuid]
        return title

    def get_buddie(uuid: str) -> Dict:
        data = read(join_path('cache'))
        title = None
        with contextlib.suppress(Exception):
            title = data["buddies"][uuid]
        return title

    def get_skin_lvl_or_name(name: str, uuid: str) -> Dict[str, Any]:
        data = read(join_path('cache'))
        skin = None
        with contextlib.suppress(Exception):
            skin = data["skins"][uuid]
        with contextlib.suppress(Exception):
            if skin is None:
                skin = [data["skins"][x] for x in data["skins"] if data["skins"][x]['name'] in name][0]
        return skin

    def get_tier_name(skin_uuid: str) -> Optional[str]:
        try:
            data = read(join_path('cache'))
            uuid = data['skins'][skin_uuid]['tier']
            name = data['tiers'][uuid]['name']
        except KeyError:
            pass
        return name
    
    def get_bundle(uuid: str) -> Dict[str, Any]:
        data = read(join_path('cache'))
        bundle = None
        with contextlib.suppress(Exception):
            bundle = data["bundles"][uuid]
        return bundle

class GetFormat:
    def offer_format(data: Dict, language: str) -> Dict[str, Dict]:
        offer_list = data['SkinsPanelLayout']['SingleItemOffers']
        duration = data['SkinsPanelLayout']['SingleItemOffersRemainingDurationInSeconds']

        skin_count = 0
        skin_source = {}

        for uuid in offer_list:
            skin = GetItems.get_skin(uuid)
            name, icon = skin['names']['en-US' if language == 'en' else language], skin['icon']

            price = GetItems.get_skin_price(uuid)
            tier_icon = GetItems.get_skin_tier_icon(uuid)

            if skin_count == 0:
                skin1 = dict(name=name, icon=icon, price=price, tier=tier_icon, uuid=uuid)
            elif skin_count == 1:
                skin2 = dict(name=name, icon=icon, price=price, tier=tier_icon, uuid=uuid)
            elif skin_count == 2:
                skin3 = dict(name=name, icon=icon, price=price, tier=tier_icon, uuid=uuid)
            elif skin_count == 3:
                skin4 = dict(name=name, icon=icon, price=price, tier=tier_icon, uuid=uuid)
            skin_count += 1

        skin_source = {'skin1': skin1, 'skin2': skin2, 'skin3': skin3, 'skin4': skin4, 'duration': duration}

        return skin_source

    def nightmarket_format(offer: Dict, response: Dict, language: str) -> Dict[str, Any]:
        try:
            night_offer = offer['BonusStore']['BonusStoreOffers']
        except KeyError:
            print(response.get('NIGMARKET_HAS_END', 'Nightmarket has been ended'))
        duration = offer['BonusStore']['BonusStoreRemainingDurationInSeconds']

        night_market = {}
        count = 0
        for x in night_offer:
            count += 1
            price = (*x['Offer']['Cost'].values(),)
            Disprice = (*x['DiscountCosts'].values(),)

            uuid = x['Offer']['OfferID']
            skin = GetItems.get_skin(uuid)
            name = skin['names']['en-US' if language == 'en' else language]
            icon = skin['icon']
            tier = GetItems.get_skin_tier_icon(uuid)

            night_market['skin' + f'{count}'] = {
                'uuid': uuid,
                'name': name,
                'tier': tier,
                'icon': icon,
                'price': price[0],
                'disprice': Disprice[0],
            }
        data = {'nightmarket': night_market, 'duration': duration}
        return data
