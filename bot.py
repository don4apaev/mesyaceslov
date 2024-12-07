from vkbottle import VKAPIError
from telebot.asyncio_helper import ApiTelegramException
from aiosqlite import Error as aiosqliteError

Btn_as_is = "По умолчанию"
Btn_signs = "Приметы"
Btn_saints = "Поминаемые святые"
Btn_change = "Изменить"
Btn_nothing = "Ничего"
Btn_off = "Отключить всё"
Btn_on = "Включить"
Btn_td_time = "Рассылка на текущий день"
Btn_tm_time = "Рассылка на следующий день"
Btn_undo = "Отменить"
Btn_back = "Назад"
Btn_on_time = "Включить рассылку"
Btn_chn_time = "Изменить время"
Btn_off_time = "Отменить рассылку"

Error = 'Какая-то проблема с обновлением данных... Обратись к администратору или попробуй позже.'
Already = "Привет! Я тебя уже запомнил."
Unknown = "Извини, я пока могу реагировать только на определённые команды. Посмотри их в Меню."

Statistic = "Всего {} пользоватлей, из них {} пользуется рассылкой.\n"\
            "Всего {} групп, из них {} с включённой рассылкой."

Hello_to = "Привет. Я бот Месяцеслова.\n\n"\
            "Ты можешь узнать у меня, что говорит Месяцеслов о сегодняшнем дне ({}), "\
            "дне прошедшем ({}) и дне грядущем ({}).\n\n"\
            "Удачи тебе сегодня, завтра и всегда!"
First_quest = "Для определения твоей даты я использую информацию о часовом поясе. "\
                    "По умолчанию используется часовой пояс МСК.\nТы всегда можешь изменить "\
                    "его командой {}.\n\n"\
                    "Пришли мне свой часовой пояс в целых часах относительно Москвы:"
Secon_quest = 'Так же я могу делать рассылку с праздниками и приметами. Она редактирется '\
                'командой {}.\n{}\n\nХочешь что-нибудь получать?'

Help = "Привет!\nЯ бот Месяцеслова. Я могу сообщить о дне всё согласно Месяцеслову: пост "\
            "и его степень, допустимость венчания, церковнеые праздники, народное название дня, "\
            "приметы и пословицы.\n\n"\
            "Ты можешь использовать команды {}, {} и {}, чтобы "\
            "получить информацию о прошедшем, текущем и грядущем днях соответстввенно.\n\n"\
            "Так же я дважды в сутки осуществляю рассылку с церковными праздниках на текущий день и "\
            "приметами на следующий день. Управлять рассылкой можно командой {}.\n\n"\
            "Расчёт твой текущей даты и времени осуществляется с учётом часового пояса. Изменяется он "\
            "командой {}."

Day_quest = "Что бы ты хотел узнать?"

TZ_info = '\N{globe with meridians} Твой часовой пояс - МСК{}.'
TZ_quest = '\n\nЧто мне сдалать?'
TZ_promt =  'Часовой пояс используется для определения твоей текущей даты, так как мы можем '\
                'быть на разных сторонах Земли.\n\n'
TZ_quest = "\nПришли мне свой часовой пояс в целых часах относительно Москвы:"
TZ_finish = 'Готово!\n\n'
TZ_warning = "Часовой пояс должен быть целочисленным и в пределах от -15 до +9"

Mailin_first_quest = '\n\nЧто редактируем?'
Mailin_second_quest = '\n\nЧто ещё изменить?'
Mailing_time_first_quest = '\nРедактируем рассылку на {} день:'
Mailing_time_next = 'следующий'
Mailing_time_now = 'текущий'
Mailing_time_second_quest = "\nПришли мне время рассылки на {} день в твоём часовом поясе 24-часовом формате:"
Mailing_time_warning = "Время рассылки должно быть целочисленным и в пределах от 0 до 23"

Mailing_info =  'Рассылка осуществляется дважды в сутки: я передаю информацию о '\
                'церковных праздниках на текущий день и приметы на следующий день.\n\n'
Mailing_info_off = "\N{envelope} Рассылка отключена."
Mailing_info_on = "\N{envelope} Рассылка включена;\n\N{calendar} Рассылка на сегодня {};"\
                    "\n\N{Crystal Ball} Рассылка на завтра {}."
Mailing_info_time_off = "не назначена"
Mailing_info_time_on = "в {} час{}"

class Bot_Sender:
    @property
    def db_type(self):
        return self._db_type

    def __init__(self, db_handler, ms_producer, logger):
        self._db_type = None
        self._db_handler = db_handler
        self._ms_producer = ms_producer
        self._logger = logger
        self._user_inreract = {}

    def _make_mailing_info(self, user: dict) -> str:
        """
        Напечатать информацию о настройках рассылки
        """
        # Получаем статус
        if user['mailing'] != 1:
            text = Mailing_info_off
        else:
            tz = user['timezone']
            if user['today'] is not None:
                time = (user['today'] + tz)%24
                td = Mailing_info_time_on.format(time, self._hours_ending(time))
            else:
                td = Mailing_info_time_off
            if user['tomorrow'] is not None:
                time = (user['tomorrow'] + tz)%24
                tm = Mailing_info_time_on.format(time, self._hours_ending(time))
            else:
                tm = Mailing_info_time_off
            text = Mailing_info_on.format(td, tm)
        return text

    def _make_timezone_info(self, user: dict) -> str:
        """
        Напечатать информацию о часовом поясе относительно МСК
        """
        # Часовой пояс к МСК
        timezone = user['timezone'] - 3
        if timezone < 0:    tz = f'{timezone}'
        elif timezone > 0:  tz = f'+{timezone}'
        else:               tz = ''
        return TZ_info.format(tz)

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

    def except_log(func):
        async def wrapper(self, *args, **kwargs):
            ret = None
            try:
                await func(self, *args, **kwargs)
            except ApiTelegramException as e:
                self._logger.warning(f'Exception in Telegram API in <{func.__name__}>\n\t"{e}"')
            except VKAPIError as e:
                self._logger.warning(f'Exception in VK API in <{func.__name__}>\n\t"{e}"')
            except aiosqliteError as e:
                self._logger.error(f'Exception in DB in <{func.__name__}>\n\t"{e}"')
            except Exception as e:
                self._logger.error(f'Some undefined exception in <{func.__name__}>\n\t"{e}"')
        return wrapper