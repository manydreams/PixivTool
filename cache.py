import datetime
import bisect

from typing import Any
from ncatbot.utils import get_log

_log = get_log(__name__)

class Cache:
    default_timeout = 60 * 60 * 24 * 7 # 1 week in seconds
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.cache_timeout: list[tuple[float, str]] = []
    
    def _is_timeout(self, key: Any) -> bool:
        """Check if the cache entry for the given key is timed out.

        Args:
            key (Any): The key to check in the cache.

        Returns:
            bool: True if the cache entry is timed out, False is not timeout.
        """
        return self.cache[key][1] < datetime.datetime.now().timestamp()

    def clear_timeout(self) -> int:
        now = datetime.datetime.now().timestamp()
        cnt = 0
        
        while len(self.cache_timeout) > 0 and self.cache_timeout[-1][0] < now:
            
            key = self.cache_timeout.pop()[1]
            del self.cache[key]
            cnt += 1
            
        return cnt
    
    def clear(self) -> None:
        self.cache.clear()
    
    def get(self, key: str) -> Any | None:
        if key not in self.cache.keys():
            return None
        if self._is_timeout(key):
            _log.debug(f"Cache entry for {key} is timed out.")
            self.remove(key, no_check=True)
            return None
        _log.debug(f"Cache hit: {key}")
        return self.cache[key][0]

    def update(self, key: str, value: Any,
               timeout: int = default_timeout) -> None:
        self.clear_timeout()
        now = datetime.datetime.now().timestamp()
        
        if key in self.cache.keys():
            self.cache_timeout.remove((self.cache[key][1], key))
            self.cache[key] = (value, now + timeout)
            bisect.insort(self.cache_timeout, (now + timeout, key),
                          key=lambda x: -x[0])
            while len(self.cache) > self.max_size:
                key = self.cache_timeout.pop()[1]
                del self.cache[key]
        else:
            self.cache[key] = (value, now + timeout)
            bisect.insort(self.cache_timeout, (now + timeout, key),
                          key=lambda x: -x[0])
            while len(self.cache) > self.max_size:
                key = self.cache_timeout.pop()[1]
                del self.cache[key]
        _log.debug(f"Cache updated: {key}")
          
    def remove(self, key: str, no_check: bool = False):
        if no_check or key in self.cache:
            self.cache_timeout.remove((self.cache[key][1], key))
            del self.cache[key]