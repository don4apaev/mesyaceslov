import aiosqlite
import aiohttp
import asyncio
from datetime import date, timedelta
import xml.etree.ElementTree as ET

from utils import get_fasting_type, get_crowning, get_holyday
from utils import XMLCalendarError

class DB_handler:
    def __init__(self, db_name: str, logger):
        self.lock = asyncio.Lock()
        self.db_name = db_name
        self._logger = logger

    async def __aenter__(self):
        self.db = await aiosqlite.connect(self.db_name)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.db.close()

class User_DB_handler(DB_handler):
    async def add_user(self, user_id: int):
        async with self.lock:
            try:
                sql_req = 'SELECT * FROM users WHERE id=?'
                cursor = await self.db.execute(sql_req, (user_id,))
                user = await cursor.fetchone()
                if user:
                    self._logger.debug(f'Try to add already existin user {user_id}')
                    return
                sql_req = 'INSERT INTO users (id, admin, mailing, timezone, morning, evening) '\
                        'VALUES (?, ?, ?, ?, ?, ?)'
                cursor = await self.db.execute(sql_req, (user_id, False, None, 3, None, None))
                await self.db.commit()
            except Exception as e:
                self._logger.error(f'Some exception while adding user {user_id}\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')
            else:
                self._logger.debug(f'New user {user_id} addded to DB')


    async def get_user_info(self, user_id) -> dict:
        async with self.lock:
            try:
                sql_req = 'SELECT * FROM users WHERE id=?'
                async with self.db.execute(sql_req, (user_id,)) as cursor:
                    user = await cursor.fetchone()
                    if not user:
                        return None
                    keys = ('id', 'admin', 'mailing', 'timezone', 'morning', 'evening')
                    return dict(zip(keys, user))
            except Exception as e:
                self._logger.error(f'Some exception while get user {user_id} info\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')
                return None

    async def get_users(self) -> list:
        async with self.lock:
            try:
                sql_req = 'SELECT id, mailing, timezone, morning, evening FROM users'
                async with self.db.execute(sql_req) as cursor:
                    users = await cursor.fetchall()
                    if len(users) == 0:
                        return None
                    return dict(users)
            except Exception as e:
                self._logger.error(f'Some exception while get users info\n'\
                                    f'\t"{e}" on {e.__traceback__.tb_lineno}')
                return None

class Days_DB_handler(DB_handler):
    async def fill_daytable(self):
        # Обновить данные в days_os
        holydays = {}
        cur_year = date.today().year
        # Скачать и распаковать производственный календарь
        try:
            url = f'https://xmlcalendar.ru/data/ru/{cur_year}/calendar.xml'
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    calendar = response.content.decode()
        except Exception as e:
            self._logger.error(f'Some exception while get xmlcalendar\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            return
        try:
            root = ET.fromstring(calendar)
            if not (xmldays:=root.find('days')):
                raise XMLCalendarError
            for day in xmldays:
                """
                В XML теги <days>:
                    d - дата в формате ММ.ДД.
                    t - тип записи: 
                        1 - выходной день,
                        2 - рабочий и сокращенный (может быть использован для любого дня недели),
                        3 - рабочий день.
                    h - ссылкой на идентификатор праздника из <holidays>.
                    f - дата с которой был перенесен выходной день в формате ММ.ДД
                """
                xml_date = day.get('d').split('.')
                holydays[int(xml_date[0])*100+int(xml_date[1])] = int(day.get('t'))
        except Exception as e:
            self._logger.error(f'Some exception while parsing xmlcalendar\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            return
        # Заполнить даты в календаре на год
        all_days = []
        iter_date = date(year=cur_year,month=1,day=1)
        while iter_date.year == cur_year:
            if not (day_type := holydays.get(iter_date.month*100+iter_date.day)):
                day_type = 3 if iter_date.isoweekday() < 6 else 1
            fasting = get_fasting_type(iter_date, cur_year)
            crowning = get_crowning(iter_date, cur_year)
            holyday = get_holyday(iter_date, cur_year)
            iter_date += timedelta(days=1)
            all_days.append(day_type, fasting, crowning, holyday,
                    iter_date.month, iter_date.day)

        sql_req = "UPDATE days_os SET (work, fasting, crowning, holy) = (?, ?, ?, ?) "\
                    "WHERE month=? AND day=?"
        try:
            cursor = await self.db.executemany(sql_req, all_days)
            await self.db.commit()
        except Exception as e:
            self._logger.error(f'Some exception while updatiing days_os\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            return
        else:
            self._logger.debug(f'days_os updated')
        # Обновить данные в saints
        # Обновить даты переходящих праздников
        # 104 - первое вск после 31 окт
        # 230 - ближайшее вск к 23 ноя
        con.commit()

    async def get_day_values(self, day_date: date) -> tuple:
        try:
            sql_req = 'SELECT name, work, fasting, crowning, holy FROM days_os '\
                        'WHERE month=? AND day=?'
            async with self.db.execute(sql_req, (day_date.month, day_date.day)) as cursor:
                day = await cursor.fetchone()
                if not day:
                    return None
                return tuple(day)
        except Exception as e:
            self._logger.error(f'Some exception while get {day_date} info from days_os\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            return None

    async def get_saints(self, day_date: date) -> tuple:
        try:
            sql_req = 'SELECT id, name, sign FROM saints WHERE month=? AND day=?'
            async with self.db.execute(sql_req, (day_date.month, day_date.day)) as cursor:
                saints = await cursor.fetchall()
                if len(saints) == 0:
                    return None
                return tuple(tuple(saint) for saint in saints)
        except Exception as e:
            self._logger.error(f'Some exception while get {day_date} info from saints\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            return None

    async def get_saint(self, saint_id: int) -> tuple:
        try:
            sql_req = 'SELECT name, sign, month, day FROM saints WHERE id=?'
            async with self.db.execute(sql_req, (saint_id,)) as cursor:
                saint = cursor.fetchall()
                if not saint:
                    return None
                return tuple(saint)
        except Exception as e:
            self._logger.error(f'Some exception while get saint {saint_id} info from saints\n'\
                                f'\t"{e}" on {e.__traceback__.tb_lineno}')
            return None
