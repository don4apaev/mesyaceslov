from datetime import datetime, timedelta, timezone

from utils import ZeroInDate

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
    1 : '\N{circled cross pommee}',
    2 : '\N{cross pommee with half-circle below}',
    3 : '\N{cross pommee}',
    4 : '\N{notched left semicircle with three dots}',
    5 : '\N{notched right semicircle with three dots}',
}

class MS_producer:
    def __init__(self, db_handler):
        self._db_handler = db_handler

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

    def make_today(self, user: dict) -> str:
        slovo = 'Сегодня '
        # Формируем дату
        date = datetime.now(timezone(timedelta(hours=user['timezone']))).date()
        old_date = date - timedelta(days=(date.year//100 - date.year//400 - 2))
        # Получаем данные о дне из БД
        name, work, fasting, crowning, holy = self._db_handler.get_day_values(date)
        # Заполняем дату
        slovo += f'{date.day}[{self._arab_to_cyril(date.day)}] {Mesyacy[date.month]} '\
        f'({old_date.day}[{self._arab_to_cyril(old_date.day)}] {Mesyacy[old_date.month]} cт.ст.) '\
        f'{self._creation_year(date)} г. от сотворения мира.'
        # Заполняем пост
        if fasting := Posty.get(fasting) :
            slovo += f' {fasting}.\n'
        else:
            slovo += '\n'
        # Заполняем Великие праздники
        if holy:
            name, sign = get_saint(holy)
            slovo += f'Сегодня Великий праздник - {name}!\n'
        # Получаем поминаемых святых и иконы
        holy_list = self._db_handler.get_saints(date)
        saint_slovo = 'Сегодня день памяти: '
        saint_count = 0
        icon_slovo = 'Сегодня прославляются иконы Божей Матери: '
        icon_count = 0
        # Отделяем дни поминования от икон
        for holy in holy_list:
            s_id, s_name, s_sign = holy
            if s_sign == 0:
                icon_slovo += s_name + ' · '
                icon_count += 1
            elif s_sign != 1:
                # tipicon 1F540-1F544
                if s_sign:
                    saint_slovo += Znaki[s_sign]
                saint_slovo += s_name + ' · '
                saint_count += 1
        if saint_count:
            saint_slovo = saint_slovo[:-3]
            slovo += saint_slovo + '.\n'
        if icon_count:
            icon_slovo = icon_slovo[:-3]
            slovo += icon_slovo + '.\n'
        # Получаем притчу или житие
        # with open(f'signs/{date.month}/{date.day}.txt', 'r') as sign:
        #     for line in sign.readlines():
        #         slovo += line
        return slovo

    def make_tomorrow(self, user: dict) -> str:
        slovo = 'Завтра '
        # Формируем дату
        date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() + timedelta(days=1)
        # Получаем данные о дне из БД
        name, work, fasting, crowning, holy = self._db_handler.get_day_values(date)
        # Заполняем название
        slovo += f'{name}. {Dni[work]} день, '
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
        slovo += '\n'
        # Получаем приметы
        try:
            with open(f'signs/{date.month}/{date.day}.txt', 'r') as sign:
                for line in sign.readlines():
                    slovo += line
        except FileNotFoundError:
            pass
        return slovo
