
from telebot.async_telebot import AsyncTeleBot

class TG_Sender:
    def __init__(self, token, db_handler,
                    get_today_slovo, get_tomorrow_slovo):
        self.bot = AsyncTeleBot(token)
        self.db_handler = db_handler
        self.get_today_slovo = get_today_slovo
        self.get_tomorrow_slovo = get_tomorrow_slovo

        @self.bot.message_handler(commands=['help', 'start'])
        async def send_welcome(message):
            self.db_handler.add_user(message.from_user.id)
            text = "Привет. Я бот Месяцеслова.\nТы можешь узнать у меня, что говорит"\
            " Месяцеслов о сегодняшнем дне (/today) и дне грядущем (/tomorrow). "\
            "Удачи тебе сегодня, завтра и всегда!"
            await self.bot.reply_to(message, text)

        @self.bot.message_handler(commands=['today'])
        async def send_welcome(message):
            user = self.db_handler.get_user_info(message.from_user.id)
            text = self.get_today_slovo(user, db_handler)
            await self.bot.reply_to(message, text)

        @self.bot.message_handler(commands=['tomorrow'])
        async def send_welcome(message):
            user = self.db_handler.get_user_info(message.from_user.id)
            text = self.get_tomorrow_slovo(user, db_handler)
            await self.bot.reply_to(message, text)

        @self.bot.message_handler()
        async def send_welcome(message):
            text = "Извини, я пока могу реагировать только на 2 команды: /today и /tomorrow"
            await self.bot.reply_to(message, text)

    def poll(self):
        return self.bot.polling()