# Telegram ExchangeRatesBot

[![Build Status](https://travis-ci.com/llybin/TelegramExchangeRatesBot.svg?branch=master)](https://travis-ci.com/llybin/TelegramExchangeRatesBot)
[![GPLv3](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

Telegram bot actual exchange rates for travel, work and daily life.

Online from 01 July 2015.

https://telegram.me/ExchangeRatesBot

**In the process of refactoring. This repository is not in production.**

# Translations

Don't have your localization? Any translation errors? Help fix it.

👉 [PoEditor.com](https://poeditor.com/join/project/LLu8AztSPb)

# How to run

`cp .env.default .env`

Configure your .env:

BOT_TOKEN - set up

`docker-compose up`

# Development

## See manage commands

`docker-compose run service ./manage.py`

## How to run tests

`docker-compose run service ./manage.py test`
