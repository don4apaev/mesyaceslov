import sqlite3
from datetime import date, timedelta
from requests import get
import xml.etree.ElementTree as ET

from utils import get_fasting, get_crowning
from utils import XMLCalendarError, DateDBError


class DB_handler:
    def __init__(self, db_name: str):
        self.db_name = db_name

    def fill_daytable(self):
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
        holydays = {}
        cur_year = date.today().year
        # Скачать и распаковать производственный календарь
        url = f'https://xmlcalendar.ru/data/ru/{cur_year}/calendar.xml'
        response = get(url)
        root = ET.fromstring(response.content.decode())
        if not (xmldays:=root.find('days')):
            raise XMLCalendarError
        for day in xmldays:
            xml_date = day.get('d').split('.')
            holydays[int(xml_date[0])*100+int(xml_date[1])] = int(day.get('t'))
        # Заполнить даты
        date = date(year=cur_year,month=1,day=1)
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        while date.year == cur_year:
            if not (day_type := holydays.get(date.month*100+date.day)):
                day_type = 3 if date.isoweekday() < 6 else 1
            fasting = get_fasting(date, cur_year)
            crowning = get_crowning(date, cur_year)
            sql_req = "UPDATE days_os SET (work, fasting, crowning) = (?, ?, ?) "\
                        "WHERE month=? AND day=?;"
            cur.execute(sql_req, (day_type, fasting, crowning, date.month, date.day))
            date += timedelta(days=1)
        con.commit()

    def get_day_values(self, day_date: date) -> tuple:
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        sql_req = 'SELECT name, work, fasting, crowning, holy FROM days_os '\
                    'WHERE month=? AND day=?;'
        cur.execute(sql_req, (day_date.month, day_date.day))
        res = cur.fetchall()
        if len(res) != 1:
            raise DateDBError
        return res[0]

    def add_user(self, user_id):
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        sql_req = 'SELECT * FROM users WHERE id=?'
        cur.execute(sql_req, (user_id,))
        res = cur.fetchall()
        if len(res) != 0:
            return
        sql_req = 'INSERT INTO users (id, admin, timezone, morning, evening) '\
                    'VALUES (?, ?, ?, ?, ?);'
        cur.execute(sql_req, (user_id, False, 3, None, None))
        con.commit()

    def get_user_info(self, user_id):
        con = sqlite3.connect(self.db_name)
        cur = con.cursor()
        sql_req = 'SELECT timezone FROM users WHERE id=?'
        cur.execute(sql_req, (user_id,))
        res = cur.fetchall()
        if len(res) != 1:
            raise DateDBError
        user = {'timezone':res[0][0]}
        return user
        
