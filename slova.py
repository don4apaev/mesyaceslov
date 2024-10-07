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
    1:  'пост в воспоминание предательства Иудой Христа',
    10: 'пост в память крестных страданий и смерти Спасителя',
    2:  'Рожденственский пост',
    3:  'Великий пост',
    4:  'Апостольский пост',
    5:  'Успенский пост',
    6:  'Крещенский сочельник',
    7:  'пост в память Усекновения главы Иоанна Предтечи',
    8:  'пост в память Воздвижения Креста Господня',
    -1: 'Светлое Христово Воскресение, Пасха',
    -2: 'Рождество Христово',
    -3: 'Святки',
    -4: 'Седьмица мытаря и фарисея',
    -5: 'Сырная седьмица',
    -6: 'Светлая седьмица',
    -7: 'Троицкая седьмица',
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
        slovo += f'{date.day}[{self._arab_to_cyril(date.day)}] {Mesyacy[date.month]} '\
        f'({old_date.day}[{self._arab_to_cyril(old_date.day)}] {Mesyacy[old_date.month]} cт.ст.) '\
        f'{self._creation_year(date)} г. от сотворения мира'
        # Получаем данные из БД
        name, work, fasting, crowning, holy = self._db_handler.get_day_values(date)
        # Заполняем слово
        if fasting := Posty.get(fasting):
            slovo += f', {fasting}.'
        else:
            slovo += '.'
        slovo += '\n'
        # Поминаемых святых и праздники
        # if holy:
        #      "Сегодня празднуется "
        # tipicon 1F540-1F544
        # Притчу или житие
        with open(f'signs/{date.month}/{date.day}.txt', 'r') as sign:
            for line in sign.readlines():
                slovo += line
        return slovo

    def make_tomorrow(self, user: dict) -> str:
        slovo = 'Завтра '
        # Формируем дату
        date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() + timedelta(days=1)
        # Получаем данные из БД
        name, work, fasting, crowning, holy = self._db_handler.get_day_values(date)
        slovo += f'{name}. {Dni[work]} день, '
        if fasting > 0:
            slovo += 'постный, '
        else:
            slovo += 'поста нет, '
        if crowning == 0:
            slovo += 'Браковенчание не совершается.'
        if crowning == 2:
            slovo += 'венчание нежелательно.'
        slovo += '\n'
        # Получаем приметы
        with open(f'signs/{date.month}/{date.day}.txt', 'r') as sign:
            for line in sign.readlines():
                slovo += line
        return slovo