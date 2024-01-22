from __future__ import annotations
import json, os, requests
from typing import Dict, Optional
from rinbot.base.logger import logger
from rinbot.base.helpers import load_lang
from .useful import JSON

text = load_lang()

def create_json(filename:str, formats=None) -> None:
    file_path = f"{os.path.realpath(os.path.dirname(__file__))}/../cache/valorant/{filename}.json"
    file_dir = os.path.dirname(file_path)
    os.makedirs(file_dir, exist_ok=True)
    if not formats: formats = {}
    formats = {"valorant_version": formats}
    if not os.path.exists(file_path):
        with open(file_path, "w") as fp:
            json.dump(formats, fp, indent=2)

def get_valorant_version() -> Optional[str]:
    logger.info(text['VAL_CACHE_VERSION'])
    resp = requests.get("https://valorant-api.com/v1/version")
    return resp.json()["data"]["manifestId"]

def fetch_skin() -> None:
    data = JSON.read('cache')
    logger.info(text['VAL_CACHE_WEAPON_SKIN'])
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
        JSON.save('cache', data)

def fetch_tier() -> None:
    data = JSON.read('cache')
    logger.info(text['VAL_CACHE_TIER_SKIN'])
    resp = requests.get('https://valorant-api.com/v1/contenttiers/')
    if resp.status_code == 200:
        json = {}
        for tier in resp.json()['data']:
            json[tier['uuid']] = {
                'uuid': tier['uuid'],
                'name': tier['devName'],
                'icon': tier['displayIcon'],}
        data['tiers'] = json
        JSON.save('cache', data)

def pre_fetch_price() -> None:
    try:
        logger.info(text['VAL_CACHE_PRE_FETCH'])
        data = JSON.read('cache')
        pre_json = {'is_price': False}
        data['prices'] = pre_json
        JSON.save('cache', data)
    except Exception as e:
        logger.error(text['VAL_CACHE_PRE_FETCH_CANT'])

def fetch_currencies() -> None:
    data = JSON.read('cache')
    logger.info(text['VAL_CACHE_CURRENCIES'])
    resp = requests.get(f'https://valorant-api.com/v1/currencies?language=all')
    if resp.status_code == 200:
        payload = {}
        for currencie in resp.json()['data']:
            payload[currencie['uuid']] = {
                'uuid': currencie['uuid'],
                'names': currencie['displayName'],
                'icon': currencie['displayIcon'],}
        data['currencies'] = payload
        JSON.save('cache', data)

def fetch_price(data_price: Dict) -> None:
    data = JSON.read('cache')
    logger.info(text['VAL_CACHE_PRICE'])
    payload = {}
    for skin in data_price['Offers']:
        if skin["OfferID"] in data['skins']:
            (*cost,) = skin["Cost"].values()
            payload[skin['OfferID']] = cost[0]
    data['prices'] = payload
    JSON.save('cache', data)

def get_cache() -> None:
    create_json('cache', get_valorant_version())

    fetch_skin()
    fetch_tier()
    pre_fetch_price()
    fetch_currencies()

    logger.info(text['VAL_CACHE_LOADED'])