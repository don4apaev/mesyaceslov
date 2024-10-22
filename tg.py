
from telebot.async_telebot import AsyncTeleBot
import asyncio

class TG_Sender:
    def __init__(self, token, db_handler, ms_producer):
        self._bot = AsyncTeleBot(token)
        self._db_handler = db_handler
        self._ms_producer = ms_producer

        @self._bot.message_handler(commands=['help', 'start'])
        async def send_welcome(message):
            self._db_handler.add_user(message.from_user.id)
            text = "Привет. Я бот Месяцеслова.\nТы можешь узнать у меня, что говорит"\
            " Месяцеслов о сегодняшнем дне (/today) и дне грядущем (/tomorrow). "\
            "Удачи тебе сегодня, завтра и всегда!"
            await self._bot.send_message(message.from_user.id, text)

        @self._bot.message_handler(commands=['today'])
        async def send_welcome(message):
            user = self._db_handler.get_user_info(message.from_user.id)
            text = self._ms_producer.make_today(user)
            await self._bot.send_message(message.from_user.id, text)

        @self._bot.message_handler(commands=['tomorrow'])
        async def send_welcome(message):
            user = self._db_handler.get_user_info(message.from_user.id)
            text = self._ms_producer.make_tomorrow(user)
            await self._bot.send_message(message.from_user.id, text)

        @self._bot.message_handler()
        async def send_welcome(message):
            text = "Извини, я пока могу реагировать только на 2 команды: /today и /tomorrow"
            await self._bot.reply_to(message, text)

    def poll(self):
        return self._bot.polling()