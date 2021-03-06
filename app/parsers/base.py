from abc import ABC, abstractmethod
from decimal import Decimal
from typing import NamedTuple

from app.translations import transform_locale


class DirectionWriting(object):
    UNKNOWN = None
    LEFT2RIGHT = "LEFT2RIGHT"
    RIGHT2LEFT = "RIGHT2LEFT"


class PriceRequest(NamedTuple):
    amount: Decimal or None
    currency: str
    to_currency: str or None
    parser_name: str
    direction_writing: DirectionWriting = DirectionWriting.UNKNOWN


class Parser(ABC):
    text: str
    chat_id: int
    default_currency: str
    default_currency_position: bool
    locale: str

    def __init__(
        self,
        text: str,
        chat_id: int,
        locale: str,
        default_currency: str,
        default_currency_position: bool,
    ):
        self.text = text
        self.chat_id = chat_id
        self.default_currency = default_currency
        self.default_currency_position = default_currency_position
        self.locale = transform_locale(locale)

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def parse(self) -> PriceRequest:
        pass
