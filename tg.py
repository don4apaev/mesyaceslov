from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from asyncio import sleep

from utils import Days, BotType
import bot as B

CMD_START           = 'start'
CMD_HELP            = 'help'
CMD_STAT            = 'stat'
CMD_TO_ALL          = 'toall: '
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

class TG_Sender(B.Bot_Sender):
    def __init__(self, token, **kwargs):
        super().__init__(**kwargs)
        self._db_type = BotType.TG.value
        self._bot = AsyncTeleBot(token)
        self._user_inreract = {}

        @self._bot.message_handler(commands=[CMD_START])
        @B.Bot_Sender.except_log
        async def welcome_send(message):
            """
            Начало работы с ботом: оповещение и опрос
            """
            self._logger.info(f'New Telegram user {message.chat.id}')
            if await self._db_handler.add_user(message.chat.id, self._db_type):
                await self._bot.send_message(message.chat.id, B.Hello_to.format(
                                        f'/{CMD_TODAY}', f'/{CMD_YESTERDAY}', f'/{CMD_TOMORROW}'))
                keyboard = InlineKeyboardMarkup(row_width=1)
                keyboard.add(InlineKeyboardButton(text=B.Btn_as_is,callback_data=BTN_CANCEL))
                message = await self._bot.send_message(message.chat.id,
                                                    B.First_quest.format(f'/{CMD_TIMEZONE}'),
                                                        reply_markup=keyboard)
                self._user_inreract[message.chat.id] = {'type':2, 'msg':message.message_id}
            else:
                user = await self._db_handler.get_user_info(message.chat.id, self._db_type)
                text = B.Already + '\n' + self._make_timezone_info(user)
                text += '\n' + self._make_mailing_info(user)
                await self._bot.send_message(message.chat.id, text)

        @self._bot.message_handler(commands=[CMD_HELP])
        @B.Bot_Sender.except_log
        async def help_send(message):
            """
            Подсказка - вывод доступных команд
            """
            await self._bot.send_message(message.chat.id, B.Help.format(f'/{CMD_YESTERDAY}',
                            f'/{CMD_TODAY}', f'/{CMD_TOMORROW}', f'/{CMD_MAILING}', f'/{CMD_TIMEZONE}'))

        @self._bot.message_handler(commands=[CMD_STAT], chat_types=['private'])
        @B.Bot_Sender.except_log
        async def stat_send(message):
            """
            Статистика по боту
            """
            text = B.Unknown
            # Только если пользователь существует и администратор
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
                    text = B.Statistic.format(p_count[0], p_count[1], g_count[0], g_count[1])
            await self._bot.reply_to(message, text)

        @self._bot.message_handler(func=lambda m: m.text.startswith(CMD_TO_ALL), chat_types=['private'])
        # @B.Bot_Sender.except_log
        async def send_from_admin_to_all(message):
            """
            Статистика по боту
            """
            text = B.Unknown
            # Только если пользователь существует и администратор
            if user := await self._db_handler.get_user_info(message.chat.id, self._db_type):
                if user['admin'] == True:
                    text_to_all = message.text.removeprefix(CMD_TO_ALL)
                    if message.entities:
                        for e in message.entities:
                            e.offset -= len(CMD_TO_ALL)
                    all_users = await self._db_handler.get_users(self._db_type)
                    bad = []
                    ok = 0
                    limit_count = 0
                    for u in all_users:
                        if limit_count == 20:
                            await sleep(1)
                            limit_count = 0
                        try:
                            await self._bot.send_message(u['id'], text_to_all, entities=message.entities)
                        except Exception as e:
                            bad.append(str(u['id']))
                            self._logger.info(f'Broadcast error for VK user {u['id']}: {e}')
                        else:
                            ok += 1
                            self._logger.debug(f'Send broadcast to VK user {u['id']}')
                        finally:
                            limit_count += 1
                    text = f'Send in {ok} chats.'
                    if len(bad):
                        text += f'\nError with {len(bad)} chats: {', '.join(bad)}'
            await self._bot.reply_to(message, text)

        @self._bot.message_handler(commands=[CMD_TODAY, CMD_TOMORROW, CMD_YESTERDAY])
        @B.Bot_Sender.except_log
        async def slovo_reply_commands(message):
            """
            Обработка команд /today, /tomorrow, /yesterday - показать кнопки
            """
            text = B.Day_quest
            cmd = message.text.split('@')[0]
            # Назначаем кнопки
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_sing = InlineKeyboardButton(text=B.Btn_signs, callback_data=f'{BTN_SIGN}{cmd[1:]}')
            button_holy = InlineKeyboardButton(text=B.Btn_saints, callback_data=f'{BTN_HOLY}{cmd[1:]}')
            keyboard.add(button_sing, button_holy)
            await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[:5] in (BTN_SIGN, BTN_HOLY))
        @B.Bot_Sender.except_log
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
            elif call.data.endswith(CMD_TOMORROW):
                day = Days.TOMMOROW
            else:
                day = Days.TODAY
            # Получаем Слово на день
            if call.data.startswith(BTN_SIGN):
                text_func = self._ms_producer.make_sign
            else:
                text_func = self._ms_producer.make_holy
            text = await text_func(user, day)
            parse = 'Markdown'
            # Отредактировать сообщение
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id,
                                            parse_mode=parse)
            self._logger.debug(f'Send Slovo for request of VK user {message.chat.id}')

        @self._bot.message_handler(commands=[CMD_TIMEZONE])
        @B.Bot_Sender.except_log
        async def timezone_start_choice(message):
            """
            Обработка команды /timezone - спросить, что делаем
            """
            keyboard = None
            if user := await self._db_handler.get_user_info(message.chat.id, self._db_type):
                text = B.TZ_promt
                text += self._make_timezone_info(user)
                text += B.TZ_quest
                keyboard = InlineKeyboardMarkup(row_width=1)
                button_list = []
                button_list.append(InlineKeyboardButton(text=B.Btn_change, callback_data=BTN_TZ_CHANGE))
                button_list.append(InlineKeyboardButton(text=B.Btn_nothing,callback_data=BTN_CANCEL))
                keyboard.add(*button_list)
            else:
                text = B.Error
            await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data == BTN_TZ_CHANGE)
        @B.Bot_Sender.except_log
        async def timezone_change(call):
            """
            Обработка команды /timezone - запросить и ожидать ввод
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += B.TZ_quest
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(text=B.Btn_undo,callback_data=BTN_CANCEL))
            # Запомнить пользователя
            self._user_inreract[message.chat.id] = {'type':1, 'msg':message.message_id}
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.message_handler(commands=[CMD_MAILING])
        @B.Bot_Sender.except_log
        async def mailing_start_choice(message):
            """
            Обработка команды /mailing - спросить, что делаем
            """
            text, keyboard = await self._make_mailing_choice(message.chat.id)
            if keyboard:
                text += B.Mailin_first_quest
            await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data == BTN_ML_TIME_BACK)
        @B.Bot_Sender.except_log
        async def mailing_return_to_start_choice(call):
            """
            Обработка команды /mailing - вернуться к главному меню
            """
            message = call.message
            text, keyboard = await self._make_mailing_choice(message.chat.id)
            text += B.Mailin_first_quest
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)
            
        @self._bot.callback_query_handler(func=lambda call: call.data.startswith(BTN_ML_TURN_TO))
        @B.Bot_Sender.except_log
        async def mailing_turn(call):
            """
            Обработка команды /mailing - переключить и запросить дальнейшие действия
            """
            message = call.message
            turn_to = True if call.data.endswith(BTN_ON) else False
            if await self._db_handler.set_user_mailing(message.chat.id, self._db_type, turn_to):
                text, keyboard = await self._make_mailing_choice(message.chat.id)
                text += B.Mailin_second_quest
            else:
                text = B.Error
                keyboard = None
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[:13] == BTN_ML_TIME_EDIT)
        @B.Bot_Sender.except_log
        async def mailing_edit_choice(call):
            """
            Обработка команды /mailing - запросить дальнейшие действия с рассылкой
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += B.Mailing_time_first_quest.format(\
                    B.Mailing_time_next if call.data[13:] == BTN_ML_TOMORROW else B.Mailing_time_now)
            keyboard = InlineKeyboardMarkup(row_width=1)
            button_list = []
            user = await self._db_handler.get_user_info(message.chat.id, self._db_type)
            if user[call.data[13:]] is None:
                button_list.append(InlineKeyboardButton(text=B.Btn_on_time,
                                    callback_data=f'{BTN_ML_TIME_SET}{BTN_ON}{call.data[13:]}'))
            else:
                button_list.append(InlineKeyboardButton(text=B.Btn_chn_time,
                                    callback_data=f'{BTN_ML_TIME_SET}{BTN_ON}{call.data[13:]}'))
                button_list.append(InlineKeyboardButton(text=B.Btn_off_time,
                                    callback_data=f'{BTN_ML_TIME_SET}{BTN_OFF}{call.data[13:]}'))
            button_list.append(InlineKeyboardButton(text=B.Btn_back,callback_data=BTN_ML_TIME_BACK))
            keyboard.add(*button_list)
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[:16] == f'{BTN_ML_TIME_SET}{BTN_ON}')
        @B.Bot_Sender.except_log
        async def mailing_time_change(call):
            """
            Обработка команды /mailing - запросить и ожидать ввод вермя рассылки
            """
            message = call.message
            text = message.text[:message.text.rindex('\n')]
            text += B.Mailing_time_second_quest.format(\
                    B.Mailing_time_next if call.data[16:] == BTN_ML_TOMORROW else B.Mailing_time_now)
            keyboard = InlineKeyboardMarkup(row_width=1)
            keyboard.add(InlineKeyboardButton(text=B.Btn_undo,callback_data=BTN_CANCEL))
            # Запомнить пользователя
            if call.data[16:] == BTN_ML_TOMORROW:
                change_type = 4
            else:
                change_type = 3
            self._user_inreract[message.chat.id] = {'type':change_type, 'msg':message.message_id}
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data[:17] == f'{BTN_ML_TIME_SET}{BTN_OFF}')
        @B.Bot_Sender.except_log
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
                text += B.Mailin_second_quest
            else:
                text = B.Error
                keyboard = None
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id, reply_markup=keyboard)

        @self._bot.callback_query_handler(func=lambda call: call.data == BTN_CANCEL)
        @B.Bot_Sender.except_log
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
            await self._bot.edit_message_text(text, message.chat.id, message_id=message.message_id)
            # При старте спросить про рассылку
            if inter_type == 2:
                text, keyboard = await self._make_mailing_choice(message.chat.id)
                text = B.Secon_quest.format(f'/{CMD_MAILING}', text)
                await self._bot.send_message(message.chat.id, text, reply_markup=keyboard)

        @self._bot.message_handler()
        @B.Bot_Sender.except_log
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
                        await self._bot.edit_message_reply_markup(user_id,
                                    self._user_inreract[user_id]['msg'], None)
                        inter_type = self._user_inreract[user_id]['type']
                        self._user_inreract.pop(user_id)
                        # Привести ЧП к UTC из МСК и записать результаты в БД
                        timezone = tz_num + 3
                        res = await self._db_handler.set_user_timezone(user_id, self._db_type, timezone)
                        user = await self._db_handler.get_user_info(user_id, self._db_type)
                        text = B.TZ_finish
                        text += self._make_timezone_info(user)
                        await self._bot.send_message(user_id, text)
                        # При старте спросить про рассылку
                        if res and inter_type == 2:
                            text, keyboard = await self._make_mailing_choice(user_id)
                            text = B.Secon_quest.format(f'/{CMD_MAILING}', text)
                            await self._bot.send_message(user_id, text, reply_markup=keyboard)
                    else:
                        text = B.TZ_warning
                        await self._bot.send_message(user_id, text)
                # Проверка на команду /mailing - записать время рассылки
                elif self._user_inreract[user_id]['type'] in (3, 4):
                    time = self._parse_mailing_time(message.text)
                    if time is not None:
                        await self._bot.edit_message_reply_markup(user_id, self._user_inreract[user_id]['msg'], None)
                        if self._user_inreract[user_id]['type'] == 3:
                            edit_func = self._db_handler.set_user_today_time
                        else:
                            edit_func = self._db_handler.set_user_tomorrow_time
                        self._user_inreract.pop(user_id)
                        # Привести Время к UTC из ЧП пользователя
                        user = await self._db_handler.get_user_info(user_id, self._db_type)
                        time = (time - user['timezone'])%24
                        # Записать результаты в БД
                        await edit_func(user_id, self._db_type, time)
                        text, keyboard = await self._make_mailing_choice(user_id)
                        text += B.Mailin_second_quest
                        await self._bot.send_message(user_id, text, reply_markup=keyboard)
                    else:
                        text = B.Mailing_time_warning
                        await self._bot.send_message(user_id, text)
            # Все остальные случаи в личных чатах (не группах)
            elif user_id > 0:
                text = B.Unknown
                await self._bot.reply_to(message, text)

    def poll(self):
        """
        Вернуть асинхронную функцию бесконечного опроса бота
        """
        return self._bot.polling()

    @B.Bot_Sender.except_log
    async def slovo_send_by_mailing(self, users, day_type):
            """
            Отправить сообщение с рассылкой
            """
            if day_type == Days.TOMMOROW:
                text_func = self._ms_producer.make_sign
                day = "tomorrow"
            else: # Days.TODAY
                text_func = self._ms_producer.make_holy
                day = "today"
            parse = 'Markdown'
            # Получаем Слово на день и отправить сообщение
            limit_count = 0
            for user in users:
                if limit_count == 30:
                    await sleep(1)
                    limit_count = 0
                text = await text_func(user, day_type)
                try:
                    await self._bot.send_message(user['id'], text, parse_mode=parse)
                except Exception as e:
                    self._logger.info(f'Mailing error for Telegram user {user['id']}: {e}')
                else:
                    self._logger.debug(f'Send Slovo in {day} mailing of Telegram user {user['id']}')
                finally:
                    limit_count += 1

    async def _make_mailing_choice(self, user_id):
            """
            Обработка команды /mailing - собрать главное меню для отображения
            """
            text: str
            keyboard = None
            if user := await self._db_handler.get_user_info(user_id, self._db_type):
                text = B.Mailing_info + self._make_timezone_info(user) + '\n' + self._make_mailing_info(user)
                keyboard = InlineKeyboardMarkup(row_width=1)
                button_list = []
                if user['mailing'] != 1:
                    button_list.append(InlineKeyboardButton(text=B.Btn_on, callback_data=f'{BTN_ML_TURN_TO}{BTN_ON}'))
                else:
                    button_list.append(InlineKeyboardButton(text=B.Btn_td_time,
                                                            callback_data=f'{BTN_ML_TIME_EDIT}{BTN_ML_TODAY}'))
                    button_list.append(InlineKeyboardButton(text=B.Btn_tm_time,
                                                            callback_data=f'{BTN_ML_TIME_EDIT}{BTN_ML_TOMORROW}'))
                    button_list.append(InlineKeyboardButton(text=B.Btn_off,
                                                            callback_data=f'{BTN_ML_TURN_TO}{BTN_OFF}'))
                button_list.append(InlineKeyboardButton(text=B.Btn_nothing,callback_data=BTN_CANCEL))
                keyboard.add(*button_list)
            else:
                text = B.Error
            return text, keyboard