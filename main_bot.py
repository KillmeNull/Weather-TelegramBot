import datetime
import json
import os
import time
from datetime import timedelta, timezone
from threading import Thread

import database_files.database_cities as dbcities
import database_files.database_notifications as dbnotif
import database_files.database_settings as dbsettings

from dotenv import load_dotenv

import requests

import schedule

import telebot
from telebot import types


load_dotenv()
bot = telebot.TeleBot(os.getenv('API_TELEGRAMBOT'))
API_weather = os.getenv('API_OPENWEATHERMAP')


markup_start = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton("🌞 Узнать погоду"),
    types.KeyboardButton("⚙️ Настройки")
)

markup_settings = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(
    types.KeyboardButton("🔔 Уведомления"),
    types.KeyboardButton("🌦️ Параметры погоды"),
    types.KeyboardButton("🏙️ Города"),
    types.KeyboardButton("↩️ Назад")
)

markup_settings_cities = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2).add(
    types.KeyboardButton("Добавить город"),
    types.KeyboardButton("Удалить город"),
    types.KeyboardButton("Список моих городов"),
    types.KeyboardButton("↩️ Нaзад")
)


def buttons_weather_parameters(list_settings):
    dictionary_weather_parameters_panel = {
        0: "❌",
        1: "✔️"
    }

    markup_weather_parameters = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton(f"Температура {dictionary_weather_parameters_panel.get(list_settings[0])}", callback_data="weather_parameters01"),
        types.InlineKeyboardButton(f"Краткое описание {dictionary_weather_parameters_panel.get(list_settings[1])}", callback_data="weather_parameters02"),
        types.InlineKeyboardButton(f"Давление {dictionary_weather_parameters_panel.get(list_settings[2])}", callback_data="weather_parameters03"),
        types.InlineKeyboardButton(f"Ветер {dictionary_weather_parameters_panel.get(list_settings[3])}", callback_data="weather_parameters04"),
        types.InlineKeyboardButton(f"Влажность {dictionary_weather_parameters_panel.get(list_settings[4])}", callback_data="weather_parameters05"),
        types.InlineKeyboardButton(f"Облачность {dictionary_weather_parameters_panel.get(list_settings[5])}", callback_data="weather_parameters06"),
        types.InlineKeyboardButton(f"Видимость {dictionary_weather_parameters_panel.get(list_settings[6])}", callback_data="weather_parameters07"),
        types.InlineKeyboardButton(f"Восход/закат {dictionary_weather_parameters_panel.get(list_settings[7])}", callback_data="weather_parameters08"),
        types.InlineKeyboardButton(f"Местное время {dictionary_weather_parameters_panel.get(list_settings[8])}", callback_data="weather_parameters09"),
        types.InlineKeyboardButton(f"UTC {dictionary_weather_parameters_panel.get(list_settings[9])}", callback_data="weather_parameters10"),
        types.InlineKeyboardButton(f"Картинка {dictionary_weather_parameters_panel.get(list_settings[10])}", callback_data="weather_parameters11")
    )

    return markup_weather_parameters


def buttons_days_notifications(callback):
    dictionary_days_week = {
        0: "❌",
        1: "✔️"
    }

    click_status = dbnotif.get_day_click_status(callback.from_user.id)
    markup_get_days_notifications = types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(f"Понедельник {dictionary_days_week.get(click_status[0])}", callback_data="notif|week_panel|day_01"),
        types.InlineKeyboardButton(f"Вторник {dictionary_days_week.get(click_status[1])}", callback_data="notif|week_panel|day_02")
    )

    markup_get_days_notifications.add(
        types.InlineKeyboardButton(f"Среда {dictionary_days_week.get(click_status[2])}", callback_data="notif|week_panel|day_03"),
        types.InlineKeyboardButton(f"Четверг {dictionary_days_week.get(click_status[3])}", callback_data="notif|week_panel|day_04"),
        types.InlineKeyboardButton(f"Пятница {dictionary_days_week.get(click_status[4])}", callback_data="notif|week_panel|day_05")
    )

    markup_get_days_notifications.add(
        types.InlineKeyboardButton(f"Суббота {dictionary_days_week.get(click_status[5])}", callback_data="notif|week_panel|day_06"),
        types.InlineKeyboardButton(f"Воскресенье {dictionary_days_week.get(click_status[6])}", callback_data="notif|week_panel|day_07")
    )

    markup_get_days_notifications.add(types.InlineKeyboardButton("Готово", callback_data="notif|accept_panel|accept"))
    markup_get_days_notifications.add(types.InlineKeyboardButton("↩️ Назад", callback_data="notif|back_panel|back_02"))

    return markup_get_days_notifications


def buttons_notifications_panel(user_id):
    markup_notifications = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if dbnotif.get_bool_dispatch_time_utc(user_id) is False:
        markup_notifications.add(types.KeyboardButton("Добавить уведомление"))

    else:
        if dbnotif.get_status_notifications(user_id) == 1:
            button01_notifications = types.KeyboardButton("Выкл уведомление")
        else:
            button01_notifications = types.KeyboardButton("Вкл уведомление")
        markup_notifications.add(button01_notifications, types.KeyboardButton("Удалить уведомление"))
        markup_notifications.add(types.KeyboardButton("Мои уведомления"), types.KeyboardButton("↩️ Нaзад"))
        return markup_notifications

    markup_notifications.add(types.KeyboardButton("↩️ Нaзад"))
    return markup_notifications


def get_number_value(value):
    """
    Узнать однозначное или двузначное число в конце callback_data
    """

    return value[-1:] if value[0] == "0" else value[-2:]


def list_sities_handler(message):
    """
    Преобразование кортежа городов из базы данных, для замены городов с значением None на ""
    """

    list_sities_database = list(dbcities.list_cities(message.from_user.id))
    list_sities_database = [item if item is not None else "" for item in list_sities_database]
    return list_sities_database


def list_sities_handler_client(message):
    """
    Преобразование кортежа городов из базы данных, для вывода пользователю
    """

    list_sities_database = dbcities.list_cities(message.from_user.id)
    final_list = [item for item in list_sities_database if item is not None]
    return "\n".join(final_list)


def list_value_notifications(user_id):
    """
    Возвращает выбранные пользователем параметры при добавлении уведомлений: город, дни, время
    """

    dictionary_days_week = {
        0: "понедельник",
        1: "вторник",
        2: "среду",
        3: "четверг",
        4: "пятницу",
        5: "субботу",
        6: "воскресенье"
    }

    all_days = dbnotif.get_day_click_status(user_id)
    if all_days.count(1) == 7:
        selected_days = " ежедневно"
    elif all_days.count(1) == 0:
        selected_days = ""
    else:
        indices = [index for index, item in enumerate(all_days) if item == 1]  # индексы дней недели, которые выбрал пользователь
        if indices == [0, 1, 2, 3, 4]:
            selected_days = " по будням"
        elif indices == [5, 6]:
            selected_days = " по выходным"
        else:
            list_selected_days = []
            for element in indices:
                list_selected_days.append(dictionary_days_week.get(element))
            selected_days = f" на {', '.join(list_selected_days)}"

    city_name = dbnotif.get_city(user_id)
    time_utc = dbnotif.get_dispatch_time_utc(user_id)
    time_utc = f"{time_utc[:2]}:{time_utc[2:]}"

    return city_name, time_utc, selected_days


@bot.message_handler(commands=['start'])
def start_panel(message):
    def check_user_last_name(message):  # Проверка на наличие фамилии у пользователя
        return "" if message.from_user.last_name is None else f" {message.from_user.last_name}"

    dbcities.check_id(message.from_user.id)  # Проверка на наличие пользователя в базе данных городов
    dbsettings.check_id(message.from_user.id)  # Проверка на наличие пользователя в базе данных параметров
    dbnotif.check_id(message.from_user.id, message.chat.id)  # Проверка на наличие пользователя в базе данных уведомлений

    bot.send_message(message.chat.id, f"""Привет, {message.from_user.first_name}{check_user_last_name(message)}. \
Я <b>Bot Weather</b>, отправлю тебе погоду в любое время.""", reply_markup=markup_start, parse_mode="html")


@bot.message_handler(regexp="🌞 Узнать погоду")
def find_weather(message):
    if dbcities.check_missing_cities(message.from_user.id) is False:
        if dbcities.get_number_of_cities(message.from_user.id) == 1:  # Отправка погоды сразу, если в базе данных пользователя один город
            city_name = list_sities_handler_client(message)
            get_weather(message.from_user.id, None, message.chat.id, city_name)
        else:
            erlst = list_sities_handler(message)
            markup_settings_find_weather = types.InlineKeyboardMarkup(row_width=1).add(
                types.InlineKeyboardButton(erlst[0], callback_data="find_weather_city01"),
                types.InlineKeyboardButton(erlst[1], callback_data="find_weather_city02"),
                types.InlineKeyboardButton(erlst[2], callback_data="find_weather_city03"),
                types.InlineKeyboardButton(erlst[3], callback_data="find_weather_city04"),
                types.InlineKeyboardButton(erlst[4], callback_data="find_weather_city05")
            )
            bot.send_message(message.chat.id, "Выберите город:", reply_markup=markup_settings_find_weather)
    else:
        bot.send_message(message.chat.id, "Для начала <b>укажите город</b> в Настройки → Города → Добавить город. Всего можно указать до 5 городов",
                         parse_mode="html")


def get_weather(user_id, message_id, chat_id, city_name, call_type="message"):
    """
    Вывод погоды пользователю
    """

    weather_fromsite = requests.get(f'https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_weather}&lang=ru&units=metric')
    weather_answer = json.loads(weather_fromsite.text)

    list_settings = dbsettings.get_list_settings(user_id)
    one_option_selected = [item for item in list_settings if item == 1]

    if one_option_selected:
        if list_settings[0]:
            temperature = f"\n{int(weather_answer['main']['temp'])}°C  Ощущается как {int(weather_answer['main']['feels_like'])}°C"
        else:
            temperature = ""

        if list_settings[1]:
            weather_description = f"\n{weather_answer['weather'][0]['description'].title()}"
        else:
            weather_description = ""

        if list_settings[2]:
            pressure_celsius = int(float(weather_answer["main"]["pressure"]) * 0.750063755419211)
            pressure = f"\nДавление: {pressure_celsius} мм рт. ст."
        else:
            pressure = ""

        if list_settings[3]:
            wind_speed = f"\nВетер: {weather_answer['wind']['speed']} метр/сек"
        else:
            wind_speed = ""

        if list_settings[4]:
            humidity = f"\nВлажность: {weather_answer['main']['humidity']}%"
        else:
            humidity = ""

        if list_settings[5]:
            cloudy = f"\nОблачность: {weather_answer['clouds']['all']}%"
        else:
            cloudy = ""

        if list_settings[6]:
            visibility = f"\nВидимость: {weather_answer['visibility']} м"
        else:
            visibility = ""

        if list_settings[7]:
            sunrise = datetime.datetime.fromtimestamp(weather_answer['sys']['sunrise']).strftime('%H:%M')
            sunset = datetime.datetime.fromtimestamp(weather_answer['sys']['sunset']).strftime('%H:%M')
            sunrise_sunset = f"\nВосход: {sunrise} Закат: {sunset}"
        else:
            sunrise_sunset = ""

        if list_settings[8]:
            times = datetime.datetime.fromtimestamp(time.time() + weather_answer['timezone'], datetime.UTC).strftime("%H:%M")
            utc_time = f" {times}"
        else:
            utc_time = ""

        if list_settings[9]:
            utc = f" {timezone(timedelta(seconds=weather_answer['timezone']))}"
        else:
            utc = ""

        if list_settings[10]:
            image = '<a href="https://i.ibb.co/LdpmHR0/photo-2023-10-28-19-33-08.jpg">&#8205;</a>'
        else:
            image = ""

        comma = "," if utc else ""

        weather_text = f"""{city_name}{utc_time}{comma}{utc}\
        \n\n<b>Текущая погода</b>{image}{temperature}{weather_description}{pressure}{wind_speed}{humidity}{cloudy}{visibility}{sunrise_sunset}"""

        if call_type == "message":
            bot.send_message(chat_id, weather_text, parse_mode="html", disable_web_page_preview=False)
        else:
            bot.edit_message_text(weather_text, chat_id, message_id, parse_mode="html", disable_web_page_preview=False)

    else:
        if call_type == "message":
            bot.send_message(chat_id, "Вы <b>отключили все параметры</b> вывода погоды. Выберите хотя бы один параметр, чтобы я мог вывести данные",
                             parse_mode="html")
        else:
            bot.edit_message_text("Вы <b>отключили все параметры вывода</b> погоды. Выберите хотя бы один параметр, чтобы я мог вывести данные",
                                  chat_id, message_id, parse_mode="html")


@bot.message_handler(regexp="⚙️ Настройки")
def settings_panel(message):
    bot.send_message(message.chat.id, "Настройки", reply_markup=markup_settings)


@bot.message_handler(regexp="🔔 Уведомления")
def notifications_panel(message):
    bot.send_message(message.chat.id, "Уведомления", reply_markup=buttons_notifications_panel(message.from_user.id))


@bot.message_handler(regexp="Добавить уведомление")
def add_notifications_panel(message, call_type="message"):
    erlst = list_sities_handler(message)
    markup_cities_notifications = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton(erlst[0], callback_data=f"notif|city_panel|{erlst[0]}"),
        types.InlineKeyboardButton(erlst[1], callback_data=f"notif|city_panel|{erlst[1]}"),
        types.InlineKeyboardButton(erlst[2], callback_data=f"notif|city_panel|{erlst[2]}"),
        types.InlineKeyboardButton(erlst[3], callback_data=f"notif|city_panel|{erlst[3]}"),
        types.InlineKeyboardButton(erlst[4], callback_data=f"notif|city_panel|{erlst[4]}")
    )

    if dbcities.get_number_of_cities(message.from_user.id) == 0:
        text = "Для начала <b>укажите город</b> в Настройки → Города → Добавить город. Всего можно указать до 5 городов"
    else:
        text = "Выберите город, для которого планируете добавить уведомление"

    if call_type == "message":
        bot.send_message(message.chat.id, text, reply_markup=markup_cities_notifications, parse_mode="html")
    else:
        bot.edit_message_text(text, message.message.chat.id, message.message.message_id,
                              reply_markup=markup_cities_notifications, parse_mode="html")


def get_days_notification(callback):
    markup_get_type_notifications = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton("Ежедневное уведомление", callback_data="notif|days_panel|every_day"),
        types.InlineKeyboardButton("По дням недели", callback_data="notif|days_panel|select_days_week"),
        types.InlineKeyboardButton("↩️ Назад", callback_data="notif|back_panel|back_01")
    )

    bot.edit_message_text("Выберите время отправки уведомлений", callback.message.chat.id, callback.message.message_id,
                          reply_markup=markup_get_type_notifications)


def select_days_week(callback):
    try:  # Используется, если сообщение меняется на идентичное
        bot.edit_message_text("Выберите дни недели, когда планируете получать уведомление", callback.message.chat.id,
                              callback.message.message_id, reply_markup=buttons_days_notifications(callback))
    except BaseException as e:
        print(e)


def get_time_clock_notification(callback):
    markup_time_clock_panel = types.InlineKeyboardMarkup(row_width=4)
    list_buttons = []
    for i in range(0, 24):
        number = str(i).zfill(2)
        list_buttons.append(types.InlineKeyboardButton(f"{number}:00", callback_data=f"notif|time_clock_panel|time_{number}"))
    markup_time_clock_panel.add(*list_buttons)
    markup_time_clock_panel.add(types.InlineKeyboardButton("↩️ Назад", callback_data="notif|back_panel|back_03"))

    bot.edit_message_text("Выберите <b>UTC ВРЕМЯ</b>, во сколько планируете получать уведомление",
                          callback.message.chat.id, callback.message.message_id, reply_markup=markup_time_clock_panel, parse_mode="html")


def get_time_minutes_notification(callback, clock):
    markup_time_minutes_panel = types.InlineKeyboardMarkup(row_width=4)
    list_buttons = []
    for i in range(0, 60):
        number = str(i).zfill(2)
        list_buttons.append(types.InlineKeyboardButton(f"{clock}:{number}", callback_data=f"notif|time_minutes_panel|time_{clock}{number}"))
    markup_time_minutes_panel.add(*list_buttons)
    markup_time_minutes_panel.add(types.InlineKeyboardButton("↩️ Назад", callback_data="notif|back_panel|back_04"))

    bot.edit_message_text("Выберите <b>UTC ВРЕМЯ</b>, во сколько планируете получать уведомление",
                          callback.message.chat.id, callback.message.message_id, reply_markup=markup_time_minutes_panel, parse_mode="html")


def end_notification(callback):
    city_name, time_utc, selected_days = list_value_notifications(callback.from_user.id)
    bot.edit_message_text(f"Уведомление добавлено для города <b>{city_name}</b>{selected_days} в <b>{time_utc}</b> по UTC",
                          callback.message.chat.id, callback.message.message_id, parse_mode="html")
    bot.send_sticker(callback.message.chat.id, "CAACAgIAAxkBAAELYKZlyOpKYx8hfAyS79Y5kTWx3I0quwAC4zQAAj-6IUu1IkFRj3IQ6zQE",
                     reply_markup=buttons_notifications_panel(callback.from_user.id))


@bot.message_handler(regexp="Выкл уведомление")
def off_notifications_panel(message):
    dbnotif.change_status_notifications(message.from_user.id, 0)
    bot.send_message(message.chat.id, "Уведомление выключено", reply_markup=buttons_notifications_panel(message.from_user.id))


@bot.message_handler(regexp="Вкл уведомление")
def on_notifications_panel(message):
    dbnotif.change_status_notifications(message.from_user.id, 1)
    bot.send_message(message.chat.id, "Уведомление включено", reply_markup=buttons_notifications_panel(message.from_user.id))


@bot.message_handler(regexp="Удалить уведомление")
def delete_notification_panel(message):
    dbnotif.delete_notification(message.from_user.id)
    bot.send_message(message.chat.id, "Уведомление удалено", reply_markup=buttons_notifications_panel(message.from_user.id))


@bot.message_handler(regexp="Мои уведомления")
def list_notification_panel(message):
    dictionary_status_notifications = {
        0: "выключено",
        1: "включено"
    }
    status_notifications = dictionary_status_notifications.get(dbnotif.get_status_notifications(message.from_user.id))

    city_name, time_utc, selected_days = list_value_notifications(message.from_user.id)

    text = f"Уведомление для города <b>{city_name}</b>{selected_days} в <b>{time_utc}</b> по UTC.\
    \n\nСтатус уведомления: <b>{status_notifications}</b>"

    bot.send_message(message.chat.id, text, parse_mode="html")


@bot.message_handler(regexp="🏙️ Города")
def cities_panel(message):
    bot.send_message(message.chat.id, "Настройки городов", reply_markup=markup_settings_cities)


@bot.message_handler(regexp="🌦️ Параметры погоды")
def weather_parameters_panel(message):
    list_settings = dbsettings.get_list_settings(message.from_user.id)
    markup_weather_parameters = buttons_weather_parameters(list_settings)
    bot.send_message(message.chat.id, "Список параметров:", reply_markup=markup_weather_parameters)


def changing_weather_parameters(callback, index):
    """
    Меняет выбранное значение параметра на противоположное (параметры погоды)
    """

    dbsettings.change_parameter(callback.from_user.id, int(get_number_value(index)))
    list_settings = dbsettings.get_list_settings(callback.from_user.id)
    markup_weather_parameters = buttons_weather_parameters(list_settings)

    try:  # Используется, если сообщение меняется на идентичное
        bot.edit_message_text("Список параметров:", callback.message.chat.id, callback.message.message_id,
                              reply_markup=markup_weather_parameters)
    except BaseException as e:
        print(e)


@bot.message_handler(regexp="↩️ Назад")  # Вернуться в Гланое меню
def return_start_panel(message):
    bot.send_message(message.chat.id, "Гланое меню", reply_markup=markup_start)


@bot.message_handler(regexp="↩️ Нaзад")  # Вернуться в Настройки
def return_settings_panel(message):
    bot.send_message(message.chat.id, "Настройки", reply_markup=markup_settings)


@bot.message_handler(regexp="Удалить город")
def delete_cities_panel(message):
    if dbcities.check_missing_cities(message.from_user.id) is False:
        erlst = list_sities_handler(message)
        markup_settings_cities_delete = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton(erlst[0], callback_data="delete_city01"),
            types.InlineKeyboardButton(erlst[1], callback_data="delete_city02"),
            types.InlineKeyboardButton(erlst[2], callback_data="delete_city03"),
            types.InlineKeyboardButton(erlst[3], callback_data="delete_city04"),
            types.InlineKeyboardButton(erlst[4], callback_data="delete_city05")
        )
        bot.send_message(message.chat.id, "Выберите город:", reply_markup=markup_settings_cities_delete)
    else:
        bot.send_message(message.chat.id, """<b>Список городов пуст</b>\
            \n\nУкажите город при помощи команды 'Добавить город'""", parse_mode="html")


def delete_city_database(callback, city_name):
    """
    Обработка выбранного города, перед удалением из базы данных пользователя
    """

    if city_name != "Error_delete":  # Error_delete значит город уже был удален (ячейка с городом пуста)
        bot.edit_message_text(f"Город {city_name} <b>удален</b> из списка", callback.message.chat.id,
                              callback.message.message_id, parse_mode="html")
    else:
        bot.edit_message_text("Данного города уже нет в списке", callback.message.chat.id, callback.message.message_id)


@bot.message_handler(regexp="Список моих городов")
def list_cities_panel(message):
    if dbcities.check_missing_cities(message.from_user.id) is False:
        bot.send_message(message.chat.id, f"<b>Список городов:</b>\n\n{list_sities_handler_client(message)}", parse_mode="html")
    else:
        bot.send_message(message.chat.id, "<b>Список городов пуст</b>\n\nУкажите город при помощи команды 'Добавить город'", parse_mode="html")


@bot.message_handler(regexp="Добавить город")
def add_cities_panel(message):
    if dbcities.check_max_numbers(message.from_user.id) is False:
        bot.send_message(message.chat.id, "Введите название города")
        bot.register_next_step_handler(message, add_city_handler)
    else:
        bot.send_message(message.chat.id, f"""К сожалению, Вы <b>достигли лимита</b> добавленных городов. Для добавления нового города, надо удалить один из старых.\
            \n\n<b>Ваш список городов:</b>\n\n{list_sities_handler_client(message)}""", reply_markup=markup_settings_cities, parse_mode="html")


def add_city_handler(message):
    """
    Полная обработка города, до внесения его в базу данных пользователя:
    """

    list_commands_add_cities_panel = (
        "Добавить город",
        "Удалить город",
        "Список моих городов",
        "/start",
        "↩️ нaзад"
    )

    message_from_user = message.text.strip().capitalize()
    weather_fromsite = requests.get(f"""https://api.openweathermap.org/data/2.5/weather?q={message_from_user}&appid={API_weather}&lang=ru&units=metric""")
    weather_answer = json.loads(weather_fromsite.text)

    if weather_fromsite.status_code == 200:  # Статус 200 = сайт распознал введенный пользователем город
        city_name = weather_answer['name']
        if dbcities.check_duplicate(message.from_user.id, city_name) is False:
            dbcities.add_city(message.from_user.id, city_name)
            bot.send_message(message.chat.id, f"Город {city_name} <b>добавлен</b> в список", reply_markup=markup_settings_cities, parse_mode="html")
        else:
            bot.send_message(message.chat.id,
                             f"Данный город уже есть в списке.\n\n<b>Ваш список городов:</b>\n\n{list_sities_handler_client(message)}",
                             reply_markup=markup_settings_cities, parse_mode="html")

    elif message_from_user in list_commands_add_cities_panel:
        if message_from_user == "↩️ нaзад":
            return_settings_panel(message)
        elif message_from_user == "Добавить город":
            add_cities_panel(message)
        elif message_from_user == "Удалить город":
            delete_cities_panel(message)
        elif message_from_user == "Список моих городов":
            list_cities_panel(message)
        elif message_from_user == "/start":
            start_panel(message)

    else:
        bot.send_message(message.chat.id, "К сожалению, я данного города не знаю", reply_markup=markup_settings_cities)


@bot.message_handler(content_types=['text'])
def other_regexp(message):
    bot.send_message(message.chat.id, "Я вас не понял. Попробуйте воспользоваться кнопками. Если их нет, нажмите на /start", reply_markup=markup_start)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    index = callback.data
    if index.startswith("delete"):
        dictionary_delete_callback = {
            "delete_city01": 1,
            "delete_city02": 2,
            "delete_city03": 3,
            "delete_city04": 4,
            "delete_city05": 5
        }
        city_name = dbcities.delete_city(callback.from_user.id, dictionary_delete_callback.get(index))
        delete_city_database(callback, city_name)

    elif index.startswith("find"):
        dictionary_find_weather_callback = {
            "find_weather_city01": 0,
            "find_weather_city02": 1,
            "find_weather_city03": 2,
            "find_weather_city04": 3,
            "find_weather_city05": 4
        }
        city_name = dbcities.list_cities(callback.from_user.id)[dictionary_find_weather_callback.get(index)]
        get_weather(callback.from_user.id, callback.message.message_id, callback.message.chat.id, city_name, "callback")

    elif index.startswith("weather"):
        changing_weather_parameters(callback, index)

    elif index.startswith("notif"):
        subsection = index.split("|")[1]
        ending = index.split("|")[2]

        if subsection == "city_panel":
            dbnotif.add_city(callback.from_user.id, ending)
            get_days_notification(callback)

        elif subsection == "days_panel":
            if ending == "every_day":
                dbnotif.change_all_days(callback.from_user.id, 1)
                get_time_clock_notification(callback)
            elif ending == "select_days_week":
                select_days_week(callback)

        elif subsection == "accept_panel":
            if dbnotif.get_day_click_status(callback.from_user.id).count(1) == 0:
                bot.answer_callback_query(callback.id, 'Выберите хотя бы один день')
            else:
                get_time_clock_notification(callback)

        elif subsection == "back_panel":
            if ending == "back_01":
                add_notifications_panel(callback, "callback")
            elif ending == "back_02":
                get_days_notification(callback)
            elif ending == "back_03":
                get_days_notification(callback)
            elif ending == "back_04":
                get_time_clock_notification(callback)

        elif subsection == "week_panel":
            dictionary_day_week = {
                1: "Monday",
                2: "Tuesday",
                3: "Wednesday",
                4: "Thursday",
                5: "Friday",
                6: "Saturday",
                7: "Sunday"
            }

            dbnotif.add_selected_day(callback.from_user.id, dictionary_day_week.get(int(ending[-1])))
            select_days_week(callback)

        elif subsection == "time_clock_panel":
            get_time_minutes_notification(callback, ending[-2:])

        elif subsection == "time_minutes_panel":
            dbnotif.add_dispatch_time_utc(callback.from_user.id, ending[-4:])
            end_notification(callback)


def schedule_job():
    '''
    Каждую минуту бот проверяет текущее время, на совпадение со временем отправки уведомлений в базе данных пользователей
    '''

    notifications = dbnotif.get_notifications()
    for element in notifications:
        if element[2] == datetime.datetime.fromtimestamp(time.time(), datetime.UTC).strftime("%H%M"):
            get_weather(user_id=element[0], chat_id=element[1], message_id=None, city_name=element[3])


def schedule_start_job():
    """
    Запуск функции schedule_job каждую минуту в :00
    """

    schedule.every().minute.at(":00").do(schedule_job)
    while True:
        schedule.run_pending()
        time.sleep(1)


Thread(target=schedule_start_job).start()


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(10)
