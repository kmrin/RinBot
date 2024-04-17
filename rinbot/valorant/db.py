from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from .auth import Auth
from .cache import fetch_price
from .useful import JSON
from rinbot.base.logger import logger
from rinbot.base.helpers import log_exception, get_lang

text = get_lang()

def timestamp_utc() -> float:
    return datetime.timestamp(datetime.utcnow())

class DATABASE:
    _version = 1
    
    def __init__(self) -> None:
        self.auth = Auth()
    
    def insert_user(self, data:Dict) -> None:
        JSON.save("users", data)
    
    def read_db(self) -> Dict:
        data = JSON.read("users")
        return data
    
    def read_cache(self) -> Dict:
        data = JSON.read("cache")
        return data
    
    def insert_cache(self, data:Dict) -> None:
        JSON.save("cache", data)
    
    async def is_login(self, user_id:int) -> Optional[Dict[str, Any]]:
        db = self.read_db()
        data = db.get(str(user_id), None)
        login = False
        if data is None:
            logger.error(f"{text['VAL_DB_NO_LOGIN']} {user_id}")
        elif login:
            return False
        return data
    
    async def login(self, user_id:int, data:dict) -> Optional[Dict[str, Any]]:
        db = self.read_db()
        auth = self.auth
        auth_data = data['data']
        cookie = auth_data['cookie']['cookie']
        access_token = auth_data['access_token']
        token_id = auth_data['token_id']
        try:
            entitlements_token = await auth.get_entitlements_token(access_token)
            puuid, name, tag = await auth.get_userinfo(access_token)
            region = await auth.get_region(access_token, token_id)
            player_name = f"{name}#{tag}" if tag is not None and tag is not None else "no_username"
            expiry_token = datetime.timestamp(datetime.utcnow() + timedelta(minutes=59))
            data = dict(
                cookie=cookie,
                access_token=access_token,
                token_id=token_id,
                emt=entitlements_token,
                puuid=puuid,
                username=player_name,
                region=region,
                expiry_token=expiry_token,
                notify_mode=None,
                DM_Message=True,)
            db[str(user_id)] = data
            self.insert_user(db)
        except Exception as e:
            log_exception(e)
        else:
            return {'auth': True, 'player': player_name}
    
    def logout(self, user_id: int) -> Optional[bool]:
        try:
            db = self.read_db()
            del db[str(user_id)]
            self.insert_user(db)
        except KeyError:
            logger.error(f"{text['VAL_DB_LOGOUT_ERROR_KEY']}")
        except Exception as e:
            log_exception(e)
        else:
            return True
    
    async def is_data(self, user_id:int) -> Optional[Dict[str, Any]]:
        try:
            auth = await self.is_login(user_id)
            puuid = auth['puuid']
            region = auth['region']
            username = auth['username']
            access_token = auth['access_token']
            entitlements_token = auth['emt']
            notify_mode = auth['notify_mode']
            expiry_token = auth['expiry_token']
            cookie = auth['cookie']
            notify_channel = auth.get('notify_channel', None)
            dm_message = auth.get('DM_Message', None)
            if timestamp_utc() > expiry_token:
                access_token, entitlements_token = await self.refresh_token(user_id, auth)
            headers = {'Authorization': f'Bearer {access_token}', 'X-Riot-Entitlements-JWT': entitlements_token}
            data = dict(
                puuid=puuid,
                region=region,
                headers=headers,
                player_name=username,
                notify_mode=notify_mode,
                cookie=cookie,
                notify_channel=notify_channel,
                dm_message=dm_message,)
            return data
        except:
            return False
    
    async def refresh_token(self, user_id: int, data: Dict) -> Optional[Dict]:
        auth = self.auth
        cookies, access_token, entitlements_token = await auth.redeem_cookies(data['cookie'])
        expired_cookie = datetime.timestamp(datetime.utcnow() + timedelta(minutes=59))
        db = self.read_db()
        db[str(user_id)]['cookie'] = cookies['cookie']
        db[str(user_id)]['access_token'] = access_token
        db[str(user_id)]['emt'] = entitlements_token
        db[str(user_id)]['expiry_token'] = expired_cookie
        self.insert_user(db)
        return access_token, entitlements_token
    
    def insert_skin_price(self, skin_price: Dict, force=False) -> None:
        cache = self.read_cache()
        price = cache['prices']
        check_price = price.get('is_price', None)
        if check_price is False or force:
            fetch_price(skin_price)
    
    async def cookie_login(self, user_id: int, cookie: Optional[str], locale_code: str) -> Optional[Dict[str, Any]]:
        db = self.read_db()
        auth = self.auth
        auth.locale_code = locale_code
        data = await auth.login_with_cookie(cookie)
        cookie = data['cookies']
        access_token = data['AccessToken']
        token_id = data['token_id']
        entitlements_token = data['emt']
        puuid, name, tag = await auth.get_userinfo(access_token)
        region = await auth.get_region(access_token, token_id)
        player_name = f'{name}#{tag}' if tag is not None and tag is not None else 'no_username'
        expiry_token = datetime.timestamp(datetime.utcnow() + timedelta(minutes=59))
        try:
            data = dict(
                cookie=cookie,
                access_token=access_token,
                token_id=token_id,
                emt=entitlements_token,
                puuid=puuid,
                username=player_name,
                region=region,
                expiry_token=expiry_token,
                notify_mode=None,
                DM_Message=True,)
            db[str(user_id)] = data
            self.insert_user(db)
        except Exception as e:
            print(e)
            return {'auth': False}
        else:
            return {'auth': True, 'player': player_name}
