import aiofiles
from datetime import datetime, timedelta, timezone

from utils import ZeroInDate, Days

Cyril_numbers = {
    1: 'а',
    2: 'в',
    3: 'г',
    4: 'д',
    5: 'е',
    6: 'ѕ',
    7: 'з',
    8: 'ѳ',
    9: 'и',
    10: 'і',
    20: 'к',
    30: 'л',
}

Mesyacy = {
    1: "января",
    2: "февраля",
    3: "марта",
    4: "апреля",
    5: "мая",
    6: "июня",
    7: "июля",
    8: "августа",
    9: "сентября",
    10: "октября",
    11: "ноября",
    12: "декабря",
}

Dni = {
    1 : 'Выходной',
    2 : 'Сокращённый рабочий',
    3 : 'Рабочий',
}

Posty = {
    1:  'Мясопуст, воздержание от мяса',
    2:  'Постный день, разрешена рыба',
    3:  'Постный день, разрешена горячая пища с маслом',
    4:  'Постный день, разрешена горячая пища без масла',
    5:  'Постный день, сухоядение',
    6:  'Постный день, рекомендуется воздержание от пищи',
}

Znaki = {
    0 : '\N{EIGHT POINTED BLACK STAR}',
    1 : '\N{circled cross pommee}',
    2 : '\N{cross pommee with half-circle below}',
    3 : '\N{cross pommee}',
    4 : '\N{notched left semicircle with three dots}',
    5 : '\N{notched right semicircle with three dots}',
    6 : '\N{BLACK CIRCLE}',
}

Error = "Друг, у меня какие-то проблемы... Обратись к администратору."

class MS_producer:
    def __init__(self, db_handler, logger):
        self._db_handler = db_handler
        self._logger = logger

    def _arab_to_cyril(self, number: int) -> str:
        cyr_number = ''
        dec = number//10
        un = number%10
        if un == 0:
            if dec == 0:
                raise ZeroInDate
            cyr_number = f'{Cyril_numbers[dec*10]}{u'\u0483'}'
        else:
            if dec == 1:
                cyr_number = f'{Cyril_numbers[un]}{u'\u0483'}{Cyril_numbers[dec*10]}'
            elif dec > 1:
                cyr_number = f'{Cyril_numbers[dec*10]}{u'\u0483'}{Cyril_numbers[un]}'
            else:
                cyr_number = f'{Cyril_numbers[un]}{u'\u0483'}'
        return cyr_number

    def _creation_year(self, date) -> int:
        sept_new_year = datetime(day=13, month=9, year=date.year).date()
        creation = 5508
        if(date>sept_new_year):
            creation += 1
        return date.year + creation

    async def make_holy(self, user: dict, day: Days) -> str:
        slovo: str
        # Формируем дату
        if day == Days.TODAY:
            slovo = 'Сегодня '
            date = datetime.now(timezone(timedelta(hours=user['timezone']))).date()
        elif day == Days.TOMMOROW:
            slovo = 'Завтра '
            date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() + timedelta(days=1)
        elif day == Days.YESTERDAY:
            slovo = 'Вчера было '
            date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() - timedelta(days=1)
        else:
            return Error
        # Получаем данные о дне из БД
        if ( day_info := await self._db_handler.get_day_values(date) ) is None:
            return Error
        name, work, fasting, crowning, holy = day_info
        # Получаем поминаемых святых и иконы  из БД
        if ( saints_list := await self._db_handler.get_saints(date) ) is None:
            return Error
        # Заполняем дату
        old_date = date - timedelta(days=(date.year//100 - date.year//400 - 2))
        slovo += f'*{self._arab_to_cyril(date.day)} {Mesyacy[date.month]} '\
                    f'{self._creation_year(date)} г.* от сотворения мира.'
        # Заполняем пост
        if fasting := Posty.get(fasting) :
            slovo += f' {fasting}.'
        slovo += '\n'
        # Заполняем Великие праздники
        if holy:
            name, sign, _, _ = get_saint(holy)
            slovo += f'\nВеликий праздник - {Znaki[sign]} {name}!\n'
        # Отделяем дни поминования от икон
        saint_slovo = ''
        icon_slovo = ''
        for holy in saints_list:
            _, s_name, s_sign = holy
            if s_sign == 0:
                icon_slovo += '\n' + Znaki[s_sign] + ' ' + s_name
            elif s_sign is None:
                saint_slovo += '\n' + Znaki[6] + ' ' + s_name
            elif s_sign != 1:
                saint_slovo += '\n' + Znaki[s_sign] + ' ' + s_name
        if len(saint_slovo):
            slovo += '\nДень памяти:' + saint_slovo
        if len(icon_slovo):
            slovo += '\n\nПрославляются иконы Божей Матери:'  + icon_slovo
        # Получаем притчу или житие
        # with open(f'signs/{date.month}/{date.day}.md', 'r') as sign:
        #     for line in sign.readlines():
        #         slovo += line
        return slovo

    async def make_sign(self, user: dict, day: Days) -> str:
        slovo: str
        # Формируем дату
        if day == Days.TODAY:
            slovo = 'Сегодня - '
            date = datetime.now(timezone(timedelta(hours=user['timezone']))).date()
        elif day == Days.TOMMOROW:
            slovo = 'Завтра - '
            date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() + timedelta(days=1)
        elif day == Days.YESTERDAY:
            slovo = 'Истёк день рекомый '
            date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() - timedelta(days=1)
        else:
            return Error
        # Получаем данные о дне из БД
        if ( day_info := await self._db_handler.get_day_values(date) ) is None:
            return Error
        name, work, fasting, crowning, _ = day_info
        # Заполняем название
        slovo += f'*{name}*. {Dni[work]} день, '
        # Заполняем пост
        if fasting > 0:
            slovo += 'постный'
        else:
            slovo += 'поста нет'
        # Заполняем венчание
        if crowning == 0:
            slovo += ', браковенчание не совершается.'
        elif crowning == 2:
            slovo += ', венчание нежелательно.'
        else:
            slovo += '.'
        slovo += '\n\n'
        # Получаем приметы
        try:
            async with aiofiles.open(f'signs/{date.month}/{date.day}.md', 'r') as sign:
                async for line in sign:
                    slovo += line
        except FileNotFoundError:
            self._logger.error(f'Can\'t find  Slovo for  {date.day}.{date.month}')
            return Error
        except Exception as e:
            self._logger.error(f'Some exception while get Slovo for  {date.day}.{date.month}\n'\
                                f'\t{e} on {e.__traceback__.tb_lineno}')
            return Error
        return slovo
