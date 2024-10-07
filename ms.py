"""
Заполняем таблицу пользователей;
Создаём таймеры для оповещений;
Формируем сообщения и передаём на рассылку;
"""

# TODO:
# 1) Степени поста

#import sched
import asyncio
from slova import MS_producer
from db import DB_handler
from tg import TG_Sender
from utils import TG_TOKEN, DB_NAME

def main():
    db = DB_handler(DB_NAME)
    ms = MS_producer(db)
    tg = TG_Sender(TG_TOKEN, db, ms)
    # Запланировать обновление календаря
    # Запланировать рассылки
    # Запустить ботов
    asyncio.run(tg.poll())

if __name__ == "__main__":
    main()