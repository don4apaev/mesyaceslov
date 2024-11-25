"""
Заполняем таблицу пользователей;
Создаём таймеры для оповещений;
Формируем сообщения и передаём на рассылку;
"""

import asyncio
import logging
import os

from ms import MS_producer
from db import Days_DB_handler, User_DB_handler
from tg import TG_Sender
from utils import InitError

DB_MS_FILE_NAME     = 'mesyaceslov.db'
DB_USER_FILE_NAME   = 'users.db'
TG_TOKEN_ENV_NAME   =  'TG_MS_TOKEN'

async def main():
    if ( tg_token := os.environ.get(TG_TOKEN_ENV_NAME) ) is None:
        raise(InitError(f'Need "{TG_TOKEN_ENV_NAME}" variable with Telegram bot token'))
    log_format = '%(asctime)s %(filename)s:%(lineno)s %(levelname)s: %(message)s'
    logging.basicConfig(filename='log', format=log_format, level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    log = logging.getLogger("aiosqlite")
    log.setLevel(logging.WARNING)

    d_db = Days_DB_handler(db_name=DB_MS_FILE_NAME, logger=logger)
    u_db = User_DB_handler(db_name=DB_USER_FILE_NAME, logger=logger)
    async with d_db, u_db:
        ms = MS_producer(db_handler=d_db, logger=logger)
        tg = TG_Sender(token=tg_token, db_handler=u_db, ms_producer=ms, logger=logger)
        # Запустить ботов
        await tg.poll()

if __name__ == "__main__":
    asyncio.run(main())
