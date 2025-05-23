import aiosqlite
import aiohttp
import asyncio
from datetime import date, timedelta
import xml.etree.ElementTree as ET
from logging import Logger

from utils import get_fasting, get_fasting_type, get_crowning, get_g_holyday
from utils import DateDBError


class DB_handler:
    def __init__(self, db_name: str, logger: Logger):
        self.lock = asyncio.Lock()
        self.db_name = db_name
        self._logger = logger

    async def __aenter__(self):
        self.db = await aiosqlite.connect(self.db_name)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.db.close()


class User_DB_handler(DB_handler):
    async def add_user(self, user_id: int, bot_type: int) -> bool:
        async with self.lock:
            sql_req = "SELECT * FROM users WHERE id=? AND type=?"
            cursor = await self.db.execute(sql_req, (user_id, bot_type))
            user = await cursor.fetchone()
            if user:
                self._logger.debug(
                    f"Try to add already existin user {user_id} in {bot_type}"
                )
                return False
            sql_req = (
                "INSERT INTO users (id, type, admin, mailing, timezone, today, tomorrow) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)"
            )
            cursor = await self.db.execute(
                sql_req, (user_id, bot_type, False, None, 3, None, None)
            )
            await self.db.commit()
            self._logger.debug(f"New user {user_id} in {bot_type} addded to DB")
            return True

    async def get_user_info(self, user_id: int, bot_type: int) -> dict:
        async with self.lock:
            keys = ("id", "admin", "mailing", "timezone", "today", "tomorrow")
            sql_req = f"SELECT {','.join(keys)} FROM users WHERE id=? AND type=?"
            async with self.db.execute(sql_req, (user_id, bot_type)) as cursor:
                user = await cursor.fetchone()
                if not user:
                    return None
                return dict(zip(keys, user))

    async def _set_user_field(
        self, user_id: int, bot_type: int, field_name: str, field_value: bool | int
    ) -> bool:
        async with self.lock:
            sql_req = "SELECT * FROM users WHERE id=? AND type=?"
            cursor = await self.db.execute(sql_req, (user_id, bot_type))
            user = await cursor.fetchone()
            if not user:
                self._logger.error(f"No user {user_id} in {bot_type} in DB")
                return False
            sql_req = f"UPDATE users SET {field_name} = ? WHERE id=? AND type=?"
            await self.db.execute(sql_req, (field_value, user_id, bot_type))
            await self.db.commit()
            self._logger.debug(
                f"Update user {user_id} in {bot_type} {field_name} to {field_value}"
            )
            return True

    async def set_user_mailing(
        self, user_id: int, bot_type: int, mailing: bool
    ) -> bool:
        return await self._set_user_field(user_id, bot_type, "mailing", mailing)

    async def set_user_timezone(
        self, user_id: int, bot_type: int, timezone: int
    ) -> bool:
        return await self._set_user_field(user_id, bot_type, "timezone", timezone)

    async def set_user_today_time(
        self, user_id: int, bot_type: int, today_time: int
    ) -> bool:
        return await self._set_user_field(user_id, bot_type, "today", today_time)

    async def set_user_tomorrow_time(
        self, user_id: int, bot_type: int, tomorrow_time: int
    ) -> bool:
        return await self._set_user_field(user_id, bot_type, "tomorrow", tomorrow_time)

    async def _get_mailing_users(self, bot_type: int, mailing_type: str, hour_utc: int):
        async with self.lock:
            keys = (
                "id",
                "timezone",
            )
            sql_req = (
                f"SELECT {','.join(keys)} FROM users "
                f'WHERE type=? AND mailing=? AND {mailing_type}=?'
            )
            async with self.db.execute(sql_req, (bot_type, True, hour_utc)) as cursor:
                users = await cursor.fetchall()
                if len(users) == 0:
                    return tuple()
                return tuple(dict(zip(keys, user)) for user in users)

    async def get_today_mailing_users(self, bot_type: int, hour_utc: int):
        return await self._get_mailing_users(bot_type, "today", hour_utc)

    async def get_tomorrow_mailing_users(self, bot_type: int, hour_utc: int):
        return await self._get_mailing_users(bot_type, "tomorrow", hour_utc)

    async def get_users(self, bot_type: int) -> list:
        async with self.lock:
            keys = ("id", "mailing", "timezone", "today", "tomorrow")
            sql_req = f"SELECT {','.join(keys)} FROM users WHERE type=?"
            async with self.db.execute(sql_req, (bot_type,)) as cursor:
                users = await cursor.fetchall()
                if len(users) == 0:
                    return tuple()
                return tuple(dict(zip(keys, user)) for user in users)


class Days_DB_handler(DB_handler):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._limit = 5
        self._days_cache = {}
        self._saints_cache = {}
        
    async def __aenter__(self):
        await DB_handler.__aenter__(self)
        sql_req = "SELECT current FROM year"
        async with self.db.execute(sql_req) as cursor:
            self._table_year = (await cursor.fetchone())[0]

    async def fill_daytable(self):
        """
        Обновить данные в days
        """
        holydays = {}
        cur_year = self._table_year + 1
        try:
            # Обновить год в таблице
            sql_req = (
                "UPDATE year SET current = ? WHERE current=?"
            )
            await self.db.execute(sql_req, (cur_year, self._table_year))
            # Перенести последние 4 дня текущего года в пердыдущий
            sql_req = (
                "SELECT work, fasting, f_type, crowning, holy, day FROM days "
                "WHERE month=12 AND day > 27"
            )
            async with self.db.execute(sql_req) as cursor:
                old_days = await cursor.fetchall()
            sql_req = (
                "UPDATE days SET (work, fasting, f_type, crowning, holy) = "
                "(?, ?, ?, ?, ?) WHERE month=-1 AND day=?"
            )
            cursor = await self.db.executemany(sql_req, old_days)
            # Скачать и распаковать производственный календарь
            url = f"https://xmlcalendar.ru/data/ru/{cur_year}/calendar.xml"
            self._logger.debug(f"Download calendar from {url}")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    calendar = (await response.read()).decode()
            root = ET.fromstring(calendar)
            xmldays = root.find("days")
            for day in xmldays:
                # В XML теги <days>:
                #     d - дата в формате ММ.ДД.
                #     t - тип записи: см. workday_types
                #     h - ссылкой на идентификатор праздника из <holidays>.
                #     f - дата с которой был перенесен выходной день в формате ММ.ДД
                xml_date = day.get("d").split(".")
                holydays[int(xml_date[0]) * 100 + int(xml_date[1])] = int(day.get("t"))
                self._logger.debug(f"Get days: {holydays}")
            # Заполнить даты в календаре на год
            all_days = []
            iter_date = date(year=cur_year, month=1, day=1)
            while iter_date.year == cur_year:
                if not (day_type := holydays.get(iter_date.month * 100 + iter_date.day)):
                    day_type = 3 if iter_date.isoweekday() < 6 else 1
                fasting = get_fasting(iter_date, cur_year)
                f_type = get_fasting_type(iter_date, cur_year)
                crowning = get_crowning(iter_date, cur_year)
                g_holyday = get_g_holyday(iter_date, cur_year)
                all_days.append((
                    day_type, fasting, f_type, crowning,
                    g_holyday, iter_date.month, iter_date.day
                ))
                iter_date += timedelta(days=1)
            sql_req = (
                "UPDATE days SET (work, fasting, f_type, crowning, holy) = "
                "(?, ?, ?, ?, ?) WHERE month=? AND day=?"
            )
            cursor = await self.db.executemany(sql_req, all_days)
            # Обновить данные в saints
            # Обновить даты переходящих праздников
            # 1-18 - великие праздники
            # 104 - первое вск после 31 окт
            # 230 - ближайшее вск к 23 ноя
            # 485 - первое вскр после Р или пн, если Р в вскр
            # 561 - первая суб по Богоявлению
            # 653 - вскр: 7; до 7, если оно пн-ср; после 7, если чт-сб
            # 695 - 1 вскр после 11 фев
            # 761 - чтв Сырной седмицы
            # 769-803 - +/- 1 день в зависимости от високосности
            # 804 - сб 1 седмицы Великого поста
            # 805-821 - +/- 1 день в зависимости от високосности
            # 822,823,825-828 - ???
            # 845 - второе вскр Великого поста
            # 849 - второе вскр Великого поста
            # 933 - четвёртое вскр Великого поста
            # 966 - пятое вскр Великого поста
            # 996 - шетая субб Великого поста
            # 1057 - вторник Светлой седмицы
            # 1061 - вторник Светлой седмицы
            # 1062 - вторник Светлой седмицы
            # 1063 - вторник Светлой седмицы
            # 1068 - среда Светлой седмицы
            # 1077 - пятница Светлой седмицы
            # 1129 - 2 вскр после Пасхи
            # 1136 - 2 вскр после Пасхи
            # 1213 - 4 вскр после Пасхи
            # 1214 - 4 вскр после Пасхи
            # 1235 - 25 день по Пасхе
            # 1236 - 25 день по Пасхе
            # 1258 - 4 субб после Пасхи
            # 1338 - в день Вознесенья
            # 1360 - 1 вскр после или в 1 июня
            # 1361 - 6 вскр после Пасхи
            # 1362 - 6 вскр после Пасхи
            # 1384 - среда по Вознесении
            # 
            # 
            # 
        except Exception as e:
            self._logger.error(
                f"Some exception while updatiing days\n"
                f'\t"{e}" on {e.__traceback__.tb_lineno}'
            )
            return
        else:
            self._logger.info(f"days updated")
            await self.db.commit()

    async def get_day_values(self, day_date: date) -> tuple:
        if day_date in self._days_cache:
            return self._days_cache[day_date]
        try:
            sql_req = (
                "SELECT D.name, W.name, F.name, T.name, C.name, S.name "
                "FROM days AS D "
                "JOIN workday_types AS W ON W.id=D.work "
                "JOIN fasting_name AS F ON F.id=D.fasting "
                "JOIN fasting_type AS T ON T.id=D.f_type "
                "JOIN crowning_types AS C ON C.id=D.crowning "
                "JOIN saints AS S ON S.id=D.holy "
                "WHERE D.month=? AND D.day=?"
            )
            async with self.db.execute(
                sql_req, (self._month_conversion(day_date), day_date.day)
            ) as cursor:
                day = tuple(await cursor.fetchone())
                self._cache(day_date, day=day)
                return day
        except Exception as e:
            self._logger.error(
                f"Some exception while get {day_date} info from days\n"
                f'\t"{e}" on {e.__traceback__.tb_lineno}'
            )
            return None

    async def get_saints(self, day_date: date) -> tuple:
        if day_date in self._saints_cache:
            return self._saints_cache[day_date]
        try:
            sql_req = "SELECT id, name, sign FROM saints WHERE month=? AND day=?"
            async with self.db.execute(
                sql_req, (self._month_conversion(day_date), day_date.day)
            ) as cursor:
                saints = tuple(tuple(saint) for saint in (await cursor.fetchall()))
                self._cache(day_date, saints=saints)
                return saints
        except Exception as e:
            self._logger.error(
                f"Some exception while get {day_date} info from saints\n"
                f'\t"{e}" on {e.__traceback__.tb_lineno}'
            )
            return tuple()

    async def get_saint(self, saint_id: int) -> tuple:
        try:
            sql_req = "SELECT name, sign, month, day FROM saints WHERE id=?"
            async with self.db.execute(sql_req, (saint_id,)) as cursor:
                saint = await cursor.fetchone()
                return tuple(saint)
        except Exception as e:
            self._logger.error(
                f"Some exception while get saint {saint_id} info from saints\n"
                f'\t"{e}" on {e.__traceback__.tb_lineno}'
            )
            return tuple()

    def _month_conversion(self, day_date: date):
        if day_date.year != self._table_year:
            if day_date.month == 12 and day_date.day in range(28, 32):
                return -1
            else:
                raise DateDBError("Date from past year")
        else:
            return day_date.month
        
    def _cache(self, day_date: date, day: tuple = [], saints: tuple = []):
        if day:
            cache = self._days_cache
            data = day
        elif saints:
            cache = self._saints_cache
            data = saints
        else:
            return
        while len(cache) >= self._limit:
            keys = sorted(cache.keys())
            if day_date > keys[0]:
                cache.pop(keys[0])
        cache[day_date] = data
