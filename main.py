"""
Заполняем таблицу пользователей;
Создаём таймеры для оповещений;
Формируем сообщения и передаём на рассылку;
"""

import asyncio
from ms import MS_producer
from db import Days_DB_handler, User_DB_handler
from tg import TG_Sender
from utils import DB_MS_NAME, DB_US_NAME
from tokens import TG_TOKEN

# TODO:
# - логи для статистики

async def main():
    d_db = Days_DB_handler(DB_MS_NAME)
    u_db = User_DB_handler(DB_US_NAME)
    async with d_db, u_db:
        ms = MS_producer(d_db)
        tg = TG_Sender(TG_TOKEN, u_db, ms)
    # Запустить ботов
        await tg.poll()

if __name__ == "__main__":
    asyncio.run(main())
