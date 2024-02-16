import os
import sqlite3

from dotenv import load_dotenv


load_dotenv()
path = os.getenv('PATH_DATABASE')


with sqlite3.connect(path) as db:
    c = db.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        temperature INTEGER DEFAULT 1,
        weather_description INTEGER DEFAULT 1,
        pressure INTEGER DEFAULT 1,
        wind_speed INTEGER DEFAULT 1,
        humidity INTEGER DEFAULT 1,
        cloudy INTEGER DEFAULT 1,
        visibility INTEGER DEFAULT 1,
        sunrise_sunset INTEGER DEFAULT 1,
        utc_time INTEGER DEFAULT 1,
        utc INTEGER DEFAULT 1,
        image INTEGER DEFAULT 1
    )""")
    db.commit()


def check_id(user_id: int):
    '''
    Проверка на наличие пользователя в базе данных
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT id FROM settings WHERE rowid = ?", (user_id,))
        if c.fetchone() is None:
            c.execute("INSERT INTO settings(id) VALUES(?)", (user_id,))
            db.commit()


def get_list_settings(user_id: int) -> list:
    '''
    Получение списка параметров из базы данных пользователя
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT * FROM settings WHERE rowid = ?", (user_id,))
        return c.fetchone()[1:]


def change_parameter(user_id: int, number_parametr: int):
    '''
    Изменение параметра вывода погоды
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()

        dictionary_list_settings = {
            1: "temperature",
            2: "weather_description",
            3: "pressure",
            4: "wind_speed",
            5: "humidity",
            6: "cloudy",
            7: "visibility",
            8: "sunrise_sunset",
            9: "utc_time",
            10: "utc",
            11: "image"
        }

        dictionary_reciprocal_values = {
            0: "1",
            1: "0"
        }

        selected_parametr = dictionary_list_settings.get(number_parametr)
        c.execute("""SELECT {selected_parametr} FROM settings WHERE rowid = ?""".format(selected_parametr=selected_parametr), (user_id,))  # Получение текущего значения выбранного параметра
        value_selected_parametr = c.fetchone()[0]

        reciprocal_value = dictionary_reciprocal_values.get(value_selected_parametr)
        c.execute("""UPDATE settings SET {selected_parametr} = ? WHERE rowid = ?""".format(selected_parametr=selected_parametr), (reciprocal_value, user_id))  # Замена параметра на противоположный
        db.commit()
