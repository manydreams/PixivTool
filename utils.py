import httpx, base64

from functools import lru_cache
from time import sleep
from lxml import etree

from ncatbot.core import Image
from ncatbot.utils import get_log

from .cache import Cache

_log = get_log(__name__)
img_ceche = Cache(max_size=1024)

async def get_top50_id() -> list[str]:
    try:
        res = await httpx.AsyncClient().get(url="https://pixiv.mokeyjay.com")
    except httpx.ReadTimeout:
        _log.warning("get_top50_id timeout")
        return []
    except Exception as e:
        _log.warning(f"get_top50_id error: {e}")
        return []  
    
    # check response status  
    if res.status_code != 200:
        return []
    
    # parse the response
    html = etree.HTML(res.text)
    urls: list[str] = html.xpath("//a/@href")
    
    # get the ids from parsed urls
    ids = [url.split("/")[-1] 
            for url in urls 
                if url.startswith("https://www.pixiv.net/artworks/")]
    return ids

async def get_image(url: str, retry: int = 0) -> dict | None:
    
    ret = img_ceche.get(url)
    
    if ret != None:
        _log.info(f"Cache hit: {url}")
        return ret
    if retry >= 5:
        _log.warning(f"get_image error: {url}, retrying {retry}")
        return None
    try:
        res = await httpx.AsyncClient().get(url, timeout=30)
    except httpx.ReadTimeout:
        _log.warning(f"get_image timeout: {url}, retrying {retry + 1}...")
        return await get_image(url, retry+1)
    except Exception as e:
        _log.warning(f"get_image failed: {url}, {e}, retrying {retry + 1}...")
        return await get_image(url, retry+1)
    if res.status_code != 200:
        _log.warning(f"Http Code: {res.status_code}")
        return
    ret = Image(f"base64://{base64.b64encode(res.content).decode('utf-8')}")
    img_ceche.update(url, ret)
    return ret