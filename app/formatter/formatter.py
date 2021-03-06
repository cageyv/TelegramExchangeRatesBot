from decimal import ROUND_HALF_UP, Decimal
from random import choice, randrange

from babel.numbers import format_decimal, get_decimal_quantum, get_decimal_symbol

from app import constants
from app.converter.base import PriceRequestResult
from app.parsers.base import DirectionWriting
from app.translations import transform_locale
from suite.conf import settings


def clever_round(number: Decimal, ndigits: int) -> Decimal:
    """
    Round a number with dynamic precision with a last ndigits non-zero digits for small number
    """
    if number > 1:
        return number.quantize(get_decimal_quantum(ndigits))

    # split on integer and fraction parts
    str_number_parts = f"{number:f}".split(".")

    # if no fraction
    if len(str_number_parts) == 1:
        return number

    str_fraction = str_number_parts[1]

    precision = len(str_fraction) - len(str_fraction.lstrip("0")) + 1

    if precision > constants.decimal_scale:
        # very small
        return Decimal("0")

    elif constants.decimal_scale - precision < ndigits:
        precision += constants.decimal_scale - precision

    else:
        precision += ndigits - 1

    return number.quantize(get_decimal_quantum(precision), rounding=ROUND_HALF_UP)


class FormatPriceRequestResult(object):
    locale: str
    prr: PriceRequestResult

    def __init__(self, prr: PriceRequestResult, locale: str):
        self.prr = prr
        self.locale = transform_locale(locale)

    def is_rate_diff_available(self) -> bool:
        return bool(self.prr.rate and self.prr.rate_open)

    def is_high_low_available(self) -> bool:
        return bool(self.prr.low24h and self.prr.high24h)

    def _diff_rate(self) -> Decimal or None:
        assert self.is_rate_diff_available()

        return self.prr.rate - self.prr.rate_open

    def _percent_diff_rate(self) -> Decimal or None:
        assert self.is_rate_diff_available()

        return (self._diff_rate() / self.prr.rate_open) * Decimal("100")

    def _get_sign(self) -> str or None:
        assert self.is_rate_diff_available()

        # return nothing because if minus then amount already contain minus
        return "+" if self._diff_rate() > 0 else ""

    def _get_arrow(self) -> str:
        assert self.is_rate_diff_available()

        number = self._diff_rate()

        if number > 0:
            return constants.arrows["up"]
        elif number < 0:
            return constants.arrows["down"]
        else:
            return ""

    def is_convert_mode(self) -> bool:
        return self.prr.price_request.amount is not None

    def format_amount(self, number: Decimal, ndigits: int = 4) -> str:
        assert ndigits % 2 == 0

        rounded_number = clever_round(number, ndigits)
        formatted = format_decimal(
            rounded_number, locale=self.locale, decimal_quantization=False
        )
        return self.normalize_amount_str(formatted, ndigits)

    def normalize_amount_str(self, formatted: str, ndigits: int = 4):
        decimal_symbol = get_decimal_symbol(self.locale)
        str_number_parts = formatted.partition(decimal_symbol)
        if str_number_parts[2] == "":
            # 3,995 -> 3,995.0
            return f"{formatted}{decimal_symbol}0"
        elif len(str_number_parts[2]) <= 2:
            # 1.1 -> 1.1 ; 1.12 -> 1.12
            return formatted
        else:
            # 1.123 -> 1.1230 ; 1.0123 -> 1.0123 ; 0.00123 -> 0.00123 ; 1.001 -> 1.0010
            return formatted + "0" * (ndigits - len(str_number_parts[2]))

    def format_last_trade_at(self) -> str:
        if self.prr.last_trade_at.year == 1996:
            # Baba Vanga
            return f"_{self.prr.last_trade_at:%d %B %Y}_"
        else:
            return f"_{self.prr.last_trade_at:%d %B, %H:%M} UTC_"

    def format_exchanges(self) -> str:
        return f'{" 📡 ".join(self.prr.exchanges)} 📡'

    def format_difference(self) -> str:
        if not self.is_rate_diff_available():
            return ""

        diff = self.format_amount(self._diff_rate())
        percent = self.format_amount(self._percent_diff_rate(), 2)
        sign = self._get_sign()

        return f"{sign}{diff} ({sign}{percent}%)"

    def format_high_low(self) -> str:
        if not self.is_high_low_available():
            return ""

        low24h = self.format_amount(self.prr.low24h)
        high24h = self.format_amount(self.prr.high24h)

        return f"*Low*: {low24h} *High*: {high24h}"

    def format_price(self) -> str:
        assert not self.is_convert_mode()

        rate = self.format_amount(self.prr.rate)
        from_currency = self.prr.price_request.currency
        to_currency = self.prr.price_request.to_currency

        if self.is_rate_diff_available() and self._get_arrow():
            return f"*{from_currency} {to_currency}* {rate} {self._get_arrow()}"
        else:
            return f"*{from_currency} {to_currency}* {rate}"

    def format_amount_convert(self) -> str:
        assert self.is_convert_mode()

        from_amount = self.format_amount(self.prr.price_request.amount)
        result_amount = self.format_amount(
            self.prr.price_request.amount * self.prr.rate
        )
        from_currency = self.prr.price_request.currency
        to_currency = self.prr.price_request.to_currency

        if self.prr.price_request.direction_writing == DirectionWriting.RIGHT2LEFT:
            return f"{result_amount} *{to_currency}* = {from_amount} *{from_currency}*"
        else:
            return f"{from_amount} *{from_currency}* = {result_amount} *{to_currency}*"

    @staticmethod
    def format_donations(currency):
        return f"/donate{currency} {choice(constants.DONATION_EMOJIS)}"

    def get(self) -> str:
        msg_list = []

        if self.is_convert_mode():
            msg_list.append(self.format_amount_convert())

        else:
            msg_list.append(self.format_price())

            if self.is_rate_diff_available():
                msg_list.append(self.format_difference())

            if self.is_high_low_available():
                msg_list.append(self.format_high_low())

        msg_list.append(self.format_last_trade_at())
        msg_list.append(self.format_exchanges())

        if randrange(settings.DONATION_FREQUENCY) == 0:
            from_currency = self.prr.price_request.currency
            to_currency = self.prr.price_request.to_currency
            if from_currency in settings.DONATION_WALLETS:
                msg_list.append(self.format_donations(from_currency))
            elif to_currency in settings.DONATION_WALLETS:
                msg_list.append(self.format_donations(to_currency))

        return "\n".join(msg_list)


class InlineFormatPriceRequestResult(FormatPriceRequestResult):
    # FIXME: copy-paste
    def format_price(self) -> str:
        assert not self.is_convert_mode()

        rate = self.format_amount(self.prr.rate)
        from_currency = self.prr.price_request.currency
        to_currency = self.prr.price_request.to_currency

        if self.is_rate_diff_available() and self._get_arrow():
            return f"{from_currency} {to_currency} {rate} {self._get_arrow()}"
        else:
            return f"{from_currency} {to_currency} {rate}"

    def format_amount_convert(self) -> str:
        assert self.is_convert_mode()

        from_amount = self.format_amount(self.prr.price_request.amount)
        result_amount = self.format_amount(
            self.prr.price_request.amount * self.prr.rate
        )
        from_currency = self.prr.price_request.currency
        to_currency = self.prr.price_request.to_currency

        if self.prr.price_request.direction_writing == DirectionWriting.RIGHT2LEFT:
            return f"{result_amount} {to_currency} = {from_amount} {from_currency}"
        else:
            return f"{from_amount} {from_currency} = {result_amount} {to_currency}"

    def get(self) -> str:
        if self.is_convert_mode():
            return self.format_amount_convert()
        else:
            return self.format_price()


class NotifyFormatPriceRequestResult(FormatPriceRequestResult):
    # FIXME: copy-paste
    def format_price(self) -> str:
        assert not self.is_convert_mode()

        rate = self.format_amount(self.prr.rate)
        from_currency = self.prr.price_request.currency
        to_currency = self.prr.price_request.to_currency

        if self.is_rate_diff_available() and self._get_arrow():
            return f"*{from_currency} {to_currency}* {rate} {self._get_arrow()} 🔔"
        else:
            return f"*{from_currency} {to_currency}* {rate} 🔔"
