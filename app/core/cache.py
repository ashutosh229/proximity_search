import json
import logging
from collections.abc import Hashable
from typing import Any
import threading
import redis
from collections import OrderedDict

log = logging.getLogger(__name__)


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self._d: OrderedDict[Hashable, Any] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: Hashable):
        with self._lock:
            if key in self._d:
                self._d.move_to_end(key)
                self.hits += 1
                return self._d[key]
            self.misses += 1
            return None

    def put(self, key: Hashable, value: Any):
        if self.capacity <= 0:
            return
        with self._lock:
            self._d[key] = value
            self._d.move_to_end(key)
            while len(self._d) > self.capacity:
                self._d.popitem(last=False)

    def __len__(self):
        with self._lock:
            return len(self._d)


class RedisCache:
    def __init__(self, url: str, ttl: int = 3600):
        self._err = (redis.RedisError, ValueError)
        self.r = redis.Redis.from_url(
            url, socket_timeout=0.05, socket_connect_timeout=0.05
        )
        self.ttl = ttl

    def get(self, key: Hashable):
        try:
            v = self.r.get("ip:" + repr(key))
            return tuple(json.loads(v)) if v is not None else None
        except self._err as e:
            log.warning("redis get failed: %s", e)
            return None

    def put(self, key: Hashable, value: Any):
        try:
            self.r.setex("ip:" + repr(key), self.ttl, json.dumps(list(value)))
        except self._err as e:
            log.warning("redis put failed: %s", e)

    def __len__(self):
        return 0
