import httpx, base64

from functools import lru_cache
from time import sleep
from lxml import etree

from ncatbot.core import BotAPI ,Image
from ncatbot.utils import get_log

from .cache import Cache

_log = get_log(__name__)

def get_top50_id() -> list[str]:
    res = httpx.request(url="https://pixiv.mokeyjay.com", method="get")
    if res.status_code != 200:
        return []
    html = etree.HTML(res.text)
    urls: list[str] = html.xpath("//a/@href")
    ids = [url.split("/")[-1] 
            for url in urls 
                if url.startswith("https://www.pixiv.net/artworks/")]
    return ids

img_ceche = Cache(max_size=1024)
def get_image(url: str, count: int = 0) -> dict | None:
    ret = img_ceche.get(url)
    ret = None
    if ret != None:
        return ret
    try:
        res = httpx.get(url)
    except httpx.ReadTimeout:
        return
    except Exception as e:
        _log.warning(f"get_image error: {e}")
        return get_image(url, count+1)
    if res.status_code != 200:
        _log.warning(f"Http Code: {res.status_code}")
        return
    ret = Image(f"base64://{base64.b64encode(res.content).decode('utf-8')}")
    img_ceche.update(url, ret)
    if res.status_code != 200:
        return
    ret = Image(f"base64://{base64.b64encode(res.content).decode('utf-8')}")
    img_ceche.update(url, ret)
    return ret