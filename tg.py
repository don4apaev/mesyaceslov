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
                "Для определения даты по умолчанию используется часовой пояс МСК+0. "\
                "Ты всегда можешь изменить его командой /timezone.\n\n"\
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

        @self._bot.callback_query_handler(func=lambda call: call.data[:5] in ('sign_', 'holy_'))
        async def slovo_send_by_request(call):
            """
            Обработка команд /today, /tomorrow, /yesterday - результат нажатия кнопки
            """
            message = call.message
            # Получаем часовой пояс пользователя
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
        async def timezone_start_choice(message):
            """
            Обработка команды /timezone - спросить, что делаем
            """
            keyboard = None
            if user := await self._db_handler.get_user_info(message.chat.id):
                text = 'Часовой пояс используется для определения твоей текущей даты, так как мы можем '\
                'быть на разных сторонах Земли.\n\n\N{globe with meridians} Сейчас твой '
                text += self._make_timezone_info(user)
                text += '\n\nЧто мне сдалать?'
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
        async def timezone_change(call):
            """
            Обработка команды /timezone - запросить и ожидать ввод
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += "\nПришли мне свой часовой пояс в целых часах относительно Москвы:"
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_c = InlineKeyboardButton(text="Отменить",callback_data='editing_cancel')
            keyboard.add(button_c)
            # Запомнить пользователя
            self._user_inreract[message.chat.id] = {'type':1, 'msg':message.message_id}
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.message_handler(commands=['mailing'])
        async def mailing_start_choice(message):
            """
            Обработка команды /mailing - спросить, что делаем
            """
            text, keyboard = await self._make_mailing_choice(message)
            text += '\n\nЧто редактируем?'
            await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data == 'mailing_back')
        async def mailing_return_to_start_choice(call):
            """
            Обработка команды /mailing - вернуться к главному меню
            """
            message = call.message
            text, keyboard = await self._make_mailing_choice(message)
            text += '\n\nЧто редактируем?'
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            
        @self._bot.callback_query_handler(func=lambda call: call.data[:13] == 'mailing_turn_')
        async def mailing_turn(call):
            """
            Обработка команды /mailing - переключить и запросить дальнейшие действия
            """
            message = call.message
            turn_to = True if call.data.endswith('_on') else False
            if await self._db_handler.set_user_mailing(message.chat.id, turn_to):
                text, keyboard = await self._make_mailing_choice(message)
                text += '\n\nЧто ещё изменить?'
            else:
                text = Error
                keyboard = None
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[:13] == 'mailing_edit_')
        async def mailing_edit_choice(call):
            """
            Обработка команды /mailing - запросить дальнейшие действия с рассылкой
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += f'\nРедактируем {"вечернюю" if call.data[13:] == "evening" else " утреннюю"} рассылку:'
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_list = []
            user = await self._db_handler.get_user_info(message.chat.id)
            if user[call.data[13:]] is None:
                button_list.append(InlineKeyboardButton(text="Включить рассылку",
                                    callback_data=f'mailing_time_on_{call.data[13:]}'))
            else:
                button_list.append(InlineKeyboardButton(text="Изменить время",
                                    callback_data=f'mailing_time_on_{call.data[13:]}'))
                button_list.append(InlineKeyboardButton(text="Отменить рассылку",
                                    callback_data=f'mailing_time_off_{call.data[13:]}'))
            button_list.append(InlineKeyboardButton(text="Назад",callback_data='mailing_back'))
            keyboard.add(*button_list)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[:16] == 'mailing_time_on_')
        async def mailing_time_change(call):
            """
            Обработка команды /mailing - запросить и ожидать ввод вермя рассылки
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += "\nПришли мне время "
            text += "вечерней" if call.data[16:] == "evening" else " утренней"
            text += " рассылки в твоём часовом поясе 24-часовом формате:"
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_c = InlineKeyboardButton(text="Отменить",callback_data='editing_cancel')
            keyboard.add(button_c)
            # Запомнить пользователя
            if call.data[16:] == "evening":
                change_type = 3
            else:
                change_type = 2
            self._user_inreract[message.chat.id] = {'type':change_type, 'msg':message.message_id}
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[:17] == 'mailing_time_off_')
        async def mailing_off_change(call):
            """
            Обработка команды /mailing - отключить рассылку и запросить дальнейшие действия
            """
            message = call.message
            keyboard = None
            if call.data.endswith('evening'):
                edit_func = self._db_handler.set_user_evening
            else:
                edit_func = self._db_handler.set_user_morning
            if await edit_func(message.chat.id, None):
                text, keyboard = await self._make_mailing_choice(message)
            else:
                text = Error
                keyboard = None
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

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
        async def over_parse(message):
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
                        # Привести ЧП к UTC из МСК и записать результаты в БД
                        timezone = tz_num + 3
                        if await self._db_handler.set_user_timezone(message.chat.id, timezone):
                            user = await self._db_handler.get_user_info(message.chat.id)
                            text = 'Готово!\n\N{globe with meridians} Теперь твой ' 
                            text += self._make_timezone_info(user)
                        else:
                            text = Error
                        await self._bot.send_message(message.chat.id, text)
                    else:
                        text = "Часовой пояс должен быть целочисленным и в пределах от -15 до +9"
                        await self._bot.send_message(message.chat.id, text)
                # Проверка на команду /mailing - записать время рассылки
                elif self._user_inreract[message.chat.id]['type'] in (2, 3):
                    time = self._parse_mailing_time(message.text, self._user_inreract[message.chat.id]['type'])
                    if time is not None:
                        await self._bot.edit_message_reply_markup(message.chat.id,
                                        self._user_inreract[message.chat.id]['msg'], None)
                        if self._user_inreract[message.chat.id]['type'] == 2:
                            edit_func = self._db_handler.set_user_morning
                        else:
                            edit_func = self._db_handler.set_user_evening
                        self._user_inreract.pop(message.chat.id)
                        # Привести Время к UTC из ЧП пользователя
                        user = await self._db_handler.get_user_info(message.chat.id)
                        if user['timezone'] is None:
                            timezone = 3
                        else:
                            timezone = user['timezone']
                        time = time - timezone
                        # Записать результаты в БД
                        if await edit_func(message.chat.id, time):
                            text, keyboard = await self._make_mailing_choice(message)
                            text += '\n\nЧто ещё изменить?'
                        else:
                            text = Error
                            keyboard = None
                        await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)
                    else:
                        text = "Время {} рассылки должно быть целочисленным и в пределах от {} до {}"
                        if self._user_inreract[message.chat.id]['type'] == 2:
                            text = text.format('утренней', 0, 11)
                        else:
                            text = text.format('вечерней', 12, 23)
                        await self._bot.send_message(message.chat.id, text)
            # Все остальные случаи
            else:
                text = "Извини, я пока могу реагировать только на определённые команды. "\
                "Посмотри их в Меню."
                await self._bot.reply_to(message, text)

    def poll(self):
        return self._bot.polling()

    async def _make_mailing_choice(self, message):
            """
            Обработка команды /mailing - собрать главное меню для отображения
            """
            text: str
            keyboard = None
            if user := await self._db_handler.get_user_info(message.chat.id):
                text = 'Рассылка осуществляется дважды в сутки: я передаю информацию о '\
                'церковных праздниках на текущий день и приметы на следующий день.\n\n'
                text += '\N{globe with meridians} Сейчас твой ' + self._make_timezone_info(user) + '\n'
                text += self._make_mailing_info(user)
                keyboard = InlineKeyboardMarkup(row_width=1)
                button_list = []
                if user['mailing'] != 1:
                    button_list.append(InlineKeyboardButton(text="Включить", callback_data='mailing_turn_on'))
                else:
                    button_list.append(InlineKeyboardButton(text="Рассылка на текущий день",
                                                            callback_data='mailing_edit_morning'))
                    button_list.append(InlineKeyboardButton(text="Рассылка на следующий день",
                                                            callback_data='mailing_edit_evening'))
                    button_list.append(InlineKeyboardButton(text="Отключить всё", callback_data='mailing_turn_off'))
                button_list.append(InlineKeyboardButton(text="Ничего",callback_data='editing_cancel'))
                keyboard.add(*button_list)
            else:
                text = Error
            return text, keyboard

    def _make_mailing_info(self, user: dict) -> tuple:
        """
        Напечатать информацию о настройках рассылки
        """
        text = '\N{envelope} '
        # Получаем статус и генерируем соответствующие кнопки
        if user['mailing'] != 1:
            text += "Рассылка отключена."
        else:
            tz = user['timezone']
            if tz is None: tz = 3
            text += "Рассылка включена;\n\N{calendar} Рассылка на сегодня "
            if user['morning'] is not None:
                time = user['morning'] + tz
                text += f'в {time} час{Hours_ending.get(time,"ов")};'
            else:
                text += 'не назначена;'
            text += '\n\N{Chart With Upwards Trend} Рассылка на завтра'
            if user['evening'] is not None:
                time = user['evening'] + tz
                text += f'в {time} час{Hours_ending.get(time,"ов")}; '
            else:
                text += 'не назначена.'
        return text

    def _make_timezone_info(self, user: dict) -> str:
        """
        Напечатать информацию о часовом поясе относительно МСК
        """
        text = 'часовой пояс '
        # Часовой пояс к МСК
        if user['timezone'] is None:
            text += "не определён (используется МСК)."
        else:
            timezone = user['timezone'] - 3
            text += "- МСК"
            if timezone < 0:
                text += f'{timezone}'
            elif timezone > 0:
                text += f'+{timezone}'
            text += "."
        return text

    def _parse_tz(self, tz_str: str) -> int:
        """
        Распознать часовой пояс и проверить вхождение в интервал
        """
        tz_num: int
        if tz_str[0] == '-' and tz_str[1:].isdigit():
            tz_num = int(tz_str[1:]) * -1
        elif tz_str[0] == '+' and tz_str[1:].isdigit():
            tz_num = int(tz_str[1:])
        elif tz_str.isdigit():
            tz_num = int(tz_str)
        else:
            return None
        if tz_num not in range(-15, 9):
            return None
        return tz_num

    def _parse_mailing_time(self, time_str: str, mailing_type: int) -> int:
        """
        Распознать записать время рассылки и проверить вхождение в интервал
        """
        time_num: int
        if time_str.isdigit():
            time_num = int(time_str)
        else:
            return None
        if mailing_type == 2:
            time_range = range(0, 12)
        elif mailing_type == 3:
            time_range = range(12, 24)
        else:
            return None
        if time_num not in time_range:
            return None
        return time_num
