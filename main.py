# TODO
# Обновление + 4 дня вне года
# Пост на стену
# Кэш в ms.py
# Поиск именин
# подробная информация о святом

import asyncio, signal, logging, os, sys
from datetime import datetime, timezone

from ms import MS_producer
from db import Days_DB_handler, User_DB_handler
from tg import TG_Sender
from vk import VK_Sender
from utils import InitError, Days, BotType

DB_MS_FILE_NAME     = 'mesyaceslov.db'
DB_USER_FILE_NAME   = 'users.db'
LOG_FILE_NAME       = 'log'
TG_TOKEN_ENV_NAME   = 'TG_MS_TOKEN'
VK_TOKEN_ENV_NAME   = 'VK_MS_TOKEN'

async def check_mailing(users_db: User_DB_handler, bot_handlers: tuple):
    cur_hour = datetime.now(timezone.utc).hour
    while True:
        await asyncio.sleep(1)
        new_hour = datetime.now(timezone.utc).hour
        if new_hour != cur_hour:
            cur_hour = new_hour
            for bot in bot_handlers:
                # Рассылка на сегодня для ТГ
                users = await users_db.get_today_mailing_users(bot.db_type, cur_hour)
                await asyncio.gather(bot.slovo_send_by_mailing(users, Days.TODAY))
                # Рассылка на завтра для ТГ
                users = await users_db.get_tomorrow_mailing_users(bot.db_type, cur_hour)
                await asyncio.gather(bot.slovo_send_by_mailing(users, Days.TOMMOROW))

async def main(verbose: bool = False):
    # Проверить входщие данные
    if ( tg_token := os.environ.get(TG_TOKEN_ENV_NAME) ) is None:
        raise(InitError(f'Need "{TG_TOKEN_ENV_NAME}" variable with Telegram bot token'))
    if ( vk_token := os.environ.get(VK_TOKEN_ENV_NAME) ) is None:
        raise(InitError(f'Need "{VK_TOKEN_ENV_NAME}" variable with VK bot token'))
    # отключить лишний вывод aiosqlite и vkbottle
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("vkbottle").setLevel(logging.WARNING)
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
    # Запустить систему
    logger.debug('Start Mesyaceslov bot')
    d_db = Days_DB_handler(db_name=DB_MS_FILE_NAME, logger=logger)
    u_db = User_DB_handler(db_name=DB_USER_FILE_NAME, logger=logger)
    async with d_db, u_db:
        ms = MS_producer(db_handler=d_db, logger=logger)
        tg = TG_Sender(token=tg_token, db_handler=u_db, ms_producer=ms, logger=logger)
        vk = VK_Sender(token=vk_token, db_handler=u_db, ms_producer=ms, logger=logger)
        a_list = [
            tg.poll(),
            vk.poll(),
            check_mailing(u_db, (tg, vk))
        ]
        # Запустить ботов
        try:
            await asyncio.gather(*a_list)
        except (KeyboardInterrupt, SystemExit, asyncio.exceptions.CancelledError):
            pass
    logger.debug('Stop Mesyaceslov bot')

if __name__ == "__main__":

    asyncio.run(main())
