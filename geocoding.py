import logging
import math
import time
from collections import OrderedDict

import requests

logger = logging.getLogger(__name__)

_last_lookup = 0

# Kleine in-memory cache van geslaagde lookups: dezelfde straat komt vaker
# voor, en bekende locaties blijven zo ook tijdens een Nominatim-storing
# verrijkbaar. Begrensd zodat het geheugengebruik niet groeit.
_cache: OrderedDict[str, dict] = OrderedDict()
_CACHE_MAX = 256


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371
    p1 = math.radians(float(lat1))
    p2 = math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lon2) - float(lon1))

    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 2)


def _cache_key(query: str) -> str:
    return " ".join(query.lower().split())


def geocode(query, user_agent):
    global _last_lookup

    key = _cache_key(query)
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]

    # Nominatim: max ±1 request/sec
    wait = 1.1 - (time.time() - _last_lookup)
    if wait > 0:
        time.sleep(wait)

    _last_lookup = time.time()

    res = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "nl",
        },
        headers={"User-Agent": user_agent},
        timeout=10,
    )

    res.raise_for_status()
    data = res.json()

    if not data:
        return None

    result = {
        "lat": float(data[0]["lat"]),
        "lon": float(data[0]["lon"]),
        "display_name": data[0].get("display_name"),
    }

    _cache[key] = result
    while len(_cache) > _CACHE_MAX:
        _cache.popitem(last=False)

    return result
