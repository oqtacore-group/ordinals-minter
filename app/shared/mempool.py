import time
from functools import lru_cache

import requests


def get_ttl_hash(seconds=60):
    """Return the same value withing `seconds` time period."""
    return round(time.time() / seconds)


@lru_cache(maxsize=10)
def _get_fee_rates(ticker: str, ttl_cache=None):
    try:
        r = requests.get(
            'https://mempool.space/api/v1/fees/recommended',
            timeout=2,
        )
        fee_rates = r.json()
    except:
        fee_rates = {
            "fastestFee": 18,
            "halfHourFee": 11,
            "hourFee": 7,
            "economyFee": 2,
            "minimumFee": 1,
        }

    return fee_rates


def get_fee_rates() -> dict:
    """Return recomended fee rates from mempool.space or get new every min."""
    return _get_fee_rates(get_ttl_hash())
