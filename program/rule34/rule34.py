import requests
import random
import urllib.parse as urlparse
from bs4 import BeautifulSoup
from urllib.parse import parse_qs

from program.rule34.api_urls import API_URLS, __base_url__
from program.rule34.__vars__ import __headers__, __version__
from program.rule34.post import Post
from program.rule34.post_comment import PostComment
from program.rule34.icame import ICame
from program.rule34.stats import Stat
from program.rule34.toptag import TopTag

class Stats:
    def __get_top(self, name):
        retList = []
        response = requests.get(API_URLS.STATS.value, headers=__headers__)

        res_status = response.status_code
        res_len = len(response.content)
        ret_topchart = []

        if res_status != 200 or res_len <= 0:
            return []

        bfs_raw = BeautifulSoup(response.content.decode("utf-8"), features="html.parser")
        tables = bfs_raw.select(".toptencont > table")

        for table in tables:
            title = table.select("thead > tr")[0].get_text(strip=True)

            if title == name:
                trs = table.find("tbody").find_all("tr")

                for tr in trs:
                    tds = tr.find_all("td")
                    # 1 = Place
                    # 2 = Count
                    # 3 = Username
                    retList.append(Stat(tds[0].get_text(strip=True), tds[1].get_text(strip=True), tds[2].get_text(strip=True)))
                    #print(f"{tds[0].get_text(strip=True)} - {tds[1].get_text(strip=True)} - {tds[2].get_text(strip=True)}")
        return retList

    def top_taggers(self):
        return self.__get_top("Top 10 taggers")

    def top_commenters(self):
        return self.__get_top("Top 10 commenters")

    def top_forum_posters(self):
        return self.__get_top("Top 10 forum posters")

    def top_image_posters(self):
        return self.__get_top("Top 10 image posters")

    def top_note_editors(self):
        return self.__get_top("Top 10 note editors")

    def top_favorites(self):
        return self.__get_top("Top 10 favoriters")

class rule34Api(Exception):
    def __init__(self):
        self.__isInit__ = False
        self.stats = Stats()

    def search(self, tags: list, page_id: int = None, limit: int = 1000, deleted: bool = False,ignore_max_limit: bool = False) -> list:
        # Check if "limit" is in between 1 and 1000
        if not ignore_max_limit and limit > 1000 or limit <= 0:
            raise Exception("invalid value for \"limit\"\n  value must be between 1 and 1000\n  see for more info:\n  https://github.com/b3yc0d3/rule34Py/blob/master/DOC/usage.md#search")
            return

        params = [
            ["TAGS", "+".join(tags)],
            ["LIMIT", str(limit)],
        ]
        url = API_URLS.SEARCH.value
        
        # Add "page_id"
        if page_id != None:
            url += f"&pid={{PAGE_ID}}"
            params.append(["PAGE_ID", str(page_id)])

        
        if deleted:
            raise Exception("To include deleted images is not Implemented yet!")
            #url += "&deleted=show"

        formatted_url = self._parseUrlParams(url, params)
        response = requests.get(formatted_url, headers=__headers__)
        
        res_status = response.status_code
        res_len = len(response.content)
        ret_posts = []

        # checking if status code is not 200
        # (it's useless currently, becouse rule34.xxx returns always 200 OK regardless of an error)
        # and checking if content lenths is 0 or smaller
        # (curetly the only way to check for a error response)
        if res_status != 200 or res_len <= 0:
            return ret_posts

        for post in response.json():
            ret_posts.append(Post.from_json(post))

        return ret_posts

    def get_comments(self, post_id: int) -> list:
        params = [["POST_ID", str(post_id)]]
        formatted_url = self._parseUrlParams(API_URLS.COMMENTS, params) # Replaceing placeholders
        response = requests.get(formatted_url, headers=__headers__)

        res_status = response.status_code
        res_len = len(response.content)
        ret_comments = []

        if res_status != 200 or res_len <= 0:
            return ret_comments

        bfs_raw = BeautifulSoup(response.content.decode("utf-8"), features="xml")
        res_xml = bfs_raw.comments.findAll('comment')

        # loop through all comments
        for comment in res_xml:
            attrs = dict(comment.attrs)
            ret_comments.append(PostComment(attrs["id"], attrs["creator_id"], attrs["body"], attrs["post_id"], attrs["created_at"]))

        return ret_comments


    def get_pool(self, pool_id: int, fast: bool = True) -> list:
        params = [["POOL_ID", str(pool_id)]]
        response = requests.get(self._parseUrlParams(API_URLS.POOL.value, params), headers=__headers__)

        res_status = response.status_code
        res_len = len(response.content)
        ret_posts = []

        if res_status != 200 or res_len <= 0:
            return ret_posts

        soup = BeautifulSoup(response.content.decode("utf-8"), features="html.parser")

        for div in soup.find_all("span", class_="thumb"):
            a = div.find("a")
            id = div["id"][1:]

            if fast == True:
                ret_posts.append(id)
            else:
                ret_posts.append(self.get_post(id))

        return ret_posts

    def get_post(self, post_id: int) -> Post:
        params = [["POST_ID", str(post_id)]]
        formatted_url = self._parseUrlParams(API_URLS.GET_POST.value, params)
        response = requests.get(formatted_url, headers=__headers__)

        res_status = response.status_code
        res_len = len(response.content)
        ret_posts = []

        if res_status != 200 or res_len <= 0:
            return ret_posts

        for post in response.json():
            ret_posts.append(Post.from_json(post))

        return ret_posts if len(ret_posts) > 1 else (ret_posts[0] if len(ret_posts) == 1 else ret_posts)

    def icame(self, limit: int = 100) -> list:
        response = requests.get(API_URLS.ICAME.value, headers=__headers__)

        res_status = response.status_code
        res_len = len(response.content)
        ret_topchart = []

        if res_status != 200 or res_len <= 0:
            return ret_topchart

        bfs_raw = BeautifulSoup(response.content.decode("utf-8"), features="html.parser")
        rows = bfs_raw.find("table", border=1).find("tbody").find_all("tr")

        for row in rows:
            if row == None:
                continue

            character_name = row.select('td > a', href=True)[0].get_text(strip=True)
            count = row.select('td')[1].get_text(strip=True)

            if len(ret_topchart) < limit:
                ret_topchart.append(ICame(character_name, count))

        return ret_topchart

    def random_post(self, tags: list = None):
        if tags != None:
            search_raw = self.search(tags, limit=1000)
            if search_raw == []:
                return []

            randnum = random.randint(0, len(search_raw)-1)

            while len(search_raw) <= 0:
                search_raw = self.search(tags)
            else:
                return search_raw[randnum]
        else:
            return self.get_post(self._random_post_id())

    def tagmap(self) -> list:
        response = requests.get(API_URLS.TOPMAP.value, headers=__headers__)

        res_status = response.status_code
        res_len = len(response.content)
        ret_topchart = []

        if res_status != 200 or res_len <= 0:
            return []

        bfs_raw = BeautifulSoup(response.content.decode("utf-8"), features="html.parser")
        rows = bfs_raw.find("table", class_="server-assigns").find_all("tr")

        rows.pop(0)
        rows.pop(0)

        retData = []

        for row in rows:
            tags = row.find_all("td")

            rank = tags[0].string[1:]
            tagname = tags[1].string
            percentage = tags[2].string[:-1]

            retData.append(TopTag(rank=rank, tagname=tagname, percentage=percentage))

        return retData


    def _random_post_id(self) -> str:
        res = requests.get(API_URLS.RANDOM_POST.value, headers=__headers__)
        parsed = urlparse.urlparse(res.url)
        return parse_qs(parsed.query)['id'][0]

    def _parseUrlParams(self, url: str, params: list) -> str:
        retURL = url
        for g in params:
            key = g[0]
            value = g[1]
            retURL = retURL.replace("{" + key + "}", value)
        return retURL

    @property
    def version(self) -> str:
        return __version__
