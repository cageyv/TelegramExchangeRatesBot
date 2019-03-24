import gettext
import logging
from functools import wraps

import transaction
from pyramid_sqlalchemy import Session
from sqlalchemy.exc import IntegrityError

from suite.conf import settings

from app import translations
from .helpers import convert_locale
from .models import Chat
from .tasks import update_chat


def register_update(func):
    # TODO: rewrite it, fast fixes after release
    def wrapper(bot, update, *args, **kwargs):
        if not update.effective_user:
            # bots
            return

        if update.effective_chat:
            # private chat id == user id
            # group chat
            chat_id = update.effective_chat.id
        else:
            # inline commands
            chat_id = update.effective_user.id

        if update.effective_user.language_code:
            language_code = update.effective_user.language_code
        else:
            # some users don't have locale
            language_code = settings.LANGUAGE_CODE

        if 'zh' in language_code:
            logging.info('ZH STAT: %s', language_code)

        if language_code not in translations and language_code[:2] not in translations:
            logging.info('NO TRANSLATIONS STAT: %s', language_code)

        db_session = Session()
        chat = db_session.query(Chat).filter_by(id=chat_id).first()

        if not chat:
            chat = Chat(
                id=chat_id,
                first_name=update.effective_user.first_name if chat_id > 0 else None,
                username=update.effective_user.username if chat_id > 0 else None,
                locale=convert_locale(language_code),
                is_console_mode=False if chat_id > 0 else True,
            )
            db_session.add(chat)
            try:
                transaction.commit()
                kwargs['chat_info'] = {
                    'chat_id': chat_id,
                    'created': True,
                    'locale': convert_locale(language_code),
                    'is_subscribed': True,
                    'is_console_mode': False if chat_id > 0 else True,
                    'default_currency': settings.DEFAULT_CURRENCY,
                    'default_currency_position': settings.DEFAULT_CURRENCY_POSITION,
                }
            except IntegrityError:
                logging.exception("Error create chat, chat exists")
                transaction.abort()
                chat = db_session.query(Chat).filter_by(id=chat_id).one()
                kwargs['chat_info'] = {
                    'chat_id': chat.id,
                    'created': False,
                    'locale': convert_locale(language_code),
                    'is_subscribed': chat.is_subscribed,
                    'is_console_mode': chat.is_console_mode,
                    'default_currency': chat.default_currency,
                    'default_currency_position': chat.default_currency_position,
                }
        else:
            update_chat.delay(
                chat_id=chat.id,
                first_name=chat.first_name,
                username=chat.username,
                locale=convert_locale(language_code))

            kwargs['chat_info'] = {
                'chat_id': chat.id,
                'created': False,
                'locale': convert_locale(language_code),
                'is_subscribed': chat.is_subscribed,
                'is_console_mode': chat.is_console_mode,
                'default_currency': chat.default_currency,
                'default_currency_position': chat.default_currency_position,
            }

        return func(bot, update, *args, **kwargs)

    return wrapper


def chat_language(func):
    @wraps(func)
    def wrapper(bot, update, *args, **kwargs):
        language_code = kwargs['chat_info']['locale']

        if language_code in translations:
            locale = language_code
            _ = translations[locale].gettext

        elif language_code[:2] in translations:
            locale = language_code[:2]
            _ = translations[locale].gettext

        else:
            _ = gettext.gettext

        kwargs['_'] = _

        return func(bot, update, *args, **kwargs)

    return wrapper
