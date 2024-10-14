"""
Заполняем таблицу пользователей;
Создаём таймеры для оповещений;
Формируем сообщения и передаём на рассылку;
"""

# TODO:
# 1) Степени поста

import asyncio
from ms import MS_producer
from db import DB_handler
from tg import TG_Sender
from utils import DB_MS_NAME, DB_US_NAME, schedule_in
from tokens import TG_TOKEN


def main():
    # loop = asyncio.get_event_loop()
    loop = None
    db = DB_handler(DB_MS_NAME, DB_US_NAME)
    ms = MS_producer(db)
    tg = TG_Sender(TG_TOKEN, db, ms, loop)
    # Запланировать обновление календаря
    # Запланировать рассылки
    # for user in db.get_users():
    #     if user['mailing']:
    #         print(user)
    #         loop.create_task(schedule_in(60,
    #                 tg.scheduled_evening_message(user)))
    # Запустить ботов
    asyncio.run(tg.poll())
    # loop.run_forever()

if __name__ == "__main__":
    main()