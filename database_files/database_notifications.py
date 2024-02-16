import datetime
import os
import sqlite3
import time

from dotenv import load_dotenv


load_dotenv()
path = os.getenv('PATH_DATABASE')


with sqlite3.connect(path) as db:
    c = db.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY,
        chat_id INTEGER,
        status_notifications INTEGER DEFAULT 0,
        dispatch_time_utc VARCHAR(10),
        city VARCHAR(170),
        Monday INTEGER DEFAULT 0,
        Tuesday INTEGER DEFAULT 0,
        Wednesday INTEGER DEFAULT 0,
        Thursday INTEGER DEFAULT 0,
        Friday INTEGER DEFAULT 0,
        Saturday INTEGER DEFAULT 0,
        Sunday INTEGER DEFAULT 0
    )""")
    db.commit()


def check_id(user_id: int, chat_id: int):
    '''
    Проверка на наличие пользователя в базе данных
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT id FROM notifications WHERE rowid = ?", (user_id,))
        if c.fetchone() is None:
            c.execute("INSERT INTO notifications(id, chat_id) VALUES(?, ?)", (chat_id, user_id))
            db.commit()


def get_day_week():
    """
    Получение текущего дня недели
    """

    dictionary_days_week = {
        0: "Monday",
        1: "Tuesday",
        2: "Wednesday",
        3: "Thursday",
        4: "Friday",
        5: "Saturday",
        6: "Sunday"
    }

    return dictionary_days_week.get(datetime.datetime.fromtimestamp(time.time()).weekday())


def get_notifications() -> list[tuple]:
    '''
    Получение всех параметров уведомлений подходящих для проверки на уведомления

    Возвращает user_id, chat_id, dispatch_time_utc, city
    '''

    with sqlite3.connect(path) as db:
        c = db.cursor()
        day_week = get_day_week()
        c.execute("""SELECT id, chat_id, dispatch_time_utc, city FROM notifications
                  WHERE (status_notifications = 1) AND ({day_week} = 1) AND (dispatch_time_utc IS NOT NULL)""".format(day_week=day_week))
        result = c.fetchall()
        return result


def get_bool_dispatch_time_utc(user_id: int) -> bool:
    """
    Проверка на наличие добавленного времени в базе данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT dispatch_time_utc FROM notifications WHERE rowid = ?", (user_id,))
        return False if c.fetchone()[0] is None else True


def get_status_notifications(user_id: int) -> int:
    """
    Получение значения status_notifications из базы данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT status_notifications FROM notifications WHERE rowid = ?", (user_id,))
        return c.fetchone()[0]


def get_city(user_id: int) -> str:
    """
    Получение значения city из базы данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT city FROM notifications WHERE rowid = ?", (user_id,))
        return c.fetchone()[0]


def get_dispatch_time_utc(user_id: int) -> str:
    """
    Получение значения dispatch_time_utc из базы данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT dispatch_time_utc FROM notifications WHERE rowid = ?", (user_id,))
        return c.fetchone()[0]


def get_day_click_status(user_id: int) -> tuple[int]:
    """
    Получение текущих значений дней недели в базе данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("SELECT Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday FROM notifications WHERE rowid = ?", (user_id,))
        return c.fetchone()


def add_city(user_id: int, city_name: str):
    """
    Добавление города в базу данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("UPDATE notifications SET city = ? WHERE rowid = ?", (city_name, user_id))
        db.commit()


def add_selected_day(user_id: int, selected_day: str):
    """
    Добавление выбранного дня в базу данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()

        dictionary_reciprocal_values = {
            0: "1",
            1: "0"
        }

        c.execute("SELECT {selected_day} FROM notifications WHERE rowid = ?".format(selected_day=selected_day), (user_id,))
        reciprocal_value = dictionary_reciprocal_values.get(c.fetchone()[0])

        c.execute("UPDATE notifications SET {selected_day} = ? WHERE rowid = ?".format(selected_day=selected_day), (reciprocal_value, user_id))
        db.commit()


def add_dispatch_time_utc(user_id: int, time_utc: str):
    """
    Добавление времени отправки уведомления в базу данных пользователя
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("""UPDATE notifications SET dispatch_time_utc = ?, status_notifications = 1 WHERE rowid = ?""", (time_utc, user_id))
        db.commit()


def change_all_days(user_id: int, value: int):
    """
    Ставит определенное значение (value) для каждого дня недели
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("""UPDATE notifications
                  SET Monday = {value},
                  Tuesday = {value},
                  Wednesday = {value},
                  Thursday = {value},
                  Friday = {value},
                  Saturday = {value},
                  Sunday = {value} WHERE rowid = ?""".format(value=value), (user_id,))
        db.commit()


def change_status_notifications(user_id: int, value: int):
    """
    Изменяет текущее значение status_notifications на определенное (value)
    """

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("""UPDATE notifications SET status_notifications = ? WHERE rowid = ?""", (value, user_id))
        db.commit()


def delete_notification(user_id: int):
    """
    Удаление уведомления из базы данных пользователя
    """

    change_all_days(user_id, 0)
    change_status_notifications(user_id, 0)

    with sqlite3.connect(path) as db:
        c = db.cursor()
        c.execute("""UPDATE notifications SET dispatch_time_utc = NULL WHERE rowid = ?""", (user_id,))
        db.commit()
