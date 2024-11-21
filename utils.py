from datetime import date, timedelta
from dateutil import easter
import asyncio
from enum import Enum


class Days(Enum):
    YESTERDAY = -1
    TODAY = 0
    TOMMOROW = 1
    ERROR = 2

class MesyaceslovError(Exception):
    pass

class ZeroInDate(MesyaceslovError):
    pass

class XMLCalendarError(MesyaceslovError):
    pass

class DateDBError(MesyaceslovError):
    pass

DB_MS_NAME = 'mesyaceslov.db'
DB_US_NAME = 'users.db'

def get_fasting(day_date: date, cur_year: int) -> int:
    '''
    Узнать, выпадает ли день на многодневный или однодневный пост.
    '''
    # Получить Пасху
    f_easter = easter.easter(cur_year, easter.EASTER_ORTHODOX)
    # Определить пост
    if day_date < date(year=cur_year,month=1,day=2):
        # усиленный Рождественский пост
        return 8
    elif day_date > date(year=cur_year,month=1,day=1) and\
            day_date < date(year=cur_year,month=1,day=7):
        # предпраздненство Рождества
        return 9
    elif (f_easter - day_date).days in range(42, 49):
        # Великий Пост, первая седмица
        return 1
    elif (f_easter - day_date).days in range(35, 42):
        # Великий Пост, вторая-пятая седмицы
        return 2
    elif (f_easter - day_date).days in range(7, 14):
        # Великий Пост, вербная седмицы
        return 3
    elif (f_easter - day_date).days in range(1, 7):
        # Великий Пост, страстная седмица
        return 4
    elif (day_date - f_easter).days > 56 and day_date < date(year=cur_year,month=7,day=13):
        # Апостольский пост
        return 5
    elif day_date > date(year=cur_year,month=8,day=13) and\
            day_date < date(year=cur_year,month=8,day=28):
        # Успенский пост
        return 6
    elif day_date > date(year=cur_year,month=11,day=27) and\
            day_date < date(year=cur_year,month=12,day=20):
        # Рождественский пост
        return 7
    elif day_date > date(year=cur_year,month=12,day=19):
        # усиленный Рождественский пост
        return 8
    elif day_date == date(year=cur_year,month=1,day=18):
        # Крещенский сочельник
        return 10
    elif day_date == date(year=cur_year,month=9,day=11):
        # Усекновение главы Иоанна Предтечи
        return 11
    elif day_date == date(year=cur_year,month=9,day=27):
        # Воздвижение Креста Господня
        return 12
    elif (day_date - f_easter).days > 7 and\
            (day_date - f_easter).days < 50:
        # Весенний мясоед
        return -1
    elif day_date > date(year=cur_year,month=1,day=6) and\
            day_date < date(year=cur_year,month=1,day=18):
        # Святки
        return -2
    elif (f_easter - day_date).days in range(63, 70):
        #  Седьмица мытаря и фарисея
        return -3
    elif (f_easter - day_date).days in range(63, 70):
        #  Седьмица о блудном сыне
        return -4
    elif (f_easter - day_date).days in range(49, 56):
        # Сырная седьмица
        return -5
    elif (day_date - f_easter).days in range(1, 8):
        # Светлая седьмица
        return -6
    elif (day_date - f_easter).days in range(50, 57):
        # Троицкая седьмица
        return -7
    else:
        # Нет поста
        return 0

def get_holyday(day_date: date, cur_year: int) -> int:
    '''
    Узнать, выпадает ли день на Пасху или Великие праздники
    '''
    # Получить Пасху
    f_easter = easter.easter(cur_year, easter.EASTER_ORTHODOX)
    if day_date == f_easter:
        # Пасха
        return 1
    elif day_date == date(year=cur_year,month=1,day=7):
        # Рождество
        return 2
    elif day_date == date(year=cur_year,month=1,day=19):
        # Крещение Господне
        return 3
    elif day_date == date(year=cur_year,month=8,day=19):
        # Преображение Господне
        return 4
    elif day_date == date(year=cur_year,month=9,day=27):
        # Воздвижение Креста Господня
        return 5
    elif (f_easter - day_date).days == 7:
        # Вход Господень в Иерусалим
        return 6
    elif (day_date - f_easter).days == 39:
        # Вознесение Господне
        return 7
    elif (day_date - f_easter).days == 49:
        # Пятидесятница (День Святой Троицы)
        return 8
    elif day_date == date(year=cur_year,month=9,day=21):
        # Рождество Пресвятой Богородицы
        return 9
    elif day_date == date(year=cur_year,month=12,day=4):
        # Введение во Храм Пресвятой Богородицы
        return 10
    elif day_date == date(year=cur_year,month=4,day=7):
        # Благовещение Пресвятой Богородицы
        return 11
    elif day_date == date(year=cur_year,month=2,day=15):
        # Сретение Господне
        return 12
    elif day_date == date(year=cur_year,month=8,day=28):
        # Успение Пресвятой Богородицы
        return 13
    elif day_date == date(year=cur_year,month=10,day=14):
        # Покров Пресвятой Богородицы
        return 14
    elif day_date == date(year=cur_year,month=1,day=14):
        # Обрезание Спасителя по плоти
        return 15
    elif day_date == date(year=cur_year,month=7,day=7):
        # Рождество Иоанна Крестителя
        return 16
    elif day_date == date(year=cur_year,month=7,day=12):
        # Память свв. Апостолов Петра и Павла
        return 17
    elif day_date == date(year=cur_year,month=9,day=11):
        # Усекновение главы Иоанна Крестителя
        return 18
    else:
        # Нет праздников
        return 0

def get_fasting_type(day_date: date, cur_year: int) -> int:
    '''
    Степени поста:
        0 - без поста
        1 - без мяса
        2 - рыба
        3 - с маслом
        4 - без масла
        5 - сухоядение
        6 - воздержание
    '''
    fasting = get_fasting(day_date, cur_year)
    holyday = get_holyday(day_date, cur_year)
    if fasting == 1:
        if day_date.isoweekday() in (1, 2):
            return 6
        elif day_date.isoweekday() in (3, 4, 5):
            return 5
        else:
            return 3
    elif fasting == 2:
        if holyday == 11:
            return 2
        if day_date.isoweekday() in (1, 3, 5):
            return 5
        elif day_date.isoweekday() in (2, 4):
            return 4
        else:
            return 3
    elif fasting == 3:
        if holyday == 11 or day_date.isoweekday() == 7:
            return 2
        if day_date.isoweekday() in (3, 5):
            return 5
        elif day_date.isoweekday() in (1, 2, 4):
            return 4
        else:
            return 3
    elif fasting == 4:
        if day_date.isoweekday() == 5:
            return 6
        if day_date.isoweekday() == 3:
            return 5
        elif day_date.isoweekday() in (1, 2, 4):
            return 4
        else:
            return 3
    elif fasting == 5:
        if day_date == date(year=cur_year,month=7,day=12):
            if day_date.isoweekday() in (3, 5):
                return 2
            else:
                return 0
        if day_date.isoweekday() in (1, 3, 5):
            return 4
        elif day_date.isoweekday() in (2, 4):
            return 3
        else:
            return 2
    elif fasting == 6:
        if day_date == date(year=cur_year,month=8,day=28):
            if day_date.isoweekday() in (3, 5):
                return 2
            else:
                return 0
        if holyday == 4:
            return 2
        elif day_date.isoweekday() in (1, 3, 5):
            return 5
        elif day_date.isoweekday() in (2, 4):
            return 4
        else:
            return 3
    elif fasting == 7:
        if holyday:
            return 2
        elif day_date.isoweekday() in (1, 3, 5):
            return 3
        else:
            return 2
    elif fasting == 8:
        if holyday:
            return 2
        elif day_date.isoweekday() in (1, 3, 5):
            return 4
        elif day_date.isoweekday() in (2, 4):
            return 3
        else:
            return 2
    elif fasting == 9:
        if day_date.isoweekday() in (1, 3, 5):
            return 5
        elif day_date.isoweekday() in (2, 4):
            return 4
        else:
            return 3
    elif fasting in (10, 11, 12):
        return 3
    elif fasting == -1:
        if day_date.isoweekday() in (3, 5):
            return 2
        else:
            return 0
    elif fasting == -5:
        return 1
    elif fasting in (-2, -3, -6, -7):
        return 0
    elif day_date.isoweekday() in (3, 5):
        if holyday:
            return 2
        else:
            return 4
    else:
        return 0

def get_crowning(day_date: date, cur_year: int) -> int:
    '''
    0 - венчание не совершается
    1 - венчание возможно
    2 - венчание не желательно
    '''
    if day_date.isoweekday() in (2, 4, 6):
        # Вторник, четверг и суббота
        return 0
    fasting = get_fasting(day_date, cur_year)
    eve_fasting = get_fasting(day_date+timedelta(days=1), cur_year)
    holyday = get_holyday(day_date, cur_year)
    eve_holyday = get_holyday(day_date+timedelta(days=1), cur_year)
    if fasting > 0:
        # Во время многодневных и однодневных постов
        return 0
    elif eve_fasting in (11, 12):
        # На кануне строгих однодневных постов
        return 0
    elif holyday == 1 or eve_holyday:
        # Пасха или канун великих праздников
        return 0
    elif fasting in (-2, -5, -6):
        # Святки, Сырная, Светлая седьмицы
        return 0
    elif holyday:
        # Во время великих праздников
        return 2
    elif fasting in (-3, -4, -7):
        # Мытаря и фарисея, О блудном сыне, Троицкая седьмица
        return 2
    else:
        return 1
