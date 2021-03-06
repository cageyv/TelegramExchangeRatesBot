from datetime import datetime
from decimal import Decimal, DecimalException
from typing import Tuple

import requests
from cached_property import cached_property
from jsonschema import ValidationError, validate
from ratelimit import limits, sleep_and_retry

from app.exchanges.base import ECurrency, Exchange, Pair, PairData
from app.exchanges.exceptions import APIErrorException, PairNotExistsException


class BitfinexExchange(Exchange):
    """
    https://docs.bitfinex.com

    If an IP address exceeds a certain number of requests per minute (between 10 and 90)
    to a specific REST API endpoint e.g., /ticker, the requesting IP address will be blocked
    for 10-60 seconds on that endpoint and the JSON response {"error": "ERR_RATE_LIMIT"} will be returned.
    """

    name = "Bitfinex"

    @cached_property
    def _get_pairs(self) -> tuple:
        try:
            response = requests.get("https://api.bitfinex.com/v1/symbols")
            response.raise_for_status()
            pairs = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            raise APIErrorException(e)

        try:
            schema = {"type": "array", "items": {"type": "string"}}
            validate(pairs, schema)
        except ValidationError as e:
            raise APIErrorException(e)

        return tuple(pairs)

    @cached_property
    def list_pairs(self) -> Tuple[Pair]:
        pairs = set()

        for x in self._get_pairs:
            x = x.upper()

            if ":" in x:
                from_currency, to_currency = x.split(":")
            else:
                from_currency, to_currency = x[:3], x[3:]

            pairs.add(Pair(ECurrency(from_currency), ECurrency(to_currency)))

        return tuple(pairs)

    @cached_property
    def list_currencies(self) -> Tuple[ECurrency]:
        currencies = set()

        for from_currency, to_currency in self.list_pairs:
            currencies.add(from_currency)
            currencies.add(to_currency)

        return tuple(currencies)

    @sleep_and_retry
    @limits(calls=1, period=5)
    def get_pair_info(self, pair: Pair) -> PairData:
        if not self.is_pair_exists(pair):
            raise PairNotExistsException(pair)

        request_pair = f"{pair.from_currency}{pair.to_currency}".lower()

        try:
            response = requests.get(
                f"https://api.bitfinex.com/v1/pubticker/{request_pair}"
            )
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            raise APIErrorException(e)

        try:
            schema = {
                "type": "object",
                "properties": {
                    "mid": {"type": "string"},
                    "low": {"type": "string"},
                    "high": {"type": "string"},
                    "timestamp": {"type": "string"},
                },
                "required": ["mid", "low", "high", "timestamp"],
            }
            validate(data, schema)
        except ValidationError as e:
            raise APIErrorException(e)

        try:
            rate = Decimal(data["mid"])
            low = Decimal(data["low"])
            high = Decimal(data["high"])
            last_trade_at = float(data["timestamp"])
        except (DecimalException, ValueError) as e:
            raise APIErrorException(e)

        return PairData(
            pair=pair,
            rate=rate,
            low24h=low,
            high24h=high,
            last_trade_at=datetime.fromtimestamp(last_trade_at),
        )
