"""
Заполняем таблицу пользователей;
Создаём таймеры для оповещений;
Формируем сообщения и передаём на рассылку;
"""

import asyncio
from ms import MS_producer
from db import DB_handler
from tg import TG_Sender
from utils import DB_MS_NAME, DB_US_NAME, schedule_in
from tokens import TG_TOKEN


def main():
    db = DB_handler(DB_MS_NAME, DB_US_NAME)
    ms = MS_producer(db)
    tg = TG_Sender(TG_TOKEN, db, ms)
    # Запустить ботов
    asyncio.run(tg.poll())

if __name__ == "__main__":
    main()