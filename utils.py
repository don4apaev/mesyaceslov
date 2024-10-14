from datetime import date
from dateutil import easter
import asyncio

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
    # Получить Пасху
    f_easter = easter.easter(cur_year, easter.EASTER_ORTHODOX)
    # Определить пост
    if day_date < date(year=cur_year,month=1,day=7):
        # Рождественский пост
        return 2
    elif (f_easter - day_date).days in range(1, 49):
        # Великий Пост
        return 3
    elif (day_date - f_easter).days > 56 and day_date < date(year=cur_year,month=7,day=13):
        # Апостольский пост
        return 4
    elif day_date > date(year=cur_year,month=8,day=13) and\
            day_date < date(year=cur_year,month=8,day=28):
        # Успенский пост
        return 5
    elif day_date > date(year=cur_year,month=11,day=27):
        # Рождественский пост
        return 2
    elif day_date == date(year=cur_year,month=1,day=18):
        # Крещенский сочельник
        return 6
    elif day_date == date(year=cur_year,month=9,day=11):
        # Усекновение главы Иоанна Предтечи
        return 7
    elif day_date == date(year=cur_year,month=9,day=27):
        # Воздвижение Креста Господня
        return 8
    elif day_date == f_easter:
        # Пасха
        return -1
    elif day_date == date(year=cur_year,month=1,day=7):
        # Рождество
        return -2
    elif day_date > date(year=cur_year,month=1,day=6) and\
            day_date < date(year=cur_year,month=1,day=18):
        # Святки
        return -3
    elif (f_easter - day_date).days in range(63, 70):
        #  Седьмица мытаря и фарисея
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
    elif day_date.isoweekday() == 3:
        # Однодневные на неделе
        return 1
    elif day_date.isoweekday() == 5:
        # Однодневные на неделе
        return 10
    else:
        # Нет поста - скоромный день?
        return 0

def get_crowning(day_date: date, cur_year: int) -> int:
    if day_date.isoweekday() in (2, 4, 6):
        # Вторник, четверг и суббота
        return 0
    fasting = get_fasting(day_date, cur_year)
    if fasting in (-7, -4):
        # Сырная, троицкая седмицы и святки
        return 2
    elif fasting in (-1, -6, -5, -3):
        # Пасха, Светлая, Сырная седьмицы и Святки
        return 0
    elif fasting in range(2, 6):
        # Многодневные посты
        return 0
    if day_date == date(year=cur_year,month=9,day=10) or\
            fasting == 7:
        # канун и Обрезание Спасителя по плоти
        return 0
    elif day_date == date(year=cur_year,month=9,day=26) or\
            fasting == 8:
        # канун и Воздвижение Креста Господня
        return 0
    elif day_date == date(year=cur_year,month=1,day=13) or\
            day_date == date(year=cur_year,month=1,day=13):
        # канун Воздвижения Креста Господня
        return 0
    elif fasting == 6:
        # канун Крещения
        return 0
    elif day_date == date(year=cur_year,month=1,day=19):
        # Крещение
        return 2
    elif day_date == date(year=cur_year,month=9,day=20):
        # канун Рождества Богородицы
        return 0
    elif day_date == date(year=cur_year,month=9,day=21):
        # Рождество Богородицы
        return 2
    elif day_date == date(year=cur_year,month=12,day=20):
        # канун Рождества Богородицы
        return 0
    elif day_date == date(year=cur_year,month=12,day=21):
        # Рождество Богородицы
        return 2
    elif day_date == date(year=cur_year,month=2,day=14):
        # канун Сретения Господня
        return 0
    elif day_date == date(year=cur_year,month=2,day=15):
        # Сретение Господне
        return 2
    elif day_date == date(year=cur_year,month=8,day=28):
        # Успение Богородицы
        return 2
    # Получить Пасху
    f_easter = easter.easter(cur_year, easter.EASTER_ORTHODOX)
    if (day_date - f_easter).days in (38, 48):
        # Кануны Вознесения, Троицы
        return 0
    elif (day_date - f_easter).days in (39, 49):
        # Вознесение, Троица
        return 2
    return 1

async def schedule_in(secs, coro, ):
    print('SCHED', secs)
    await asyncio.sleep(secs)
    return await coro