from datetime import datetime, timedelta, timezone
from dateutil import easter
from utils import cyril_numbers, mesyacy
def arab_to_cyril(number: int) -> str:
    cyr_number = ''
    dec = number//10
    un = number%10
    if un == 0:
        if dec == 0:
            raise utils.ZeroInDate
        cyr_number = f'{cyril_numbers[dec*10]}{u'\u0483'}'
    else:
        if dec == 1:
            cyr_number = f'{cyril_numbers[un]}{u'\u0483'}{cyril_numbers[dec*10]}'
        elif dec > 1:
            cyr_number = f'{cyril_numbers[dec*10]}{u'\u0483'}{cyril_numbers[un]}'
        else:
            cyr_number = f'{cyril_numbers[un]}{u'\u0483'}'
    return cyr_number

def make_today_slovo(user: dict, database) -> str:
    slovo = 'Сегодня '
    # Формируем дату
    date = datetime.now(timezone(timedelta(hours=user['timezone']))).date()
    old_date = date - timedelta(days=(date.year//100 - date.year//400 - 2))
    slovo += f'{date.day}[{arab_to_cyril(date.day)}] {mesyacy[date.month]} '\
    f'({old_date.day}[{arab_to_cyril(old_date.day)}] {mesyacy[old_date.month]} cт.ст.)'
    # Получаем данные из БД
    name, work, fasting, crowning, holy = database.get_day_values(date)
    # Пост
    if fasting == 2:
        slovo += ', Рожденственский пост. '
    elif fasting == 3:
        slovo += ', Великий пост. '
    elif fasting == 4:
        slovo += ', Апостольский пост. '
    elif fasting == 5:
        slovo += ', Успенский пост. '
    elif fasting == 6:
        slovo += ', Крещенский сочельник. '
    elif fasting == 7:
        slovo += ', пост в память Усекновения главы Иоанна Предтечи. '
    elif fasting == 8:
        slovo += ', пост в память Воздвижения Креста Господня. '
    elif fasting == -1:
        slovo += ', Светлое Христово Воскресение, Пасха! '
    elif fasting == -2:
        slovo += ', Рождество Христово! '
    elif fasting == -3:
        slovo += ', Святки. '
    elif fasting == -4:
        slovo += ', Седьмица мытаря и фарисея. '
    elif fasting == -5:
        slovo += ', Сырная седьмица. '
    elif fasting == -6:
        slovo += ', Светлая седьмица. '
    elif fasting == -7:
        slovo += ', Троицкая седьмица. '
    elif fasting == 1:
        slovo += ', пост в воспоминание предательства Иудой Христа. '
    elif fasting == 10:
        slovo += ', пост в память крестных страданий и смерти Спасителя. '
    # Поминаемых святых и праздники
    # Притчу или житие
    return slovo
    

def make_tomorrow_slovo(user: dict, database) -> str:
    slovo = 'Завтра '
    # Формируем дату
    date = datetime.now(timezone(timedelta(hours=user['timezone']))).date() + timedelta(days=1)
    # Получаем данные из БД
    name, work, fasting, crowning, holy = database.get_day_values(date)
    slovo += f'{name}. '
    # Вычисляем выходные дни
    if work == 1:
        slovo += 'Выходной, '
    elif work == 2:
        slovo += 'Сокращённый рабочий, '
    elif work == 3:
        slovo += 'Рабочий, '
    else:
        raise DateDBError('Wrong workday type.')
    # Вычисляем пост
    if fasting > 0:
        slovo += 'постный день'
    else:
        slovo += 'поста нет'
    # Венчание
    if crowning == 0:
        slovo += ', Браковенчание не совершается. '
    if crowning == 2:
        slovo += ', венчание нежелательно. '
    slovo += '\n'
    # Получаем приметы
    with open(f'signs/{date.month}/{date.day}.txt', 'r') as sign:
        for line in sign.readlines():
            slovo += line
    return slovo