from server import Bot
import requests
from settings.config import token, group_id

bot = Bot(token, group_id)

bot.start()

while True:
    try:
        # добавить чтение pickle для десериализации данных с прошлого запуска (добавить проверку условия, что файл есть)
        print("Бот поднялся.")
        bot.start()
    except requests.exceptions.RequestException:  # любая ошибка requests
        print('ConnectionError')
        continue
    except Exception as e:  # тут бы обработку получше сделать а то шляпа какая-то, надо конкретные исключения ловить
        print("Бот упал.\nОшибка: ", e)
