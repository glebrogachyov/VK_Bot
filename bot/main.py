from requests.exceptions import ConnectionError

from server import Bot
from services.logger import logger
from storage.settings.config import token, group_id


def main():
    try:
        bot = Bot(token, group_id)
        logger.info("Запуск бота")
        bot.start()
    except ConnectionError as ce:
        logger.error(f"Бот умер. Ошибка с подключением к сети: \n\t{ce}")
    except Exception as e:
        logger.error(f"Бот умер. Ошибка: \n\t{e}")


if __name__ == '__main__':
    main()
