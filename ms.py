"""
Заполняем таблицу пользователей;
Создаём таймеры для оповещений;
Формируем сообщения и передаём на рассылку;
"""

#import sched
import asyncio
from slova import make_today_slovo, make_tomorrow_slovo
from db import DB_handler
from tg import TG_Sender
from utils import TG_TOKEN, DB_NAME

def main():
    db = DB_handler(DB_NAME)
    tg = TG_Sender(TG_TOKEN, db,
            make_today_slovo, make_tomorrow_slovo)
    asyncio.run(tg.poll())

if __name__ == "__main__":
    main()