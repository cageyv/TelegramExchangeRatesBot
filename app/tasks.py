import logging
from datetime import datetime, timedelta

import transaction
from celery_once import QueueOnce
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm.exc import NoResultFound
from telegram import Bot

from app.celery import celery_app
from app.exchanges.base import PairData, reverse_pair_data
from app.helpers import fill_rate_open, import_app_module, rate_from_pair_data
from app.models import ChatRequests, Currency, Exchange, Rate, RequestsLog
from suite.conf import settings
from suite.database import Session


# @celery_app.task(base=QueueOnce, queue='exchanges')
@celery_app.task(queue="exchanges")
def exchange_updater(exchange_class: str) -> None:
    db_session = Session()

    exchange = import_app_module(exchange_class)()
    try:
        exchange_obj = db_session.query(Exchange).filter_by(name=exchange.name).one()
        if not exchange_obj.is_active:
            logging.info(f"Exchange: {exchange.name} is not active, skip.")
            return
    except NoResultFound:
        logging.error(f"Exchange: {exchange.name} is not configured, skip.")
        return

    logging.info(f"Exchange: {exchange.name} in process.")

    for pair in exchange.list_pairs:
        from_currency = (
            db_session.query(Currency)
            .filter_by(is_active=True, code=pair.from_currency)
            .scalar()
        )
        to_currency = (
            db_session.query(Currency)
            .filter_by(is_active=True, code=pair.to_currency)
            .scalar()
        )

        if not from_currency or not to_currency:
            logging.debug(
                f"Exchange: {exchange.name}, pair: {pair} is not active or not supported, skip."
            )
            continue

        def save_rate(the_pair_data: PairData) -> None:
            new_rate = rate_from_pair_data(the_pair_data, exchange_obj.id)

            current_rate = (
                db_session.query(Rate)
                .filter_by(
                    from_currency=new_rate.from_currency,
                    to_currency=new_rate.to_currency,
                    exchange_id=exchange_obj.id,
                )
                .first()
            )

            new_rate = fill_rate_open(new_rate, current_rate)

            if current_rate:
                new_rate.id = current_rate.id
                db_session.merge(new_rate)
            else:
                db_session.add(new_rate)

        pair_data = exchange.get_pair_info(pair)

        current_time = datetime.utcnow()
        week_ago = current_time - timedelta(days=7)
        if pair_data.last_trade_at < week_ago:
            logging.debug(
                "Rate expired exchange: %s, pair: %s-%s",
                exchange.name,
                pair.from_currency.code,
                pair.to_currency.code,
            )
            continue

        save_rate(pair_data)
        if not exchange.included_reversed_pairs:
            reversed_pair_data = reverse_pair_data(pair_data)
            save_rate(reversed_pair_data)

    try:
        transaction.commit()
    except (IntegrityError, OperationalError):
        logging.exception("Error to fill rate pair")
        transaction.abort()


@celery_app.task(base=QueueOnce, queue="exchanges", time_limit=60)
def delete_expired_rates() -> None:
    db_session = Session()
    current_time = datetime.utcnow()
    two_days_ago = current_time - timedelta(days=2)
    rates = db_session.query(Rate).filter(Rate.last_trade_at < two_days_ago)
    for r in rates:
        logging.warning(
            "Rate expired exchange: %s, pair: %s-%s",
            r.exchange.name,
            r.from_currency.code,
            r.to_currency.code,
        )

    rates.delete()

    try:
        transaction.commit()
    except (IntegrityError, OperationalError):
        logging.exception("Error delete expired")
        transaction.abort()


@celery_app.task(queue="low", time_limit=10)
def write_request_log(
    chat_id: int, msg: str, created_at: datetime, tag: str = ""
) -> None:
    if len(msg) > settings.MAX_LEN_MSG_REQUESTS_LOG:
        return

    db_session = Session()
    db_session.add(
        RequestsLog(chat_id=chat_id, message=msg, tag=tag, created_at=created_at)
    )
    transaction.commit()


@celery_app.task(queue="low", time_limit=60)
def send_feedback(chat_id: int, first_name: str, username: str, text: str) -> None:
    if not settings.DEVELOPER_BOT_TOKEN or not settings.DEVELOPER_USER_ID:
        logging.warning("Developer account is not configured")
        return

    text_to = f"{chat_id}, {first_name}, @{username}: {text}"
    bot = Bot(token=settings.DEVELOPER_BOT_TOKEN)
    bot.send_message(settings.DEVELOPER_USER_ID, text=text_to)


@celery_app.task(queue="update_chat_request", time_limit=5)
def update_chat_request(chat_id: int, from_currency: str, to_currency: str):
    db_session = Session()
    from_currency = db_session.query(Currency).filter_by(code=from_currency).one()
    to_currency = db_session.query(Currency).filter_by(code=to_currency).one()

    chat_request = (
        db_session.query(ChatRequests)
        .filter_by(
            chat_id=chat_id, from_currency=from_currency, to_currency=to_currency
        )
        .first()
    )

    if chat_request:
        chat_request.times = ChatRequests.times + 1

    else:
        chat_request = ChatRequests(
            chat_id=chat_id, from_currency=from_currency, to_currency=to_currency
        )
        db_session.add(chat_request)

    try:
        transaction.commit()
    except (IntegrityError, OperationalError):
        logging.exception("Error create chat_request, chat_request exists")
        transaction.abort()
