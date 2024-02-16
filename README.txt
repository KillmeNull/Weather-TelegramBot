1) Для работы программы у вас должны быть 2 API ключа:
	
	 1. API ключ телеграмм бота (есть много видео как его получить)
	
	 2. API ключ онлайн сервера OpenWeatherMap, откуда берётся вся информация о погоде (есть много видео как его получить)


2) Далее вы дожны создать файл ".env" в той же папке, где у вас находится файл "main_bot.py", в который надо поместить 2 API ключа в таком формате:

	API_TELEGRAMBOT = "сюда вставляем API ключ"
	API_OPENWEATHERMAP = "сюда вставляем API ключ"

	Ковычки обязательны!!!


3) Далее в файле ".env" вы должны создать переменную PATH_DATABASE и указать путь до файла "database.db":

	Пример:
	PATH_DATABASE = "C:\\Users\\User\\Documents\\telegram_bot\\database_files\\database.db"

	Обязательно используйте \\, чтобы разделить папки!!!


4) Установите все нужные библиотеки, для работы программы.
	
	pip install pyTelegramBotAPI
	pip install python-dotenv
	pip install requests
	pip install schedule
	

5) Запустить файл "main_bot.py" для начала старта бота
