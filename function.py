import random
from urllib.parse import urlparse, urlunparse
import asyncio
import aiohttp
import wbi
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def get_bilibili_cookies(SESSDATA=None):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://www.bilibili.com', headers=headers) as response:
                response.raise_for_status()
                cookies = response.cookies
                if SESSDATA is not None:
                    cookies['SESSDATA'] = SESSDATA
                return cookies
        except aiohttp.ClientError as err:
            logger.error(f"HTTP error occurred: {err}")
        except Exception as err:
            logger.error(f"An error occurred: {err}")

async def MyRequest(APIurl, params, cookies):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
        'Accept': 'application/json',
    }
    async with aiohttp.ClientSession(cookies=cookies) as session:
        try:
            async with session.get(APIurl, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except aiohttp.ClientError as err:
            logger.error(f"HTTP error occurred: {err}")
            return None
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return None

async def checkLoginStatus(cookies):
    APIurl = 'https://api.bilibili.com/x/web-interface/nav'
    params = {}
    return await MyRequest(APIurl, params, cookies)

def getSessionData():
    try:
        with open('data.json', 'r') as f:
            data = json.load(f)
            return data.get('SESSDATA')
    except:
        return None

async def Search(keyword, page=1):
    cookies = await get_bilibili_cookies(getSessionData())
    APIurl = 'https://api.bilibili.com/x/web-interface/wbi/search/all/v2'
    params = {
        'keyword': keyword,
        'page': page,
    }
    return await MyRequest(APIurl, params, cookies)

async def getCid(BV, cookies):
    APIurl = 'https://api.bilibili.com/x/player/pagelist'
    params = {
        'bvid': BV,
    }
    return await MyRequest(APIurl, params, cookies)

def CalOR(a, b):  # OR运算 二进制属性位
    return a | b

async def getVideoInfo(BV, CID, cookies):
    APIurl = 'https://api.bilibili.com/x/player/playurl'
    params = {
        'bvid': BV,
        'cid': CID,
        'qn': 120,
        'otype': 'json',
        'platform': 'html5',
        'high_quality': 1,
        'fnval': CalOR(1, 128),
        'fourk': 1
    }
    return await MyRequest(APIurl, params, cookies)

async def BiliAnalysis(BV, p=1):
    cookies = await get_bilibili_cookies(getSessionData())
    CID = await getCid(BV, cookies)
    p -= 1
    if p < 0 or p >= len(CID['data']):
        p = 0
    VideoInfo = await getVideoInfo(BV, CID['data'][p]['cid'], cookies)
    Video = {
        'BV': BV,
        'page': p + 1,
        'url': VideoInfo['data']['durl'][0]['url'],
    }
    return Video

def ChangeBiliCDN(url):
    BiliCDN = [
        "upos-sz-mirrorcos.bilivideo.com",
        "upos-sz-mirrorali.bilivideo.com",
        "upos-sz-mirror08c.bilivideo.com",
    ]
    parsed_url = urlparse(url)
    new_netloc = random.choice(BiliCDN)
    new_url = urlunparse(parsed_url._replace(netloc=new_netloc))
    return new_url

async def room_play_info(room_id: int, sessdata: str = None):
    APIurl = 'https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo'
    params = {
        'room_id': str(room_id),
        'protocol': '0,1',
        'format': '1',
        'codec': '0,1',
        'platform': 'h5'
    }
    cookies = await get_bilibili_cookies(sessdata)
    return await MyRequest(APIurl, params, cookies)

async def room_play_url(room_id: int, sessdata: str = None):
    body = await room_play_info(room_id, sessdata)
    c = body.get('data', {}).get('playurl_info', {}).get('playurl', {}).get('stream', [{}])[0].get('format', [{}])[0].get('codec', [{}])[0]
    if not c:
        return ''
    return f"{c['url_info'][0]['host']}{c['base_url']}{c['url_info'][0]['extra']}"