from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from telebot.asyncio_helper import ApiTelegramException
import asyncio

from utils import Days, BotType

Error = 'Какая-то проблема с обновлением данных... Обратись к администратору или попробуй позже.'
Unknown = "Извини, я пока могу реагировать только на определённые команды. Посмотри их в Меню."

CMD_START           = 'start'
CMD_HELP            = 'help'
CMD_STAT           = 'stat'
CMD_TODAY           = 'today'
CMD_TOMORROW        = 'tomorrow'
CMD_YESTERDAY       = 'yesterday'
CMD_TIMEZONE        = 'timezone'
CMD_MAILING         = 'mailing'
BTN_CANCEL          = 'editing_cancel'
BTN_SIGN            = 'sign_'
BTN_HOLY            = 'holy_'
BTN_TZ_CHANGE       = f'{CMD_TIMEZONE}_change'
BTN_ML_TIME_BACK    = f'{CMD_MAILING}_back'
BTN_ML_TURN_TO      = f'{CMD_MAILING}_turn_'
BTN_ML_TIME_EDIT    = f'{CMD_MAILING}_edit_'
BTN_ML_TODAY        = 'today'
BTN_ML_TOMORROW     = 'tomorrow'
BTN_ML_TIME_SET    = f'{CMD_MAILING}_time_'
BTN_ON              = 'on_'
BTN_OFF             = 'off_'



class TG_Sender:
    def __init__(self, token, db_handler, ms_producer, logger):
        self._db_type = BotType.TG.value
        self._bot = AsyncTeleBot(token)
        self._db_handler = db_handler
        self._ms_producer = ms_producer
        self._logger = logger
        self._user_inreract = {}

        @self._bot.message_handler(commands=[CMD_START])
        async def welcome_send(message):
            """
            Начало работы с ботом: оповещение и опрос
            """
            self._logger.info(f'New user {message.chat.id}')
            if await self._db_handler.add_user(message.chat.id, self._db_type):
                text = "Привет. Я бот Месяцеслова.\n\n"\
                    f"Ты можешь узнать у меня, что говорит Месяцеслов о сегодняшнем дне (/{CMD_TODAY}), "\
                    f"дне прошедшем (/{CMD_YESTERDAY}) и дне грядущем (/{CMD_TOMORROW}).\n\n"\
                    "Удачи тебе сегодня, завтра и всегда!"
                try:
                    await self._bot.send_message(message.chat.id, text)
                except ApiTelegramException as e:
                    self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')
                text = "Для определения твоей даты я использую информацию о часовом поясе. "\
                    "По умолчанию используется часовой пояс МСК. Ты всегда можешь изменить "\
                    f"его командой /{CMD_TIMEZONE}.\n\n"\
                    "Пришли мне свой часовой пояс в целых часах относительно Москвы:"
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(InlineKeyboardButton(text="По умолчанию",callback_data=BTN_CANCEL))
                try:
                    message = await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)
                except ApiTelegramException as e:
                    self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')
                self._user_inreract[message.chat.id] = {'type':2, 'msg':message.message_id}
            else:
                text = Error
                try:
                    await self._bot.send_message(message.chat.id, text)
                except ApiTelegramException as e:
                    self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.message_handler(commands=[CMD_HELP])
        async def help_send(message):
            """
            Подсказка - вывод доступных команд
            """
            text = "Привет!\nЯ бот Месяцеслова. Я могу сообщить о дне всё согласно Месяцеслову: пост "\
            "и его степень, допустимость венчания, церковнеые праздники, народное название дня, "\
            "приметы и пословицы.\n\n"\
            f"Ты можешь использовать команды /{CMD_YESTERDAY}, /{CMD_TODAY} и /{CMD_TOMORROW}, чтобы "\
            "получить информацию о прошедшем, текущем и грядущем днях соответстввенно.\n\n"\
            "Так же я дважды в сутки осуществляю рассылку с церковными праздниках на текущий день и "\
            f"приметами на следующий день. Управлять рассылкой можно командой /{CMD_MAILING}.\n\n"\
            "Расчёт твой текущей даты и времени осуществляется с учётом часового пояса. Изменяется он "\
            f"командой /{CMD_TIMEZONE}."
            try:
                await self._bot.send_message(message.chat.id, text)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.message_handler(commands=[CMD_STAT])
        async def stat_send(message):
            """
            Статистика по боту
            """
            text = Unknown
            if user := await self._db_handler.get_user_info(message.chat.id, self._db_type):
                if user['admin'] == True:
                    all_users = await self._db_handler.get_users(self._db_type)
                    p_count, g_count = [0,0], [0,0]
                    for u in all_users:
                        if u['id'] > 0: counter = p_count
                        else:           counter = g_count
                        counter[0] += 1
                        if u['mailing']:
                            counter[1] += 1
                    text = f"Всего {p_count[0]} пользоватлей, из них {p_count[1]} пользуется рассылкой.\n"\
                            f"Всего {g_count[0]} групп, из них {g_count[1]} с включённой рассылкой."
            try:
                await self._bot.reply_to(message, text)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.message_handler(commands=[CMD_TODAY, CMD_TOMORROW, CMD_YESTERDAY])
        async def slovo_reply_commands(message):
            """
            Обработка команд /today, /tomorrow, /yesterday - показать кнопки
            """
            text = "Что бы ты хотел узнать?"
            cmd = message.text.split('@')[0]
            # Назначаем кнопки
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_sing = InlineKeyboardButton(text="Приметы", callback_data=f'{BTN_SIGN}{cmd[1:]}')
            button_holy = InlineKeyboardButton(text="Поминаемые святые", callback_data=f'{BTN_HOLY}{cmd[1:]}')
            keyboard.add(button_sing, button_holy)
            try:
                await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.callback_query_handler(func=lambda call: call.data[:5] in (BTN_SIGN, BTN_HOLY))
        async def slovo_send_by_request(call):
            """
            Обработка команд /today, /tomorrow, /yesterday - результат нажатия кнопки
            """
            message = call.message
            # Получаем часовой пояс пользователя
            user = await self._db_handler.get_user_info(message.chat.id, self._db_type)
            if user is None:
                user = {'timezone':0}
            # Получаем запрашиваемый день
            if call.data.endswith(CMD_YESTERDAY):
                day = Days.YESTERDAY
            elif call.data.endswith(CMD_TODAY):
                day = Days.TODAY
            elif call.data.endswith(CMD_TOMORROW):
                day = Days.TOMMOROW
            else:
                day = Days.ERROR
            # Получаем Слово на день
            if call.data.startswith(BTN_SIGN):
                text_func = self._ms_producer.make_sign
            elif call.data.startswith(BTN_HOLY):
                text_func = self._ms_producer.make_holy
            else:
                text_func = self._ms_producer.make_sign
                day = Days.ERROR
            text = await text_func(user, day)
            parse = 'Markdown'
            # Отредактировать сообщение
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id,
                                                parse_mode=parse)
                self._logger.debug(f'Send Slovo for request of user {message.chat.id}')
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.message_handler(commands=[CMD_TIMEZONE])
        async def timezone_start_choice(message):
            """
            Обработка команды /timezone - спросить, что делаем
            """
            keyboard = None
            if user := await self._db_handler.get_user_info(message.chat.id, self._db_type):
                text = 'Часовой пояс используется для определения твоей текущей даты, так как мы можем '\
                'быть на разных сторонах Земли.\n\n\N{globe with meridians} Сейчас твой '
                text += self._make_timezone_info(user)
                text += '\n\nЧто мне сдалать?'
                keyboard = InlineKeyboardMarkup(row_width=1)
                button_list = []
                button_list.append(InlineKeyboardButton(text="Изменить",callback_data=BTN_TZ_CHANGE))
                button_list.append(InlineKeyboardButton(text="Ничего",callback_data=BTN_CANCEL))
                keyboard.add(*button_list)
            else:
                text = Error
            try:
                await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.callback_query_handler(func=lambda call: call.data == BTN_TZ_CHANGE)
        async def timezone_change(call):
            """
            Обработка команды /timezone - запросить и ожидать ввод
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += "\nПришли мне свой часовой пояс в целых часах относительно Москвы:"
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(text="Отменить",callback_data=BTN_CANCEL))
            # Запомнить пользователя
            self._user_inreract[message.chat.id] = {'type':1, 'msg':message.message_id}
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.message_handler(commands=[CMD_MAILING])
        async def mailing_start_choice(message):
            """
            Обработка команды /mailing - спросить, что делаем
            """
            text, keyboard = await self._make_mailing_choice(message.chat.id)
            if keyboard:
                text += '\n\nЧто редактируем?'
            try:
                await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.callback_query_handler(func=lambda call: call.data == BTN_ML_TIME_BACK)
        async def mailing_return_to_start_choice(call):
            """
            Обработка команды /mailing - вернуться к главному меню
            """
            message = call.message
            text, keyboard = await self._make_mailing_choice(message.chat.id)
            if keyboard:
                text += '\n\nЧто редактируем?'
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            
        @self._bot.callback_query_handler(func=lambda call: call.data.startswith(BTN_ML_TURN_TO))
        async def mailing_turn(call):
            """
            Обработка команды /mailing - переключить и запросить дальнейшие действия
            """
            message = call.message
            turn_to = True if call.data.endswith(BTN_ON) else False
            if await self._db_handler.set_user_mailing(message.chat.id, self._db_type, turn_to):
                text, keyboard = await self._make_mailing_choice(message.chat.id)
                if keyboard:
                    text += '\n\nЧто ещё изменить?'
            else:
                text = Error
                keyboard = None
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.callback_query_handler(func=lambda call: call.data[:13] == BTN_ML_TIME_EDIT)
        async def mailing_edit_choice(call):
            """
            Обработка команды /mailing - запросить дальнейшие действия с рассылкой
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += f'\nРедактируем рассылку на {"следующий" if call.data[13:] == BTN_ML_TOMORROW else " текущий"} день:'
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_list = []
            user = await self._db_handler.get_user_info(message.chat.id, self._db_type)
            if user[call.data[13:]] is None:
                button_list.append(InlineKeyboardButton(text="Включить рассылку",
                                    callback_data=f'{BTN_ML_TIME_SET}{BTN_ON}{call.data[13:]}'))
            else:
                button_list.append(InlineKeyboardButton(text="Изменить время",
                                    callback_data=f'{BTN_ML_TIME_SET}{BTN_ON}{call.data[13:]}'))
                button_list.append(InlineKeyboardButton(text="Отменить рассылку",
                                    callback_data=f'{BTN_ML_TIME_SET}{BTN_OFF}{call.data[13:]}'))
            button_list.append(InlineKeyboardButton(text="Назад",callback_data=BTN_ML_TIME_BACK))
            keyboard.add(*button_list)
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.callback_query_handler(func=lambda call: call.data[:16] == f'{BTN_ML_TIME_SET}{BTN_ON}')
        async def mailing_time_change(call):
            """
            Обработка команды /mailing - запросить и ожидать ввод вермя рассылки
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += "\nПришли мне время рассылки на "
            text += "следующий" if call.data[16:] == BTN_ML_TOMORROW else "текущий"
            text += " день в твоём часовом поясе 24-часовом формате:"
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(text="Отменить",callback_data=BTN_CANCEL))
            # Запомнить пользователя
            if call.data[16:] == BTN_ML_TOMORROW:
                change_type = 4
            else:
                change_type = 3
            self._user_inreract[message.chat.id] = {'type':change_type, 'msg':message.message_id}
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.callback_query_handler(func=lambda call: call.data[:17] == f'{BTN_ML_TIME_SET}{BTN_OFF}')
        async def mailing_off_change(call):
            """
            Обработка команды /mailing - отключить рассылку и запросить дальнейшие действия
            """
            message = call.message
            keyboard = None
            if call.data.endswith(BTN_ML_TOMORROW):
                edit_func = self._db_handler.set_user_tomorrow_time
            else:
                edit_func = self._db_handler.set_user_today_time
            if await edit_func(message.chat.id, self._db_type, None):
                text, keyboard = await self._make_mailing_choice(message.chat.id)
                if keyboard:
                    text += '\n\nЧто ещё изменить?'
            else:
                text = Error
                keyboard = None
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.callback_query_handler(func=lambda call: call.data == BTN_CANCEL)
        async def editing_cancel_edit(call):
            """
            Обработка команды /mailing и /timezone - ничего не менять
            """
            message = call.message
            if type(self._user_inreract.get(message.chat.id)) is dict:
                inter_type = self._user_inreract[message.chat.id]['type']
                self._user_inreract.pop(message.chat.id)
            else: inter_type = None
            # Отредактировать сообщение - удалить часть с вопросом и кнопки
            text = message.text[:message.text.rindex('\n')]
            try:
                await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            # При старте спросить про рассылку
            if inter_type == 2:
                text, keyboard = await self._make_mailing_choice(message.chat.id)
                if keyboard:
                    text = "Так же я могу делать рассылку с праздниками и приметами. " + text
                    text += '\n\nХочешь что-нибудь получать?'
                try:
                    await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)
                except ApiTelegramException as e:
                    self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')

        @self._bot.message_handler()
        async def over_parse(message):
            """
            Обрабка всего прочего:
            - Проверка на текстовый ввод для /timezone и /mailing;
            - Все остальные случаи.
            """
            # Проверка на текстовый ввод для бота
            user_id = message.chat.id
            if type(self._user_inreract.get(user_id)) is dict:
                # Проверка на команду /timezone - записать часовой пояс
                if self._user_inreract[user_id]['type'] in (1, 2):
                    # Распознать число со знаком и проврить вхождение в интервал
                    tz_num = self._parse_tz(message.text)
                    if tz_num is not None:
                        # Убрать кнопку отмены и очистить хранилище
                        try:
                            await self._bot.edit_message_reply_markup(user_id,
                                        self._user_inreract[user_id]['msg'], None)
                        except ApiTelegramException as e:
                            self._logger.warning(f'Exception in Telegram API with {user_id}\n'\
                                            f'\t"{e}" on {e.__traceback__.tb_lineno}')
                        inter_type = self._user_inreract[user_id]['type']
                        self._user_inreract.pop(user_id)
                        # Привести ЧП к UTC из МСК и записать результаты в БД
                        timezone = tz_num + 3
                        res = await self._db_handler.set_user_timezone(user_id, self._db_type, timezone)
                        if res:
                            user = await self._db_handler.get_user_info(user_id, self._db_type)
                            text = 'Готово!\n\n\N{globe with meridians} Теперь твой ' 
                            text += self._make_timezone_info(user)
                        else:
                            text = Error
                        try:
                            await self._bot.send_message(user_id, text)
                        except ApiTelegramException as e:
                            self._logger.warning(f'Exception in Telegram API with {user_id}\n'\
                                            f'\t"{e}" on {e.__traceback__.tb_lineno}')
                        # При старте спросить про рассылку
                        if res and inter_type == 2:
                            text, keyboard = await self._make_mailing_choice(user)
                            if keyboard:
                                text = "Так же я могу делать рассылку с праздниками и приметами. " + text
                                text += '\n\nХочешь что-нибудь получать?'
                            try:
                                await self._bot.send_message(user_id, text, reply_markup=keyboard)
                            except ApiTelegramException as e:
                                self._logger.warning(f'Exception in Telegram API with {user_id}\n'\
                                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
                    else:
                        text = "Часовой пояс должен быть целочисленным и в пределах от -15 до +9"
                        try:
                            await self._bot.send_message(user_id, text)
                        except ApiTelegramException as e:
                            self._logger.warning(f'Exception in Telegram API with {user_id}\n'\
                                            f'\t"{e}" on {e.__traceback__.tb_lineno}')
                # Проверка на команду /mailing - записать время рассылки
                elif self._user_inreract[user_id]['type'] in (3, 4):
                    time = self._parse_mailing_time(message.text)
                    if time is not None:
                        try:
                            await self._bot.edit_message_reply_markup(user_id,
                                        self._user_inreract[user_id]['msg'], None)
                        except ApiTelegramException as e:
                            self._logger.warning(f'Exception in Telegram API with {user_id}\n'\
                                            f'\t"{e}" on {e.__traceback__.tb_lineno}')
                        if self._user_inreract[user_id]['type'] == 3:
                            edit_func = self._db_handler.set_user_today_time
                        else:
                            edit_func = self._db_handler.set_user_tomorrow_time
                        self._user_inreract.pop(user_id)
                        # Привести Время к UTC из ЧП пользователя
                        user = await self._db_handler.get_user_info(user_id, self._db_type)
                        time = (time - user['timezone'])%24
                        # Записать результаты в БД
                        if await edit_func(user_id, self._db_type, time):
                            text, keyboard = await self._make_mailing_choice(user_id)
                            if keyboard:
                                text += '\n\nЧто ещё изменить?'
                        else:
                            text = Error
                            keyboard = None
                        try:
                            await self._bot.send_message(user_id, text, reply_markup=keyboard)
                        except ApiTelegramException as e:
                            self._logger.warning(f'Exception in Telegram API with {user_id}\n'\
                                            f'\t"{e}" on {e.__traceback__.tb_lineno}')
                    else:
                        text = "Время рассылки должно быть целочисленным и в пределах от 0 до 23"
                        try:
                            await self._bot.send_message(user_id, text)
                        except ApiTelegramException as e:
                            self._logger.warning(f'Exception in Telegram API with {user_id}\n'\
                                            f'\t"{e}" on {e.__traceback__.tb_lineno}')
            # Все остальные случаи в личных чатах (не группах)
            elif user_id > 0:
                text = Unknown
                try:
                    await self._bot.reply_to(message, text)
                except ApiTelegramException as e:
                    self._logger.warning(f'Exception in Telegram API with {message.chat.id}\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')

    def poll(self):
        """
        Вернуть асинхронную функцию бесконечного опроса бота
        """
        return self._bot.polling()

    async def slovo_send_by_mailing(self, user, day_type):
            """
            Отправить сообщение с рассылкой
            """
            if day_type == Days.TODAY:
                text_func = self._ms_producer.make_holy
                day = "today"
            elif day_type == Days.TOMMOROW:
                text_func = self._ms_producer.make_sign
                day = "tomorrow"
            else:
                self._logger.debug(f'Wrong day_type {day} in mailing of user {user['id']}')
                return
            # Получаем Слово на день
            text = await text_func(user, day_type)
            parse = 'Markdown'
            # Отправить сообщение
            try:
                await self._bot.send_message(user['id'], text, parse_mode=parse)
                self._logger.debug(f'Send Slovo in {day} mailing of user {user['id']}')
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API with {user['id']}\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')

    async def _make_mailing_choice(self, user_id):
            """
            Обработка команды /mailing - собрать главное меню для отображения
            """
            text: str
            keyboard = None
            if user := await self._db_handler.get_user_info(user_id, self._db_type):
                text = 'Рассылка осуществляется дважды в сутки: я передаю информацию о '\
                'церковных праздниках на текущий день и приметы на следующий день.\n\n'
                text += '\N{globe with meridians} Сейчас твой ' + self._make_timezone_info(user) + '\n'
                text += self._make_mailing_info(user)
                keyboard = InlineKeyboardMarkup(row_width=1)
                button_list = []
                if user['mailing'] != 1:
                    button_list.append(InlineKeyboardButton(text="Включить", callback_data=f'{BTN_ML_TURN_TO}{BTN_ON}'))
                else:
                    button_list.append(InlineKeyboardButton(text="Рассылка на текущий день",
                                                            callback_data=f'{BTN_ML_TIME_EDIT}{BTN_ML_TODAY}'))
                    button_list.append(InlineKeyboardButton(text="Рассылка на следующий день",
                                                            callback_data=f'{BTN_ML_TIME_EDIT}{BTN_ML_TOMORROW}'))
                    button_list.append(InlineKeyboardButton(text="Отключить всё",
                                                            callback_data=f'{BTN_ML_TURN_TO}{BTN_OFF}'))
                button_list.append(InlineKeyboardButton(text="Ничего",callback_data=BTN_CANCEL))
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
            text += "Рассылка включена;\n\N{calendar} Рассылка на сегодня "
            if user['today'] is not None:
                time = (user['today'] + tz)%24
                text += f'в {time} час{self._hours_ending(time)};'
            else:
                text += 'не назначена;'
            text += '\n\N{Chart With Upwards Trend} Рассылка на завтра '
            if user['tomorrow'] is not None:
                time = (user['tomorrow'] + tz)%24
                text += f'в {time} час{self._hours_ending(time)}; '
            else:
                text += 'не назначена.'
        return text

    def _make_timezone_info(self, user: dict) -> str:
        """
        Напечатать информацию о часовом поясе относительно МСК
        """
        text = 'часовой пояс '
        # Часовой пояс к МСК
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

    def _parse_mailing_time(self, time_str: str) -> int:
        """
        Распознать записать время рассылки и проверить вхождение в интервал
        """
        time_num: int
        if time_str.isdigit():
            time_num = int(time_str)
        else:
            return None
        if time_num not in range(0, 24):
            return None
        return time_num

    def _hours_ending(self, hour):
        if hour == 1: return ''
        elif hour in range(2, 4): return  'а'
        else: return  'ов'