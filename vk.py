from vkbottle.bot import Bot, Message, MessageEvent, rules
from vkbottle import Keyboard, Text, Callback, GroupEventType

from utils import Days, BotType
import bot as B

CMD_START           = 'Начать'
CMD_HELP            = 'Помощь'
CMD_MENU            = ("Meню", "меню", 'Help', 'help')
CMD_STAT            = 'stat'
CMD_TODAY           = 'Сегодня'
CMD_TOMORROW        = 'Завтра'
CMD_YESTERDAY       = 'Вчера'
CMD_TIMEZONE        = 'Часовой пояс'
CMD_MAILING         = 'Рассылка'
BTN_CANCEL          = 'editing_cancel'
BTN_SIGN            = 'sign'
BTN_HOLY            = 'holy'
BTN_TZ_CHANGE       = 'TZ_change'
BTN_ML_TIME_BACK    = 'MLNG_back'
BTN_ML_TURN_TO      = 'MLNG_turn'
BTN_ML_TIME_EDIT    = 'MLNG_edit'
BTN_ML_TODAY        = 'today'
BTN_ML_TOMORROW     = 'tomorrow'
BTN_ML_TIME_SET     = 'MLNG_time'
BTN_ON              = 'on'
BTN_OFF             = 'off'

class VK_Sender(B.Bot_Sender):
    def __init__(self, token, **kwargs):
        super().__init__(**kwargs)
        self._db_type = BotType.VK.value
        self._bot = Bot(token=token)
        self._user_inreract = {}

        @self._bot.on.message(func=lambda m: m.text.endswith(CMD_START)\
                                            or m.text.startswith(CMD_START))
        @B.Bot_Sender.except_log
        async def welcome_send(message):
            """
            Начало работы с ботом: оповещение и опрос
            """
            self._logger.info(f'New VK user {message.peer_id}')
            if await self._db_handler.add_user(message.peer_id, self._db_type):
                if message.peer_id < 2000000000:
                    keyboard = Keyboard(one_time=False)
                else:
                    keyboard = Keyboard(one_time=True)
                self._add_menu_buttons(keyboard)
                await message.answer(B.Hello_to.format(CMD_TODAY, CMD_YESTERDAY, CMD_TOMORROW),\
                                        keyboard=keyboard)
                keyboard = Keyboard(inline=True)
                keyboard.add(Callback(B.Btn_as_is, payload={'cmd': BTN_CANCEL}))
                repl = await message.answer(
                    B.First_quest.format('\N{globe with meridians}'+CMD_TIMEZONE),
                    keyboard=keyboard)
                self._user_inreract[message.peer_id] = {'type':2, 'msg':repl.conversation_message_id}
            else:
                user = await self._db_handler.get_user_info(message.peer_id, self._db_type)
                text = B.Already + '\n' + self._make_timezone_info(user)
                text += '\n' + self._make_mailing_info(user)
                await message.answer(text)

        @self._bot.on.message(func=lambda m: m.text.endswith((CMD_HELP, *CMD_MENU))\
                        or m.text.startswith(('\N{Circled Information Source}', CMD_HELP, *CMD_MENU)))
        @B.Bot_Sender.except_log
        async def help_send(message):
            """
            Подсказка - вывод доступных команд
            """
            if message.peer_id < 2000000000:
                keyboard = Keyboard(one_time=False)
            else:
                keyboard = Keyboard(one_time=True)
            self._add_menu_buttons(keyboard)
            await message.answer(B.Help.format('\N{HOURGLASS}'+CMD_YESTERDAY, 
                    '\N{calendar}'+CMD_TODAY, '\N{Crystal Ball}'+CMD_TOMORROW,
                    '\N{envelope}'+CMD_MAILING, '\N{globe with meridians}'+CMD_TIMEZONE),
                    keyboard=keyboard)

        @self._bot.on.private_message(text=CMD_STAT)
        @B.Bot_Sender.except_log
        async def stat_send(message):
            """
            Статистика по боту
            """
            text = B.Unknown
            # Только если пользователь существует и администратор
            if user := await self._db_handler.get_user_info(message.peer_id, self._db_type):
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
            await message.reply(text)

        @self._bot.on.message(func=lambda m: m.text.endswith((CMD_TODAY, CMD_TOMORROW, CMD_YESTERDAY))\
                or m.text.startswith(('\N{calendar}', CMD_TODAY,
                                    '\N{Crystal Ball}', CMD_TOMORROW,
                                    '\N{HOURGLASS}', CMD_YESTERDAY)))
        @B.Bot_Sender.except_log
        async def slovo_reply_commands(message):
            """
            Обработка команд /today, /tomorrow, /yesterday - показать кнопки
            """
            text = B.Day_quest
            if message.text.find(CMD_YESTERDAY) >=0:
                cmd = CMD_YESTERDAY
            elif message.text.find(CMD_TOMORROW) >=0:
                cmd = CMD_TOMORROW
            else:
                cmd = CMD_TODAY
            # Назначаем кнопки
            keyboard = Keyboard(inline=True)
            keyboard.add(Callback(B.Btn_signs, payload={'cmd': BTN_SIGN, "day": cmd}))
            keyboard.row()
            keyboard.add(Callback(B.Btn_saints, payload={'cmd': BTN_HOLY, "day": cmd}))
            await message.answer(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                            rules.FuncRule(lambda m: m.payload.get('cmd') in (BTN_SIGN, BTN_HOLY)))
        @B.Bot_Sender.except_log
        async def slovo_send_by_request(event):
            """
            Обработка команд /today, /tomorrow, /yesterday - результат нажатия кнопки
            """
            # Получаем часовой пояс пользователя
            user = await self._db_handler.get_user_info(event.user_id, self._db_type)
            if user is None:
                user = {'timezone':0}
            # Получаем запрашиваемый день
            if event.payload["day"] == CMD_YESTERDAY:
                day = Days.YESTERDAY
            elif  event.payload["day"] == CMD_TOMORROW:
                day = Days.TOMMOROW
            else:
                day = Days.TODAY
            # Получаем Слово на день
            if event.payload['cmd'] == BTN_SIGN:
                text_func = self._ms_producer.make_sign
            else:
                text_func = self._ms_producer.make_holy
            text = (await text_func(user, day)).replace('_','').replace('*','')
            # Отредактировать сообщение
            await event.edit_message(text)
            self._logger.debug(f'Send Slovo for request of VK user {event.user_id}')

        @self._bot.on.message(func=lambda m: m.text.endswith(CMD_TIMEZONE)\
                                    or m.text.startswith(('\N{globe with meridians}', CMD_TIMEZONE)))
        @B.Bot_Sender.except_log
        async def timezone_start_choice(message):
            """
            Обработка команды /timezone - спросить, что делаем
            """
            keyboard = None
            if user := await self._db_handler.get_user_info(message.peer_id, self._db_type):
                text = B.TZ_promt
                text += self._make_timezone_info(user)
                text += B.TZ_quest
                keyboard = Keyboard(inline=True)
                keyboard.add(Callback(B.Btn_change, payload={'cmd': BTN_TZ_CHANGE}))
                keyboard.add(Callback(B.Btn_nothing, payload={'cmd': BTN_CANCEL}))
            else:
                text = B.Error
            await message.answer(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                            rules.PayloadRule({"cmd": BTN_TZ_CHANGE}))
        @B.Bot_Sender.except_log
        async def timezone_change(event):
            """
            Обработка команды /timezone - запросить и ожидать ввод
            """
            message = (await self._bot.api.request('messages.getByConversationMessageId',\
                        {'peer_id': event.peer_id,
                        'conversation_message_ids':event.conversation_message_id})
                    )['response']['items'][0]
            text = message['text'][:message['text'].rindex('\n')]
            text += B.TZ_quest
            keyboard = Keyboard(inline=True)
            keyboard.add(Callback(B.Btn_undo,payload={'cmd': BTN_CANCEL}))
            # Запомнить пользователя
            self._user_inreract[event.peer_id] = {'type':1, 'msg':event.conversation_message_id}
            await event.edit_message(text, keyboard=keyboard)

        @self._bot.on.message(func=lambda m: m.text.endswith(CMD_MAILING)\
                                            or m.text.startswith(('\N{envelope}', CMD_MAILING)))
        @B.Bot_Sender.except_log
        async def mailing_start_choice(message):
            """
            Обработка команды /mailing - спросить, что делаем
            """
            text, keyboard = await self._make_mailing_choice(message.peer_id)
            if keyboard:
                text += B.Mailin_first_quest
            await message.answer(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                            rules.FuncRule(lambda m: m.payload.get('cmd') == BTN_ML_TURN_TO))
        @B.Bot_Sender.except_log
        async def mailing_turn(event):
            """
            Обработка команды /mailing - переключить и запросить дальнейшие действия
            """
            turn_to = True if event.payload['set']  == BTN_ON else False
            if await self._db_handler.set_user_mailing(event.peer_id, self._db_type, turn_to):
                text, keyboard = await self._make_mailing_choice(event.peer_id)
                text += B.Mailin_second_quest
            else:
                text = B.Error
                keyboard = None
            await event.edit_message(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                            rules.FuncRule(lambda m: m.payload.get('cmd') == BTN_ML_TIME_EDIT))
        @B.Bot_Sender.except_log
        async def mailing_edit_choice(event):
            """event.peer_id
            Обработка команды /mailing - запросить дальнейшие действия с рассылкой
            """
            message = (await self._bot.api.request('messages.getByConversationMessageId',\
                        {'peer_id': event.peer_id,
                        'conversation_message_ids':event.conversation_message_id})
                    )['response']['items'][0]
            text = message['text'][:message['text'].rindex('\n')]
            text += B.Mailing_time_first_quest.format(
                B.Mailing_time_next if event.payload['type'] == BTN_ML_TOMORROW else B.Mailing_time_now)
            keyboard = Keyboard(inline=True)
            user = await self._db_handler.get_user_info(event.peer_id, self._db_type)
            if user[event.payload['type']] is None:
                keyboard.add(Callback(B.Btn_on_time, payload={
                                'cmd': BTN_ML_TIME_SET,
                                'type': event.payload['type'],
                                'set': BTN_ON}))
            else:
                keyboard.add(Callback(B.Btn_chn_time,payload={
                                'cmd': BTN_ML_TIME_SET,
                                'type': event.payload['type'],
                                'set': BTN_ON}))
                keyboard.row()
                keyboard.add(Callback(B.Btn_off_time,payload={
                                'cmd': BTN_ML_TIME_SET,
                                'type': event.payload['type'],
                                'set': BTN_OFF}))
            keyboard.row()
            keyboard.add(Callback(B.Btn_back,payload={'cmd': BTN_ML_TIME_BACK}))
            await event.edit_message(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                            rules.PayloadRule({"cmd": BTN_ML_TIME_BACK}))
        @B.Bot_Sender.except_log
        async def mailing_return_to_start_choice(event):
            """
            Обработка команды /mailing - вернуться к главному меню
            """
            text, keyboard = await self._make_mailing_choice(event.peer_id)
            text += B.Mailin_first_quest
            await event.edit_message(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                            rules.FuncRule(lambda m: m.payload.get('cmd') == BTN_ML_TIME_SET\
                                                    and m.payload.get('set') == BTN_ON))
        @B.Bot_Sender.except_log
        async def mailing_time_change(event):
            """
            Обработка команды /mailing - запросить и ожидать ввод вермя рассылки
            """
            message = (await self._bot.api.request('messages.getByConversationMessageId',\
                        {'peer_id': event.peer_id,
                        'conversation_message_ids':event.conversation_message_id})
                    )['response']['items'][0]
            text = message['text'][:message['text'].rindex('\n')]
            text += B.Mailing_time_second_quest.format(
                B.Mailing_time_next if event.payload['type'] == BTN_ML_TOMORROW else B.Mailing_time_now)
            keyboard = Keyboard(inline=True)
            keyboard.add(Callback(B.Btn_undo,payload={'cmd': BTN_CANCEL}))
            # Запомнить пользователя
            if event.payload['type'] == BTN_ML_TOMORROW:
                change_type = 4
            else:
                change_type = 3
            self._user_inreract[event.peer_id] = {'type':change_type, 'msg':event.conversation_message_id}
            await event.edit_message(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                            rules.FuncRule(lambda m: m.payload.get('cmd') == BTN_ML_TIME_SET\
                                                    and m.payload.get('set') == BTN_OFF))
        @B.Bot_Sender.except_log
        async def mailing_off_change(event):
            """
            Обработка команды /mailing - отключить рассылку и запросить дальнейшие действия
            """
            keyboard = None
            if event.payload['type'] == BTN_ML_TOMORROW:
                edit_func = self._db_handler.set_user_tomorrow_time
            else:
                edit_func = self._db_handler.set_user_today_time
            if await edit_func(event.peer_id, self._db_type, None):
                text, keyboard = await self._make_mailing_choice(event.peer_id)
                text += B.Mailin_second_quest
            else:
                text = B.Error
                keyboard = None
            await event.edit_message(text, keyboard=keyboard)

        @self._bot.on.raw_event(GroupEventType.MESSAGE_EVENT, MessageEvent,
                                rules.PayloadRule({"cmd": BTN_CANCEL}))
        @B.Bot_Sender.except_log
        async def editing_cancel_edit(event):
            """
            Обработка команды /mailing и /timezone - ничего не менять
            """
            message = (await self._bot.api.request('messages.getByConversationMessageId',\
                        {'peer_id': event.peer_id,
                        'conversation_message_ids':event.conversation_message_id})
                    )['response']['items'][0]
            if type(self._user_inreract.get(event.peer_id)) is dict:
                inter_type = self._user_inreract[event.peer_id]['type']
                self._user_inreract.pop(event.peer_id)
            else: inter_type = None
            # Отредактировать сообщение - удалить часть с вопросом и кнопки
            text = message['text'][:message['text'].rindex('\n')]
            await event.edit_message(text)
            # При старте спросить про рассылку
            if inter_type == 2:
                text, keyboard = await self._make_mailing_choice(event.peer_id)
                text = B.Secon_quest.format('\N{envelope}'+CMD_MAILING, text)
                await event.send_message(text, keyboard=keyboard)

        @self._bot.on.message()
        @B.Bot_Sender.except_log
        async def over_parse(message):
            """
            Обрабка всего прочего:
            - Проверка на текстовый ввод для /timezone и /mailing;
            - Все остальные случаи.
            """
            # Проверка на текстовый ввод для бота
            user_id = message.peer_id
            if type(self._user_inreract.get(user_id)) is dict:
                # Проверка на команду /timezone - записать часовой пояс
                if self._user_inreract[user_id]['type'] in (1, 2):
                    # Распознать число со знаком и проврить вхождение в интервал
                    tz_num = self._parse_tz(message.text)
                    if tz_num is not None:
                        # Убрать кнопку отмены и очистить хранилище
                        if message.peer_id < 2000000000:
                            prev_m = (await self._bot.api.request('messages.getByConversationMessageId',
                                        {'peer_id': user_id,
                                        'conversation_message_ids':self._user_inreract[user_id]['msg']})
                                    )['response']['items'][0]
                            await self._bot.api.messages.edit(
                                peer_id=user_id,
                                message=prev_m['text'],
                                message_id=prev_m['id'],
                                keyboard=None)
                        inter_type = self._user_inreract[user_id]['type']
                        self._user_inreract.pop(user_id)
                        # Привести ЧП к UTC из МСК и записать результаты в БД
                        timezone = tz_num + 3
                        res = await self._db_handler.set_user_timezone(user_id, self._db_type, timezone)
                        user = await self._db_handler.get_user_info(user_id, self._db_type)
                        text = B.TZ_finish
                        text += self._make_timezone_info(user)
                        await message.answer(text)
                        # При старте спросить про рассылку
                        if res and inter_type == 2:
                            text, keyboard = await self._make_mailing_choice(user_id)
                            text = B.Secon_quest.format('\N{envelope}'+CMD_MAILING, text)
                            await message.answer(text, keyboard=keyboard)
                    else:
                        text = B.TZ_warning
                        await message.answer(text)
                # Проверка на команду /mailing - записать время рассылки
                elif self._user_inreract[user_id]['type'] in (3, 4):
                    time = self._parse_mailing_time(message.text)
                    if time is not None:
                        if message.peer_id < 2000000000:
                            prev_m = (await self._bot.api.request('messages.getByConversationMessageId',
                                        {'peer_id': user_id,
                                        'conversation_message_ids':self._user_inreract[user_id]['msg']})
                                    )['response']['items'][0]
                            await self._bot.api.messages.edit(
                                peer_id=user_id,
                                message=prev_m['text'],
                                message_id=prev_m['id'],
                                keyboard=None)
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
                        await message.answer(text, keyboard=keyboard)
                    else:
                        text = B.Mailing_time_warning
                        await message.answer(text)
            # Все остальные случаи в личных чатах (не группах)
            elif user_id < 2000000000:
                text = B.Unknown
                await message.reply(text)

    def poll(self):
        """
        Вернуть асинхронную функцию бесконечного опроса бота
        """
        async def run_polling():
            async for event in self._bot.polling.listen():
                for update in event["updates"]:
                    await self._bot.router.route(update, self. _bot.polling.api)
        return run_polling()

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
                if limit_count == 20:
                    await sleep(1)
                    limit_count = 0
                text = (await text_func(user, day_type)).replace('_','').replace('*','')
                await self._bot.api.messages.send(peer_ids=user['id'], random_id=0, message=text)
                self._logger.debug(f'Send Slovo in {day} mailing of VK user {user['id']}')
                limit_count += 1

    def _add_menu_buttons(self, keyboard):
        keyboard.add(Text('\N{HOURGLASS}'+CMD_YESTERDAY))
        keyboard.add(Text('\N{calendar}'+CMD_TODAY))
        keyboard.add(Text('\N{Crystal Ball}'+CMD_TOMORROW))
        keyboard.row()
        keyboard.add(Text('\N{globe with meridians}'+CMD_TIMEZONE))
        keyboard.row()
        keyboard.add(Text('\N{envelope}'+CMD_MAILING))
        keyboard.row()
        keyboard.add(Text('\N{Circled Information Source}'+CMD_HELP))

    async def _make_mailing_choice(self, user_id):
            """
            Обработка команды /mailing - собрать главное меню для отображения
            """
            text: str
            keyboard = None
            if user := await self._db_handler.get_user_info(user_id, self._db_type):
                text = B.Mailing_info + self._make_timezone_info(user) + '\n' + self._make_mailing_info(user)
                keyboard = Keyboard(inline=True)
                if user['mailing'] != 1:
                    keyboard.add(Callback(B.Btn_on, payload={'cmd': BTN_ML_TURN_TO, 'set': BTN_ON}))
                else:
                    keyboard.add(Callback(B.Btn_td_time, payload={'cmd': BTN_ML_TIME_EDIT, 'type': BTN_ML_TODAY}))
                    keyboard.row()
                    keyboard.add(Callback(B.Btn_tm_time, payload={'cmd': BTN_ML_TIME_EDIT, 'type': BTN_ML_TOMORROW}))
                    keyboard.row()
                    keyboard.add(Callback(B.Btn_off, payload={'cmd': BTN_ML_TURN_TO, 'set': BTN_OFF}))
                keyboard.row()
                keyboard.add(Callback(B.Btn_nothing, payload={'cmd': BTN_CANCEL}))
            else:
                text = B.Error
            return text, keyboard