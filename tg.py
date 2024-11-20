
from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from utils import Days

class TG_Sender:
    def __init__(self, token, db_handler, ms_producer):
        self._bot = AsyncTeleBot(token)
        self._db_handler = db_handler
        self._ms_producer = ms_producer

        @self._bot.message_handler(commands=['help', 'start'])
        async def send_welcome(message):
            print("send_welcome")
            self._db_handler.add_user(message.chat.id)
            text = "Привет. Я бот Месяцеслова.\n\nТы можешь узнать у меня, что говорит"\
            " Месяцеслов о сегодняшнем дне (/today), дне вчерашнем (/yesterday) и "\
            "дне грядущем (/tomorrow).\n\nУдачи тебе сегодня, завтра и всегда!"
            await self._bot.send_message(message.chat.id, text)

        @self._bot.message_handler(commands=['today', 'tomorrow', 'yesterday'])
        async def reply_slovo_commands(message):
            keyboard = InlineKeyboardMarkup()
            button_sing = InlineKeyboardButton(text="Приметы", callback_data=f'sign_{message.text[1:]}')
            button_holy = InlineKeyboardButton(text="Поминаемые святые", callback_data=f'holy_{message.text[1:]}')
            keyboard.add(button_sing, button_holy)
            text = "Что бы ты хотел узнать?"
            await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data == 'sign_yesterday')
        async def send_today_sign(call):
            message = call.message
            user = self._db_handler.get_user_info(message.chat.id)
            text = self._ms_producer.make_sign(user, Days.YESTERDAY)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id,
                                                parse_mode='Markdown')
        
        @self._bot.callback_query_handler(func=lambda call: call.data == 'sign_today')
        async def send_today_sign(call):
            message = call.message
            user = self._db_handler.get_user_info(message.chat.id)
            text = self._ms_producer.make_sign(user, Days.TODAY)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id,
                                                parse_mode='Markdown')

        @self._bot.callback_query_handler(func=lambda call: call.data == 'sign_tomorrow')
        async def send_tomorrow_sign(call):
            message = call.message
            user = self._db_handler.get_user_info(message.chat.id)
            text = self._ms_producer.make_sign(user, Days.TOMMOROW)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id,
                                                parse_mode='Markdown')

        @self._bot.callback_query_handler(func=lambda call: call.data == 'holy_yesterday')
        async def send_today_holy(call):
            message = call.message
            user = self._db_handler.get_user_info(message.chat.id)
            text = self._ms_producer.make_holy(user, Days.YESTERDAY)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id)

        @self._bot.callback_query_handler(func=lambda call: call.data == 'holy_today')
        async def send_today_holy(call):
            message = call.message
            user = self._db_handler.get_user_info(message.chat.id)
            text = self._ms_producer.make_holy(user, Days.TODAY)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id)

        @self._bot.callback_query_handler(func=lambda call: call.data == 'holy_tomorrow')
        async def send_tomorrow_holy(call):
            message = call.message
            user = self._db_handler.get_user_info(message.chat.id)
            text = self._ms_producer.make_holy(user, Days.TOMMOROW)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id)

        @self._bot.message_handler()
        async def send_error(message):
            text = "Извини, я пока могу реагировать только на 2 команды: /today и /tomorrow"
            await self._bot.reply_to(message, text)

    def poll(self):
        return self._bot.polling()