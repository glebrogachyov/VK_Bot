from server import Bot
from settings.config import token, group_id

bot = Bot(token, group_id)

while True:
    try:
        bot.start()
    except Exception as e:
        print("Бот упал")
