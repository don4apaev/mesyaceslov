from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from utils import Days

class TG_Sender:
    def __init__(self, token, db_handler, ms_producer, logger):
        self._bot = AsyncTeleBot(token)
        self._db_handler = db_handler
        self._ms_producer = ms_producer
        self._logger = logger

        @self._bot.message_handler(commands=['help', 'start'])
        async def send_welcome(message):
            if message.text == '/start':
                self._logger.info(f'New user {message.chat.id}')
                await self._db_handler.add_user(message.chat.id)
            text = "Привет. Я бот Месяцеслова.\n\nТы можешь узнать у меня, что говорит"\
            " Месяцеслов о сегодняшнем дне (/today), дне прошедшем (/yesterday) и "\
            "дне грядущем (/tomorrow).\n\nУдачи тебе сегодня, завтра и всегда!"
            await self._bot.send_message(message.chat.id, text)

        @self._bot.message_handler(commands=['today', 'tomorrow', 'yesterday'])
        async def reply_slovo_commands(message):
            # set answer inline keyboard
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_sing = InlineKeyboardButton(text="Приметы", callback_data=f'sign_{message.text[1:]}')
            button_holy = InlineKeyboardButton(text="Поминаемые святые", callback_data=f'holy_{message.text[1:]}')
            keyboard.add(button_sing, button_holy)
            # question info type
            text = "Что бы ты хотел узнать?"
            await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[0:5] in ('sign_', 'holy_'))
        async def send_slovo_by_request(call):
            message = call.message
            # get user's timezone info
            user = await self._db_handler.get_user_info(message.chat.id)
            if user is None:
                user = {'timezone':0}
            # set mesyaceslov day
            if call.data.endswith('yesterday'):
                day = Days.YESTERDAY
            elif call.data.endswith('today'):
                day = Days.TODAY
            elif call.data.endswith('tomorrow'):
                day = Days.TOMMOROW
            else:
                day = Days.ERROR
            # get info
            if call.data.startswith('sign'):
                text_func = self._ms_producer.make_sign
            elif call.data.startswith('holy'):
                text_func = self._ms_producer.make_holy
            else:
                text_func = self._ms_producer.make_sign
                day = Days.ERROR
            text = await text_func(user, day)
            parse = 'Markdown'
            # post info into question
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, parse_mode=parse)
            self._logger.debug(f'Send Slovo for request of user {message.chat.id}')

        @self._bot.message_handler()
        async def send_error(message):
            text = "Извини, я пока могу реагировать только на 3 команды: /yesterday, /today и /tomorrow"
            await self._bot.reply_to(message, text)

    def poll(self):
        return self._bot.polling()