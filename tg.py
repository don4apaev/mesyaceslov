from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

from utils import Days

Hours_ending = {
    1: '',
    2: 'а',
    3: 'а',
    4: 'а',
}

Error = 'Какая-то проблема с обновлением данных... Обратись к администратору или попробуй позже.'

class TG_Sender:
    def __init__(self, token, db_handler, ms_producer, logger):
        self._bot = AsyncTeleBot(token)
        self._db_handler = db_handler
        self._ms_producer = ms_producer
        self._logger = logger
        self._user_inreract = {}

        @self._bot.message_handler(commands=['help', 'start'])
        async def welcome_send(message):
            """
            Старт и подсказка
            """
            if message.text == '/start':
                self._logger.info(f'New user {message.chat.id}')
                await self._db_handler.add_user(message.chat.id)
            text = "Привет. Я бот Месяцеслова.\n\n"\
                "Ты можешь узнать у меня, что говорит Месяцеслов о сегодняшнем дне "\
                "(/today), дне прошедшем (/yesterday) и дне грядущем (/tomorrow).\n"\
                "Для определения даты по умолчанию используется временная зона МСК+0. "\
                "Ты всегда можешь изменить её командой /timezone.\n\n"\
                "Удачи тебе сегодня, завтра и всегда!"
            await self._bot.send_message(message.chat.id, text)

        @self._bot.message_handler(commands=['today', 'tomorrow', 'yesterday'])
        async def slovo_reply_commands(message):
            """
            Обработка команд /today, /tomorrow, /yesterday - показать кнопки
            """
            text = "Что бы ты хотел узнать?"
            # Назначаем кнопки
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_sing = InlineKeyboardButton(text="Приметы", callback_data=f'sign_{message.text[1:]}')
            button_holy = InlineKeyboardButton(text="Поминаемые святые", callback_data=f'holy_{message.text[1:]}')
            keyboard.add(button_sing, button_holy)
            await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[0:5] in ('sign_', 'holy_'))
        async def slovo_send_by_request(call):
            """
            Обработка команд /today, /tomorrow, /yesterday - результат нажатия кнопки
            """
            message = call.message
            # Получаем временную зону пользователя
            user = await self._db_handler.get_user_info(message.chat.id)
            if user is None or user['timezone'] is None:
                user = {'timezone':0}
            # Получаем запрашиваемый день
            if call.data.endswith('yesterday'):
                day = Days.YESTERDAY
            elif call.data.endswith('today'):
                day = Days.TODAY
            elif call.data.endswith('tomorrow'):
                day = Days.TOMMOROW
            else:
                day = Days.ERROR
            # Получаем Слово на день
            if call.data.startswith('sign'):
                text_func = self._ms_producer.make_sign
            elif call.data.startswith('holy'):
                text_func = self._ms_producer.make_holy
            else:
                text_func = self._ms_producer.make_sign
                day = Days.ERROR
            text = await text_func(user, day)
            parse = 'Markdown'
            # Отредактировать сообщение
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, parse_mode=parse)
            self._logger.debug(f'Send Slovo for request of user {message.chat.id}')

        @self._bot.message_handler(commands=['timezone'])
        async def mailing_start_edit(message):
            """
            Обработка команды /timezone - спросить, что делаем
            """
            keyboard = None
            if user := await self._db_handler.get_user_info(message.chat.id):
                text = self._make_timezone_info(user)
                text += '\nЧто мне сдалать?'
                keyboard = InlineKeyboardMarkup(row_width=1)
                button_list = []
                button_list.append(InlineKeyboardButton(text="Изменить",callback_data='timezone_change'))
                button_list.append(InlineKeyboardButton(text="Ничего",callback_data='editing_cancel'))
                keyboard.add(*button_list)
            else:
                text = Error
            await self._bot.send_message(message.chat.id, text,
                                        reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data == 'timezone_change')
        async def timezone_change_first(call):
            """
            Обработка команды /timezone - запросить часовой пояс
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += "\nПришли мне свой часовой пояс в целых часах относительно Москвы"
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_с = InlineKeyboardButton(text="Ничего",callback_data='editing_cancel')
            keyboard.add(button_с)
            # Запомнить пользователя
            self._user_inreract[message.chat.id] = {'type':1, 'msg':message.message_id}
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        # @self._bot.message_handler(commands=['mailing'])
        # async def mailing_start_edit(message):
        #     """
        #     Обработка команды /mailing - спросить, что делаем
        #     """
        #     keyboard = None
        #     if user := await self._db_handler.get_user_info(message.chat.id):
        #         text, button_list = self._make_mailing_info_and_buttons(user)
        #         text += '\nЧто мне сдалать?'
        #         keyboard = InlineKeyboardMarkup(row_width=1)
        #         button_list.append(InlineKeyboardButton(text="Ничего",callback_data='editing_cancel'))
        #         keyboard.add(*button_list)
        #     else:
        #         text = Error
        #     await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        # @self._bot.callback_query_handler(func=lambda call: call.data == 'mailing_on')
        # async def mailing_on_first(call):
        #     """
        #     Обработка команды /mailing - включить и запросить дальнейшие действия
        #     """
        #     message = call.message
        #     keyboard = None
        #     if await self._db_handler.set_user_mailing(message.chat.id, True):
        #         user = await self._db_handler.get_user_info(message.chat.id)
        #         text, button_list = self._make_mailing_info_and_buttons(user)
        #         text += '\nЧто дальше?'
        #         keyboard = InlineKeyboardMarkup(row_width=1)
        #         button_list.append(InlineKeyboardButton(text="Ничего",callback_data='editing_cancel'))
        #         keyboard.add(*button_list)
        #     else:
        #         text = Error
        #     await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        # @self._bot.callback_query_handler(func=lambda call: call.data == 'mailing_off')
        # async def mailing_off(call):
        #     """
        #     Обработка команды /mailing - отключить рассылку
        #     """
        #     message = call.message
        #     if await self._db_handler.set_user_mailing(message.chat.id, False):
        #         user = await self._db_handler.get_user_info(message.chat.id)
        #         text, _ = self._make_mailing_info_and_buttons(user)
        #     else:
        #         text = Error
        #     await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id)

        @self._bot.callback_query_handler(func=lambda call: call.data == 'editing_cancel')
        async def editing_cancel_edit(call):
            """
            Обработка команды /mailing и /timezone - ничего не менять
            """
            message = call.message
            try:
                self._user_inreract.pop(message.chat.id)
            except KeyError:
                pass
            # Отредактировать сообщение - удалить часть с вопросом и кнопки
            text = message.text[:message.text.rindex('\n')]
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id)

        @self._bot.message_handler()
        async def over_send(message):
            """
            Обрабка всего прочего:
            - Проверка на команду /timezone - записать часовой пояс;
            - Все остальные случаи
            """
            # Проверка на команду
            if type(self._user_inreract.get(message.chat.id)) is dict:
                # Проверка на команду /timezone - записать часовой пояс
                if self._user_inreract[message.chat.id]['type'] == 1:
                    # Распознать число со знаком и проврить вхождение в интервал
                    tz_num = self._parse_tz(message.text)
                    if tz_num is not None:
                        # Убрать кнопку отмены и очистить хранилище
                        await self._bot.edit_message_reply_markup(message.chat.id,
                                        self._user_inreract[message.chat.id]['msg'], None)
                        self._user_inreract.pop(message.chat.id)
                        # Привести ВЗ к UTC bp МСК и записать результаты в БД
                        timezone = tz_numb + 3
                        if await self._db_handler.set_user_timezone(message.chat.id, timezone):
                            user = await self._db_handler.get_user_info(message.chat.id)
                            text = self._make_timezone_info(user)
                        else:
                            text = Error
                        await self._bot.send_message(message.chat.id, text)
                    else:
                        text = "Часовой пояс должен быть челочисленным и в пределах от -12 до +12"
                        await self._bot.send_message(message.chat.id, text)
            # Все остальные случаи
            else:
                text = "Извини, я пока могу реагировать только на определённые команды. "\
                "Посмотри их в Меню."
                await self._bot.reply_to(message, text)

    def poll(self):
        return self._bot.polling()

    def _make_mailing_info_and_buttons(self, user: dict) -> tuple:
        button_list = []
        text = ""
        # Получаем статус и генерируем соответствующие кнопки
        if user['mailing'] != 1:
            text += "Рассылка отключена.\n"
            button_list.append(InlineKeyboardButton(text="Включить", callback_data='mailing_on'))
        else:
            text += "Рассылка включена."
            text += '\nУтренняя рассылка '
            if user['morning'] is not None:
                text += f'в {user['morning']} час{Hours_ending.get(user['morning'],'ов')}; '
            else:
                text += 'не назначена; '
            text += '\nВечерняя рассылка '
            if user['evening'] is not None:
                text += f'в {user['evening']} час{Hours_ending.get(user['evening'],'ов')}; '
            else:
                text += 'не назначена.'
            button_list.append(InlineKeyboardButton(text="Редактировать вечернюю", callback_data='mailing_evening_edit'))
            button_list.append(InlineKeyboardButton(text="Редактировать утреннюю", callback_data='mailing_morning_edit'))
            button_list.append(InlineKeyboardButton(text="Отключить всё", callback_data='mailing_off'))
        return text, button_list


    def _make_timezone_info(self, user: dict) -> str:
        text = ""
        # Временная зона к МСК
        if user['timezone'] is None:
            text += "Временная зона не определена."
        else:
            timezone = user['timezone'] - 3
            text += "Врменная зона - МСК"
            if timezone < 0:
                text += f'{timezone}'
            else:
                text += f'+{timezone}'
            text += "."
        return text

    def _parse_tz(self, tz_str: str) -> int:
        """
        Распознать временную зону и проверить вхождение в интервал
        """
        if tz_str[0] == '-' and tz_str[1:].isdigit():
            tz_num = int(tz_str[1:]) * -1
        elif tz_str[0] == '+' and tz_str[1:].isdigit():
            tz_num = int(tz_str[1:])
        elif tz_str.isdigit():
            tz_num = int(tz_str)
        else:
            return None
        if tz_num not in range(-12, 13):
            return None
        return tz_num
