import os
import requests

from typing import Optional, Dict

from .useful import join_path

from rinbot.core.loggers import Loggers
from rinbot.core.paths import get_os_path
from rinbot.core.json_manager import read, write

logger = Loggers.VALORANT

def create_json(filename: str, formats=None) -> None:
    file_path = get_os_path(f'../instance/cache/valorant/{filename}.json')
    file_dir = os.path.dirname(file_path)
    
    os.makedirs(file_dir, exist_ok=True)
    
    if not formats:
        formats = {}
    
    formats = {
        'valorant_version': formats
    }
    
    if not os.path.exists(file_path):
        write(file_path, formats, silent=True)

def get_valorant_version() -> Optional[str]:
    logger.info('Getting version')
    
    resp = requests.get('https://valorant-api.com/v1/version')
    
    return resp.json()['data']['manifestId']

def fetch_skin() -> None:
    data = read(join_path('cache'), silent=True)

    logger.info('Getting weapon skins')
    
    resp = requests.get(f'https://valorant-api.com/v1/weapons/skins?language=all')
    if resp.status_code == 200:
        json = {}
        for skin in resp.json()['data']:
            skinone = skin['levels'][0]
            json[skinone['uuid']] = {
                'uuid': skinone['uuid'],
                'names': skin['displayName'],
                'icon': skinone['displayIcon'],
                'tier': skin['contentTierUuid'],}
        data['skins'] = json
        
        write(join_path('cache'), data, silent=True)

def fetch_tier() -> None:
    data = read(join_path('cache'), silent=True)
    
    logger.info('Getting skin tiers')
    
    resp = requests.get('https://valorant-api.com/v1/contenttiers')
    if resp.status_code == 200:
        json = {}
        for tier in resp.json()['data']:
            json[tier['uuid']] = {
                'uuid': tier['uuid'],
                'name': tier['devName'],
                'icon': tier['displayIcon'],}
        data['tiers'] = json
        
        write(join_path('cache'), data, silent=True)

def fetch_currencies() -> None:
    data = read(join_path('cache'), silent=True)
    
    logger.info('Getting currencies')
    
    resp = requests.get(f'https://valorant-api.com/v1/currencies?language=all')
    if resp.status_code == 200:
        payload = {}
        for currencie in resp.json()['data']:
            payload[currencie['uuid']] = {
                'uuid': currencie['uuid'],
                'names': currencie['displayName'],
                'icon': currencie['displayIcon'],}
        data['currencies'] = payload
        
        write(join_path('cache'), data, silent=True)

def pre_fetch_price() -> None:
    data = read(join_path('cache'), silent=True)
    
    logger.info('Getting prices (pre-fetch)')
    
    pre_json = {'is_price': False}
    data['prices'] = pre_json
    
    write(join_path('cache'), data, silent=True)

def fetch_price(data_price: Dict) -> None:
    data = read(join_path('cache'), silent=True)
    
    logger.info('Getting prices')
    
    payload = {}
    for skin in data_price['Offers']:
        if skin["OfferID"] in data['skins']:
            (*cost,) = skin["Cost"].values()
            payload[skin['OfferID']] = cost[0]
    
    data['prices'] = payload
    
    write(join_path('cache'), data, silent=True)

def get_cache() -> None:
    logger.info('Loading cache')
    
    create_json('cache', get_valorant_version())
    
    fetch_skin()
    fetch_tier()
    pre_fetch_price()
    # fetch_price()
    fetch_currencies()
    
    logger.info('Cache loaded')
