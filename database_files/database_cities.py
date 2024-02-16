import os
import sqlite3
from typing import Literal, Union

from dotenv import load_dotenv


load_dotenv()
path = os.getenv('PATH_DATABASE')


with sqlite3.connect(path) as db:
    c = db.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS cities (
        id INTEGER PRIMARY KEY,
        number_of_cities INTEGER DEFAULT 0,
        city_01 VARCHAR(170),
        city_02 VARCHAR(170),
        city_03 VARCHAR(170),
        city_04 VARCHAR(170),
        city_05 VARCHAR(170)
    )""")
    db.commit()


def check_id(user_id: int):
    '''
    Проверка на наличие пользователя в базе данных
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT id FROM cities WHERE rowid = ?", (user_id,))
        if c.fetchone() is None:
            c.execute("INSERT INTO cities(id) VALUES(?)", (user_id,))
            db.commit()


def get_number_of_cities(user_id: int) -> int:
    '''
    Получение значения столбца number_of_cities из базы данных пользователя
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT number_of_cities FROM cities WHERE rowid = ?", (user_id,))
        return c.fetchone()[0]


def check_missing_cities(user_id: int):
    '''
    Проверка на наличие городов в базе данных пользователя
    '''

    return True if get_number_of_cities(user_id) == 0 else False


def check_max_numbers(user_id: int):
    '''
    Проверка на превышения лимита добавления городов
    '''

    return False if get_number_of_cities(user_id) < 5 else True


def list_cities(user_id: int) -> tuple[str]:
    '''
    Возвращение кортежа городов из базы данных пользователя
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT city_01, city_02, city_03, city_04, city_05 FROM cities WHERE rowid = ?", (user_id,))
        return c.fetchone()


def check_duplicate(user_id: int, city_name: str):
    '''
    Проверка города на дубликат в базе данных пользователя
    '''

    return True if city_name in list_cities(user_id) else False


def add_city(user_id: int, city_name: str):
    '''
    Добавление города в базу данных пользователя
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT city_01, city_02, city_03, city_04, city_05 FROM cities WHERE rowid = ?", (user_id,))
        all_cities = c.fetchone()

        for numbering in range(5):
            city_number = f"city_0{numbering + 1}"
            if all_cities[numbering] is None:
                c.execute("UPDATE cities SET {city_number} = ? WHERE rowid = ?".format(city_number=city_number), (city_name, user_id))
                break

        c.execute("UPDATE cities SET number_of_cities = number_of_cities + 1 WHERE rowid = ?", (user_id,))
        db.commit()


def delete_city(user_id: int, number_city: int) -> Union[str, Literal['Error_delete']]:
    '''
    Удаление города из базы данных пользователя
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()

        def delete_city_func(number_city):
            city_number = f"city_0{number_city}"
            c.execute("SELECT {city_number} FROM cities WHERE rowid = ?".format(city_number=city_number), (user_id,))
            city_name = c.fetchone()[0]

            if city_name:
                c.execute("UPDATE cities SET {city_number} = NULL WHERE rowid = ?".format(city_number=city_number), (user_id,))
                c.execute("UPDATE cities SET number_of_cities = number_of_cities - 1 WHERE rowid = ?", (user_id,))
                db.commit()
                return city_name
            return "Error_delete"  # Используется, если город уже ранее был удален

        city_name = delete_city_func(number_city)
        return city_name if city_name != "Error_delete" else "Error_delete"
