import sqlite3
from datetime import date, timedelta
from requests import get
import xml.etree.ElementTree as ET

from utils import get_fasting_type, get_crowning, get_holyday
from utils import XMLCalendarError, DateDBError


class DB_handler:
    def __init__(self, db_ms_name: str, db_us_name: str):
        self.db_ms_name = db_ms_name
        self.db_us_name = db_us_name

    def fill_daytable(self):
        holydays = {}
        cur_year = date.today().year
        # Скачать и распаковать производственный календарь
        url = f'https://xmlcalendar.ru/data/ru/{cur_year}/calendar.xml'
        response = get(url)
        root = ET.fromstring(response.content.decode())
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
        # Заполнить даты в календаре на год
        iter_date = date(year=cur_year,month=1,day=1)
        con = sqlite3.connect(self.db_ms_name)
        cur = con.cursor()
        while iter_date.year == cur_year:
            if not (day_type := holydays.get(iter_date.month*100+iter_date.day)):
                day_type = 3 if iter_date.isoweekday() < 6 else 1
            fasting = get_fasting_type(iter_date, cur_year)
            crowning = get_crowning(iter_date, cur_year)
            holyday = get_holyday(iter_date, cur_year)
            sql_req = "UPDATE days_os SET (work, fasting, crowning, holy) = (?, ?, ?, ?) "\
                        "WHERE month=? AND day=?"
            cur.execute(sql_req, (day_type, fasting, crowning, holyday,
                        iter_date.month, iter_date.day))
            iter_date += timedelta(days=1)
        # Обновить даты переходящих праздников
        con.commit()

    def get_day_values(self, day_date: date) -> tuple:
        con = sqlite3.connect(self.db_ms_name)
        cur = con.cursor()
        sql_req = 'SELECT name, work, fasting, crowning, holy FROM days_os '\
                    'WHERE month=? AND day=?'
        cur.execute(sql_req, (day_date.month, day_date.day))
        res = cur.fetchall()
        if len(res) != 1:
            raise DateDBError
        return res[0]

    def get_saints(self, day_date: date) -> list:
        con = sqlite3.connect(self.db_ms_name)
        cur = con.cursor()
        sql_req = 'SELECT id, name, sign FROM saints WHERE month=? AND day=?'
        cur.execute(sql_req, (day_date.month, day_date.day))
        res = cur.fetchall()
        return res

    def get_saint(self, saint_id: int) -> tuple:
        con = sqlite3.connect(self.db_ms_name)
        cur = con.cursor()
        sql_req = 'SELECT name, sign FROM saints WHERE id=?'
        cur.execute(sql_req, (saint_id,))
        res = cur.fetchall()
        if len(res) != 1:
            raise DateDBError
        return res[0]

    def add_user(self, user_id):
        con = sqlite3.connect(self.db_us_name)
        cur = con.cursor()
        sql_req = 'SELECT * FROM users WHERE id=?'
        cur.execute(sql_req, (user_id,))
        res = cur.fetchall()
        if len(res) != 0:
            return
        sql_req = 'INSERT INTO users (id, admin, mailing, timezone, morning, evening) '\
                    'VALUES (?, ?, ?, ?, ?, ?)'
        cur.execute(sql_req, (user_id, False, None, 3, None, None))
        con.commit()

    def get_user_info(self, user_id) -> tuple:
        con = sqlite3.connect(self.db_us_name)
        cur = con.cursor()
        sql_req = 'SELECT timezone FROM users WHERE id=?'
        cur.execute(sql_req, (user_id,))
        res = cur.fetchall()
        if len(res) != 1:
            raise DateDBError
        user = {'timezone':res[0][0]}
        return user
        
    def get_users(self) -> list:
        con = sqlite3.connect(self.db_us_name)
        cur = con.cursor()
        sql_req = 'SELECT id, admin, mailing, timezone, morning, evening FROM users'
        cur.execute(sql_req)
        res = cur.fetchall()
        users = []
        for user in res:
            users.append({
                'id'        : user[0],
                'mailing'   : user[2],
                'timezone'  : user[3],
                'morning'   : user[4],
                'evening'   : user[5]
            })
        return users
