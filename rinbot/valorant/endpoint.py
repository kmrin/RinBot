import json
import urllib3
import requests

from typing import Mapping, Dict, Any

from rinbot.core.loggers import Loggers

from .resources import base_endpoint, base_endpoint_glz, base_endpoint_shared, region_shard_override, shard_region_override

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = Loggers.VALORANT

class API_ENDPOINT:
    def __init__(self) -> None:
        from .auth import Auth
        
        self.auth = Auth()
        self.client_platform = 'ew0KCSJwbGF0Zm9ybVR5cGUiOiAiUEMiLA0KCSJwbGF0Zm9ybU9TIjogIldpbmRvd3MiLA0KCSJwbGF0Zm9ybU9TVmVyc2lvbiI6ICIxMC4wLjE5MDQyLjEuMjU2LjY0Yml0IiwNCgkicGxhdGZvcm1DaGlwc2V0IjogIlVua25vd24iDQp9'
        self.locale_code = 'en-US'
    
    def activate(self, auth: Mapping[str, Any]) -> None:
        headers = self.__build_headers(auth["headers"])
        self.headers = headers
        self.puuid = auth['puuid']
        self.region = auth['region']
        self.player = auth['player_name']
        self.locale_code = auth.get('locale_code', 'en-US')
        self.__format_region()
        self.__build_urls()

    def fetch(self, endpoint: str = '\n', url: str = 'pd', errors: Dict = {}) -> Dict:
        endpoint_url = getattr(self, url)
        data = None
        r = requests.get(f'{endpoint_url}{endpoint}', headers=self.headers)
        
        try:
            data = json.loads(r.text)
        except:  # I know this is dumb but idc
            pass
        
        if 'httpStatus' not in data:
            return data
        
        if data['httpStatus'] == 400:
            logger.error('Cookies expired')
    
    def put(self, endpoint: str = '/', url: str = 'pd', data: Dict = {}, errors: Dict = {}) -> Dict:
        data = data if type(data) is list else json.dumps(data)
        endpoint_url = getattr(self, url)
        data = None
        
        r = requests.get(f'{endpoint_url}{endpoint}', headers=self.headers, data=data)
        data = json.loads(r.text)
        
        if data is not None:
            return data
        else:
            logger.error('Put request failed')
    
    def store_fetch_offers(self) -> Mapping[str, Any]:
        data = self.fetch('/store/v1/offers/', url='pd')
        return data

    def store_fetch_storefront(self) -> Mapping[str, Any]:
        data = self.fetch(f'/store/v2/storefront/{self.puuid}', url='pd')
        return data

    def store_fetch_wallet(self) -> Mapping[str, Any]:
        data = self.fetch(f'/store/v1/wallet/{self.puuid}', url='pd')
        return data

    def store_fetch_order(self, order_id: str) -> Mapping[str, Any]:
        data = self.fetch(f'/store/v1/order/{order_id}', url='pd')
        return data

    def store_fetch_entitlements(self, item_type: Mapping) -> Mapping[str, Any]:
        """
        List what the player owns (agents, skins, buddies, ect.)
        Correlate with the UUIDs in `fetch_content` to know what items are owned.
        Category names and IDs:

        `ITEMTYPEID:`
        '01bb38e1-da47-4e6a-9b3d-945fe4655707': 'Agents'\n
        'f85cb6f7-33e5-4dc8-b609-ec7212301948': 'Contracts',\n
        'd5f120f8-ff8c-4aac-92ea-f2b5acbe9475': 'Sprays',\n
        'dd3bf334-87f3-40bd-b043-682a57a8dc3a': 'Gun Buddies',\n
        '3f296c07-64c3-494c-923b-fe692a4fa1bd': 'Player Cards',\n
        'e7c63390-eda7-46e0-bb7a-a6abdacd2433': 'Skins',\n
        '3ad1b2b2-acdb-4524-852f-954a76ddae0a': 'Skins chroma',\n
        'de7caa6b-adf7-4588-bbd1-143831e786c6': 'Player titles',\n
        """
        
        data = self.fetch(
            endpoint=f'/store/v1/entitlements/{self.puuid}/{item_type}'
        )
        
        return data

    def __check_ppuid(self, puuid: str) -> str:
        return self.puuid if puuid is None else puuid
    
    def __build_urls(self) -> str:
        self.pd = base_endpoint.format(shard=self.shard)
        self.shared = base_endpoint_shared.format(shard=self.shard)
        self.glz = base_endpoint_glz.format(region=self.region, shard=self.shard)

    def __build_headers(self, headers: Mapping) -> Mapping[str, Any]:
        headers['X-Riot-ClientPlatform'] = self.client_platform
        headers['X-Riot-ClientVersion'] = self._get_client_version()
        return headers

    def __format_region(self) -> None:
        self.shard = self.region
        if self.region in region_shard_override.keys():
            self.shard = region_shard_override[self.region]
        if self.shard in shard_region_override.keys():
            self.region = shard_region_override[self.shard]
    
    def _get_client_version(self) -> str:
        r = requests.get('https://valorant-api.com/v1/version')
        data = r.json()['data']
        
        return f"{data['branch']}-shipping-{data['buildVersion']}-{data['version'].split('.')[3]}"
    
    def _get_valorant_version(self) -> str:
        r = requests.get('https://valorant-api.com/v1/version')
        if r.status != 200:
            return None
        data = r.json()['data']
        return data['version']
