import decimal
import time

from functools import lru_cache

import requests


def get_ttl_hash(seconds=3600):
    """Return the same value withing `seconds` time period."""
    return round(time.time() / seconds)


@lru_cache(maxsize=10)
def _get_binance_price(ticker: str, ttl_cache=None) -> decimal.Decimal:
    url = f'https://api.binance.com/api/v3/ticker/price?symbol={ticker}'
    r = requests.get(url)
    return decimal.Decimal(r.json()['price'])


def get_binance_price(ticker: str) -> decimal.Decimal:
    """Return cached price from binance or get new every hour."""
    return _get_binance_price(ticker, get_ttl_hash())


def sat_to_usd(sat_amount: decimal.Decimal) -> decimal.Decimal:
    btc_amount = decimal.Decimal(sat_amount) / decimal.Decimal('100000000')
    btc_usd_price = get_binance_price('BTCUSDT')
    usd_btc_price = decimal.Decimal('1') / btc_usd_price
    usd_amount = btc_amount / usd_btc_price
    return usd_amount


def usd_to_eth(usd_amount: decimal.Decimal) -> decimal.Decimal:
    eth_usd_price = get_binance_price('ETHUSDT')
    eth_amount = decimal.Decimal(usd_amount) / eth_usd_price
    return eth_amount


def eth_to_wei(eth_amount: decimal.Decimal) -> decimal.Decimal:
    wei_amount = decimal.Decimal(eth_amount) * decimal.Decimal('1000000000000000000')
    return wei_amount


if __name__ == '__main__':
    print(usd_to_eth(100))
    print(usd_to_eth(573))

    print()
    print(sat_to_usd(176709))
    print(sat_to_usd(10000))
    print(sat_to_usd(5000))

    print(sat_to_usd(100000))
    print(usd_to_eth(sat_to_usd(100000)))
    print(usd_to_eth(25))

