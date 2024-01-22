import json, re, ssl, aiohttp, urllib3, certifi, ctypes, sys, contextlib, warnings, discord
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from secrets import token_urlsafe
from rinbot.base.logger import logger
from rinbot.base.helpers import load_lang

text = load_lang()

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _extract_tokens(data: str) -> str:
    pattern = re.compile('access_token=((?:[a-zA-Z]|\d|\.|-|_)*).*id_token=((?:[a-zA-Z]|\d|\.|-|_)*).*expires_in=(\d*)')
    response = pattern.findall(data['response']['parameters']['uri'])[0]
    return response

def _extract_tokens_from_uri(url: str) -> Optional[Tuple[str, Any]]:
    try:
        access_token = url.split("access_token=")[1].split("&scope")[0]
        token_id = url.split("id_token=")[1].split("&")[0]
        return access_token, token_id
    except IndexError:
        logger.error("[Valorant] Invalid cookies")

class Auth:
    RIOT_CLIENT_USER_AGENT = token_urlsafe(111)
    
    CIPHERS13 = ":".join(
        (
            "TLS_CHACHA20_POLY1305_SHA256",
            "TLS_AES_128_GCM_SHA256",
            "TLS_AES_256_GCM_SHA384",
        )
    )
    CIPHERS = ":".join(
        (
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "ECDHE-RSA-CHACHA20-POLY1305",
            "ECDHE-ECDSA-AES128-GCM-SHA256",
            "ECDHE-RSA-AES128-GCM-SHA256",
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-AES128-SHA",
            "ECDHE-RSA-AES128-SHA",
            "ECDHE-ECDSA-AES256-SHA",
            "ECDHE-RSA-AES256-SHA",
            "AES128-GCM-SHA256",
            "AES256-GCM-SHA384",
            "AES128-SHA",
            "AES256-SHA",
            "DES-CBC3-SHA",
        )
    )
    SIGALGS = ":".join(
        (
            "ecdsa_secp256r1_sha256",
            "rsa_pss_rsae_sha256",
            "rsa_pkcs1_sha256",
            "ecdsa_secp384r1_sha384",
            "rsa_pss_rsae_sha384",
            "rsa_pkcs1_sha384",
            "rsa_pss_rsae_sha512",
            "rsa_pkcs1_sha512",
            "rsa_pkcs1_sha1",
        )
    )
    
    def __init__(self) -> None:
        self._auth_ssl_ctx = Auth.create_riot_auth_ssl_ctx()
        self._cookie_jar = aiohttp.CookieJar()
        self.user_agent = Auth.RIOT_CLIENT_USER_AGENT
        self.locale_code = "en-US"
        self.response = {}
        self._headers = {
            "Accept-Encoding": "deflate, gzip, zstd",
            # "user-agent": Auth.RIOT_CLIENT_USER_AGENT % "rso-auth",
            "user-agent": Auth.RIOT_CLIENT_USER_AGENT,
            "Cache-Control": "no-cache",
            "Accept": "application/json",}
    
    @staticmethod
    def create_riot_auth_ssl_ctx() -> ssl.SSLContext:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.load_verify_locations(certifi.where())
        addr = id(ssl_ctx) + sys.getsizeof(object())
        ssl_ctx_addr = ctypes.cast(addr, ctypes.POINTER(ctypes.c_void_p)).contents
        
        libssl: Optional[ctypes.CDLL] = None
        if sys.platform.startswith("win32"):
            for dll_name in (
                "libssl-3.dll",
                "libssl-3-x64.dll",
                "libssl-1_1.dll",
                "libssl-1_1-x64.dll",
            ):
                with contextlib.suppress(FileNotFoundError, OSError):
                    libssl = ctypes.CDLL(dll_name)
                    break
        elif sys.platform.startswith(("linux", "darwin")):
            libssl = ctypes.CDLL(ssl._ssl.__file__)
        
        if libssl is None:
            raise NotImplementedError("Failed to load libsll")
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            ssl_ctx.minimum_version = ssl.TLSVersion.TLSv1
        ssl_ctx.set_alpn_protocols(["http/1.1"])
        ssl_ctx.options |= 1 << 19
        libssl.SSL_CTX_set_ciphersuites(ssl_ctx_addr, Auth.CIPHERS13.encode())
        libssl.SSL_CTX_set_cipher_list(ssl_ctx_addr, Auth.CIPHERS.encode())
        # setting SSL_CTRL_SET_SIGALGS_LIST
        libssl.SSL_CTX_ctrl(ssl_ctx_addr, 98, 0, Auth.SIGALGS.encode())
        return ssl_ctx
    
    async def create_session(self) -> aiohttp.ClientSession:
        conn = aiohttp.TCPConnector(ssl=self._auth_ssl_ctx)
        session = aiohttp.ClientSession(
            connector=conn, raise_for_status=True, cookie_jar=self._cookie_jar)
        return session
    
    async def authenticate(self, username:str, password:str, use_query_response_mode:bool=False) -> Optional[Dict[str, Any]]:
        if username and password:
            self._cookie_jar.clear()
        
        conn = aiohttp.TCPConnector(ssl=self._auth_ssl_ctx)
        
        session = aiohttp.ClientSession(
            connector=conn, raise_for_status=True, cookie_jar=self._cookie_jar)
        
        body = {
            "acr_values": "",
            "claims": "",
            "client_id": "riot-client",
            "code_challenge": "",
            "code_challenge_method": "",
            "nonce": token_urlsafe(16),
            "redirect_uri": "http://localhost/redirect",
            "response_type": "token id_token",
            "scope": "openid link ban lol_region account",
        }
        
        if use_query_response_mode:
            body["response_mode"] = "query"
        r = await session.post("https://auth.riotgames.com/api/v1/authorization", json=body, headers=self._headers)
        
        cookies = {'cookie': {}}
        for cookie in r.cookies.items():
            cookies['cookie'][cookie[0]] = str(cookie).split('=')[1].split(';')[0]

        data = {"type": "auth", "username": username, "password": password, "remember": True}

        async with session.put('https://auth.riotgames.com/api/v1/authorization', json=data, headers=self._headers) as r:
            data = await r.json()
            for cookie in r.cookies.items():
                cookies['cookie'][cookie[0]] = str(cookie).split('=')[1].split(';')[0]
        
        await session.close()
        
        if data["type"] == "response":
            expiry_token = datetime.now() + timedelta(hours=1)
            response = _extract_tokens(data)
            access_token = response[0]
            token_id = response[1]
            expiry_token = datetime.now() + timedelta(minutes=59)
            cookies['expiry_token'] = int(datetime.timestamp(expiry_token))
            return {'auth': 'response', 'data': {'cookie': cookies, 'access_token': access_token, 'token_id': token_id}}
        elif data["type"] == "multifactor":
            label_modal = text['INTERFACE_VAL_2FA_LABEL']
            WaitFor2FA = {"auth": "2fa", "cookie": cookies, 'label': label_modal}
            if data['multifactor']['method'] == 'email':
                WaitFor2FA[
                    'message'
                ] = f"{text['INTERFACE_VAL_2FA_SENT']} {data['multifactor']['email']}"
                return WaitFor2FA
            WaitFor2FA['message'] = text['INTERFACE_VAL_2FA_ENABLED']
            return WaitFor2FA
    
    async def get_entitlements_token(self, access_token:str) -> Optional[str]:
        session = await self.create_session()
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {access_token}"}
        async with session.post("https://entitlements.auth.riotgames.com/api/token/v1", headers=headers, json={}
            ) as r:
            data = await r.json()
        await session.close()
        try:
            entitlements_token = data["entitlements_token"]
        except KeyError:
            logger.info(text['VAL_AUTH_COOKIE_EXPIRED'])
        else:
            return entitlements_token
    
    async def get_userinfo(self, access_token:str) -> Tuple[str, str, str]:
        session = await self.create_session()
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
        async with session.post("https://auth.riotgames.com/userinfo", headers=headers, json={}
            ) as r:
            data = await r.json()
        await session.close()
        try:
            puuid = data["sub"]
            name = data["acct"]["game_name"]
            tag = data["acct"]["tag_line"]
        except KeyError:
            logger.info(text['VAL_AUTH_NO_TAGLINE'])
        else:
            return puuid, name, tag
    
    async def get_region(self, access_token:str, token_id:str) -> str:
        session = await self.create_session()
        headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {access_token}'}
        body = {"id_token": token_id}
        async with session.put(
            "https://riot-geo.pas.si.riotgames.com/pas/v1/product/valorant", headers=headers, json=body
        ) as r:
            data = await r.json()
        await session.close()
        try:
            region = data["affinities"]["live"]
        except KeyError:
            logger.info(text['VAL_AUTH_X_ERROR'])
        else:
            return region
    
    async def give2facode(self, code:str, cookies:Dict) -> Dict[str, Any]:
        session = await self.create_session()
        data = {"type": "multifactor", "code": code, "rememberDevice": True}
        async with session.put("https://auth.riotgames.com/api/v1/authorization", headers=self._headers, json=data, cookies=cookies["cookie"]
        ) as r:
            data = await r.json()
        await session.close()
        if data["type"] == "response":
            cookies = {"cookie": {}}
            for cookie in r.cookies.items():
                cookies["cookie"][cookie[0]] = str(cookie).split("=")[1].split(";")[0]
            uri = data["response"]["parameters"]["uri"]
            access_token, token_id = _extract_tokens_from_uri(uri)
            return {"auth": "response", "data": {"cookie": cookies, "access_token": access_token, "token_id": token_id}}
        return {"auth": "failed", "error": "Invalid 2FA Code"}
    
    async def redeem_cookies(self, cookies:Dict) -> Tuple[Dict[str, Any], str, str]:
        if isinstance(cookies, str):
            cookies = json.loads(cookies)
        session = await self.create_session()
        if "cookie" in cookies:
            cookies = cookies["cookie"]
        async with session.get(
            "https://auth.riotgames.com/authorize?redirect_uri=https%3A%2F%2Fplayvalorant.com%2Fopt_in&client_id=play"
            "-valorant-web-prod&response_type=token%20id_token&scope=account%20openid&nonce=1",
            cookies=cookies, allow_redirects=False,
        ) as r:
            data = await r.text()
        if r.status != 303:
            logger.error("Expired cookies")
        if r.headers["Location"].startswith("/login"):
            logger.error("Expired cookies")
        old_cookie = cookies.copy()
        new_cookies = {"cookie": old_cookie}
        for cookie in r.cookies.items():
            new_cookies["cookie"][cookie[0]] = str(cookie).split("=")[1].split(";")[0]
        await session.close()
        accessToken, tokenId = _extract_tokens_from_uri(data)
        entitlements_token = await self.get_entitlements_token(accessToken)
        return new_cookies, accessToken, entitlements_token
    
    async def temp_auth(self, username:str, password:str) -> Optional[Dict[str, Any]]:
        authenticate = await self.authenticate(username, password)
        if authenticate["auth"] == "response":
            access_token = authenticate["data"]["access_token"]
            token_id = authenticate["data"]["token_id"]
            entitlements_token = await self.get_entitlements_token(access_token)
            puuid, name, tag = await self.get_userinfo(access_token)
            region = await self.get_region(access_token, token_id)
            player_name = f'{name}#{tag}' if tag is not None and tag is not None else 'no_username'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {access_token}',
                'X-Riot-Entitlements-JWT': entitlements_token,}
            user_data = {'puuid': puuid, 'region': region, 'headers': headers, 'player_name': player_name}
            return user_data
        logger.info(text['VAL_AUTH_NOT_SUPPORTED'])
    
    async def login_with_cookie(self, cookies:Dict) -> Dict[str, Any]:
        cookie_payload = f"ssid={cookies};" if cookies.startswith("e") else cookies
        session = await self.create_session()
        self._headers["cookie"] = cookie_payload
        r = await session.get(
            "https://auth.riotgames.com/authorize"
            "?redirect_uri=https%3A%2F%2Fplayvalorant.com%2Fopt_in"
            "&client_id=play-valorant-web-prod"
            "&response_type=token%20id_token"
            "&scope=account%20openid"
            "&nonce=1",
            allow_redirects=False,
            headers=self._headers,)
        self._headers.pop("cookie")
        if r.status != 303:
            logger.error(text['VAL_AUTH_COOKIE_FAILED'])
        await session.close()
        new_cookies = {'cookie': {}}
        for cookie in r.cookies.items():
            new_cookies['cookie'][cookie[0]] = str(cookie).split('=')[1].split(';')[0]
        accessToken, tokenID = _extract_tokens_from_uri(await r.text())
        entitlements_token = await self.get_entitlements_token(accessToken)
        data = {'cookies': new_cookies, 'AccessToken': accessToken, 'token_id': tokenID, 'emt': entitlements_token}
        return data
    
    async def refresh_token(self, cookies:Dict) -> Tuple[Dict[str, Any], str, str]:
        return await self.redeem_cookies(cookies)