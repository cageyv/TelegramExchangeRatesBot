# Telegram ExchangeRatesBot

[![CI](https://github.com/llybin/TelegramExchangeRatesBot/workflows/tests/badge.svg)](https://github.com/llybin/TelegramExchangeRatesBot/actions)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/ddb58369590944a69a53737837c8dd3b)](https://www.codacy.com/app/llybin/TelegramExchangeRatesBot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=llybin/TelegramExchangeRatesBot&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://api.codacy.com/project/badge/Coverage/ddb58369590944a69a53737837c8dd3b)](https://www.codacy.com/app/llybin/TelegramExchangeRatesBot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=llybin/TelegramExchangeRatesBot&amp;utm_campaign=Badge_Coverage)
[![GPLv3](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Telegram bot actual exchange rates for travel, work and daily life.

Online since 01 July 2015.

[https://telegram.me/ExchangeRatesBot]()

## Translations

Don't have your localization? Any translation errors? Help fix it.

👉 [PoEditor.com](https://poeditor.com/join/project/LLu8AztSPb)

## How to run

`cp .env.default .env`

Configure your .env:

BOT_TOKEN - set up

`docker-compose up`

## Development

### See manage commands

`docker-compose run service ./manage.py`

### How to run tests

`docker-compose run service ./manage.py test`
