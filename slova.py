from datetime import datetime, timedelta, timezone
from dateutil import easter
from utils import cyril_numbers, mesyacy, dni

def arab_to_cyril(number: int) -> str:
    cyr_number = ''
    dec = number//10
    un = number%10
    if un == 0:
        if dec == 0:
            raise utils.ZeroInDate
        cyr_number = f'{cyril_numbers[dec*10]}{u'\u0303'}'
    else:
        if dec == 1:
            cyr_number = f'{cyril_numbers[un]}{u'\u0303'}{cyril_numbers[dec*10]}'
        elif dec > 1:
            cyr_number = f'{cyril_numbers[dec*10]}{u'\u0303'}{cyril_numbers[un]}'
        else:
            cyr_number = f'{cyril_numbers[un]}{u'\u0303'}'
    return cyr_number

def creation_year(date) -> int:
    sept_new_year = datetime(day=13, month=9, year=date.year).date()
    creation = 5508
    if(date>sept_new_year):
        creation += 1
    return date.year + creation

def make_today_slovo(user: dict, database) -> str:
    slovo = 'Сегодня '
    # Формируем дату
    date = datetime.now(timezone(timedelta(hours=user['timezone']))).date()
    old_date = date - timedelta(days=(date.year//100 - date.year//400 - 2))
    slovo += f'{date.day}[{arab_to_cyril(date.day)}] {mesyacy[date.month]} '\
    f'({old_date.day}[{arab_to_cyril(old_date.day)}] {mesyacy[old_date.month]} cт.ст.) '\
    f'{creation_year(date)} г. от сотворения мира'
    # Получаем данные из БД
    name, work, fasting, crowning, holy = database.get_day_values(date)
    if fasting == 2:
        slovo += ', Рожденственский пост.'
    elif fasting == 3:
        slovo += ', Великий пост.'
    elif fasting == 4:
        slovo += ', Апостольский пост.'
    elif fasting == 5:
        slovo += ', Успенский пост.'
    elif fasting == 6:
        slovo += ', Крещенский сочельник.'
    elif fasting == 7:
        slovo += ', пост в память Усекновения главы Иоанна Предтечи.'
    elif fasting == 8:
        slovo += ', пост в память Воздвижения Креста Господня.'
    elif fasting == -1:
        slovo += ', Светлое Христово Воскресение, Пасха!'
    elif fasting == -2:
        slovo += ', Рождество Христово!'
    elif fasting == -3:
        slovo += ', Святки.'
    elif fasting == -4:
        slovo += ', Седьмица мытаря и фарисея.'
    elif fasting == -5:
        slovo += ', Сырная седьмица.'
    elif fasting == -6:
        slovo += ', Светлая седьмица.'
    elif fasting == -7:
        slovo += ', Троицкая седьмица.'
    elif fasting == 1:
        slovo += ', пост в воспоминание предательства Иудой Христа.'
    elif fasting == 10:
        slovo += ', пост в память крестных страданий и смерти Спасителя.'
    else:
        slovo += '.'
    slovo += '\n'
    # Поминаемых святых и праздники
    # Притчу или житие
    with open(f'signs/{date.month}/{date.day}.txt', 'r') as sign:
        for line in sign.readlines():
            slovo += line
    return slovo
    

def make_tomorrow_slovo(user: dict, database) -> str:
    slovo = 'Завтра '
    # Формируем дату
    date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() + timedelta(days=1)
    # Получаем данные из БД
    name, work, fasting, crowning, holy = database.get_day_values(date)
    slovo += f'{name}. {dni[work]} день, '
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