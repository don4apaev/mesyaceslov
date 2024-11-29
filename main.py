# TODO
# Меню админа - статистика
# Обновление + 4 дня вне года
# Кэш в ms.py

import asyncio, signal, logging, os, sys
from datetime import datetime, timezone

from ms import MS_producer
from db import Days_DB_handler, User_DB_handler
from tg import TG_Sender
from utils import InitError, Days

DB_MS_FILE_NAME     = 'mesyaceslov.db'
DB_USER_FILE_NAME   = 'users.db'
LOG_FILE_NAME       = 'log'
TG_TOKEN_ENV_NAME   = 'TG_MS_TOKEN'

async def check_mailing(users_db, tg_handler):
    cur_hour = datetime.now(timezone.utc).hour
    while True:
        await asyncio.sleep(1)
        new_hour = datetime.now(timezone.utc).hour
        if new_hour != cur_hour:
            cur_hour = new_hour
            # Рассылка на сегодня
            users = await users_db.get_today_mailing_users(cur_hour)
            mailing_tasks = [
                tg_handler.slovo_send_by_mailing(user, Days.TODAY)
                for user in users
            ]
            await asyncio.gather(*mailing_tasks)
            # Рассылка на завтра
            users = await users_db.get_tomorrow_mailing_users(cur_hour)
            mailing_tasks = [
                tg_handler.slovo_send_by_mailing(user, Days.TOMMOROW)
                for user in users
            ]
            await asyncio.gather(*mailing_tasks)

async def main(verbose: bool = False):
    # Проверить входщие данные
    if ( tg_token := os.environ.get(TG_TOKEN_ENV_NAME) ) is None:
        raise(InitError(f'Need "{TG_TOKEN_ENV_NAME}" variable with Telegram bot token'))
    # Инициировать логгер
    log_formater = logging.Formatter('%(asctime)s %(filename)s:%(lineno)s %(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    fileHandler = logging.FileHandler(LOG_FILE_NAME)
    fileHandler.setFormatter(log_formater)
    logger.addHandler(fileHandler)
    if '-v' in sys.argv:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(log_formater)
        logger.addHandler(consoleHandler)
    # отключить лишний вывод aiosqlite
    log = logging.getLogger("aiosqlite")
    log.setLevel(logging.WARNING)
    # Запустить систему
    logger.debug('Start Mesyaceslov bot')
    d_db = Days_DB_handler(db_name=DB_MS_FILE_NAME, logger=logger)
    u_db = User_DB_handler(db_name=DB_USER_FILE_NAME, logger=logger)
    async with d_db, u_db:
        ms = MS_producer(db_handler=d_db, logger=logger)
        tg = TG_Sender(token=tg_token, db_handler=u_db, ms_producer=ms, logger=logger)
        # Запустить ботов
        try:
            await asyncio.gather(tg.poll(), check_mailing(u_db, tg))
        except (KeyboardInterrupt, SystemExit, asyncio.exceptions.CancelledError):
            pass
    logger.debug('Stop Mesyaceslov bot')

if __name__ == "__main__":
    asyncio.run(main())
