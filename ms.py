import aiofiles
from datetime import datetime, timedelta, timezone

from utils import ZeroInDate, Days

Cyril_numbers = {
    0: "",
    1: "а",
    2: "в",
    3: "г",
    4: "д",
    5: "є",
    6: "ѕ",
    7: "з",
    8: "ѳ",
    9: "и",
    10: "і",
    20: "к",
    30: "л",
    40: "м",
    50: "н",
    60: "ѯ",
    70: "ѻ",
    80: "п",
    90: "ч",
    100: "р",
    200: "с",
    300: "т",
    400: "у",
    500: "ф",
    600: "х",
    700: "ѱ",
    800: "ѡ",
    900: "ц",
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

Znaki = {
    0: "\N{EIGHT POINTED BLACK STAR}",
    1: "\N{CIRCLED CROSS POMMEE}",
    2: "\N{CROSS POMMEE WITH HALF-CIRCLE BELOW}",
    3: "\N{CROSS POMMEE}",
    4: "\N{NOTCHED LEFT SEMICIRCLE WITH THREE DOTS}",
    5: "\N{NOTCHED RIGHT SEMICIRCLE WITH THREE DOTS}",
    6: "\N{BLACK CIRCLE}",
}

Error = "Друг, у меня какие-то проблемы... Обратись к администратору."


class MS_producer:
    def __init__(self, db_handler, logger):
        self._db_handler = db_handler
        self._logger = logger

    def _arab_to_cyril(self, number: int) -> str:
        # Проверяем на допустимость
        if number < 1:
            raise ZeroInDate("Zero or negative number")
        if number > 999999:
            raise ZeroInDate("Number is too large")
        # Разбиваем на цифры
        cyr_number = ""
        num_tuple = []
        while number:
            num_tuple.append(number % 10)
            number = number // 10
        # Обрабатываем всё, что меньше 1000
        mult = 1
        for digit in num_tuple[:3]:
            if digit * mult == 10:
                cyr_number = cyr_number + Cyril_numbers[digit * mult]
            else:
                cyr_number = Cyril_numbers[digit * mult] + cyr_number
            mult *= 10
        # Обрабатываем всё, что осталось
        mult = 1
        for digit in num_tuple[3:]:
            if digit * mult == 10:
                cyr_number = cyr_number + "҂" + Cyril_numbers[digit * mult]
            else:
                cyr_number = "҂" + Cyril_numbers[digit * mult] + cyr_number
            mult *= 10
        # Добавляем титло
        if len(cyr_number) > 1:
            cyr_number = cyr_number[:-1] + "\u0483" + cyr_number[-1:] + "."
        else:
            cyr_number = cyr_number + "\u0483" + "."
        return cyr_number

    def _creation_year(self, date) -> int:
        sept_new_year = datetime(day=13, month=9, year=date.year).date()
        creation = 5508
        if date > sept_new_year:
            creation += 1
        return date.year + creation

    async def make_holy(self, user: dict, day: Days) -> str:
        slovo: str
        # Формируем дату
        date = datetime.now(timezone(timedelta(hours=user["timezone"]))).date()
        if day == Days.YESTERDAY:
            slovo = "Вчера было "
            date = date - timedelta(days=1)
        elif day == Days.TOMMOROW:
            slovo = "Завтра "
            date = date + timedelta(days=1)
        else:  # Days.TODAY
            slovo = "Сегодня "
        # Получаем данные о дне из БД
        if len(day_info := await self._db_handler.get_day_values(date)) == 0:
            self._logger.error(f"Can't find day info for {date.day}.{date.month}")
            return Error
        _, _, fasting, f_type, _, holy = day_info
        # Получаем поминаемых святых и иконы  из БД
        if len(saints_list := await self._db_handler.get_saints(date)) == 0:
            self._logger.error(f"Can't find saits info for {date.day}.{date.month}")
        # Заполняем дату
        old_date = date - timedelta(days=(date.year // 100 - date.year // 400 - 2))
        try:
            ciril_day = self._arab_to_cyril(old_date.day)
            creation_year = self._creation_year(date)
            ciril_creation_year = self._arab_to_cyril(creation_year)
        except ZeroInDate as e:
            self._logger.error(f"Error while convert number to cirillic: {e}")
            return Error
        slovo += (
            f"*{ciril_day}* ({old_date.day}) *{Mesyacy[old_date.month]} {ciril_creation_year}* "
            f"({creation_year}) *года от сотворения мира * по старому стилю.\n"
        )
        # Заполняем великие праздники и пост
        if holy:
            slovo += f"\nВеликий праздник - {Znaki[1]} *{holy}*!\n"
        if fasting and f_type:
            slovo += f"\nИдёт {fasting}, {f_type}.\n"
        # Отделяем дни поминования от икон
        saint_slovo = ""
        icon_slovo = ""
        for saint in saints_list:
            _, s_name, s_sign = saint
            if s_sign == 0:
                icon_slovo += "\n" + Znaki[s_sign] + " " + s_name
            elif s_sign is None:
                saint_slovo += "\n" + Znaki[6] + " " + s_name
            elif s_sign != 1:
                saint_slovo += "\n" + Znaki[s_sign] + " " + s_name
        if len(saint_slovo):
            slovo += "\nДень памяти:" + saint_slovo
        if len(icon_slovo):
            slovo += "\n\nПрославляются иконы Божей Матери:" + icon_slovo
        # Получаем притчу или житие
        # with open(f'signs/{date.month}/{date.day}.md', 'r') as sign:
        #     for line in sign.readlines():
        #         slovo += line
        return slovo

    async def make_sign(self, user: dict, day: Days) -> str:
        slovo: str
        # Формируем дату
        date = datetime.now(timezone(timedelta(hours=user["timezone"]))).date()
        if day == Days.TODAY:
            slovo = "Сегодня - "
        elif day == Days.TOMMOROW:
            slovo = "Завтра - "
            date = date + timedelta(days=1)
        elif day == Days.YESTERDAY:
            slovo = "Истёк день рекомый "
            date = date - timedelta(days=1)
        else:
            return Error
        # Получаем данные о дне из БД
        if len(day_info := await self._db_handler.get_day_values(date)) == 0:
            self._logger.error(f"Can't find day info for {date.day}.{date.month}")
            return Error
        name, work, fasting, _, crowning, holy = day_info
        # Заполняем название
        slovo += f"*{name}*. "
        if date.isoweekday() == 3:
            slovo += "\N{FROG FACE} "
        # Заполняем рабочесть, пост, венчание и великие праздники
        slovo += f"{work} день, "
        if fasting:
            slovo += f"идёт {fasting}, "
        else:
            slovo += "поста нет, "
        slovo += f"{crowning}."
        if holy:
            slovo += f"\nВеликий праздник - *{holy}*!"
        slovo += "\n\n"
        # Получаем приметы
        try:
            async with aiofiles.open(f"signs/{date.month}/{date.day}.md", "r") as sign:
                async for line in sign:
                    slovo += line
        except FileNotFoundError:
            self._logger.error(f"Can't find  Slovo for  {date.day}.{date.month}")
            return Error
        except Exception as e:
            self._logger.error(
                f"Some exception while get Slovo for  {date.day}.{date.month}\n"
                f"\t{e} on {e.__traceback__.tb_lineno}"
            )
            return Error
        return slovo
