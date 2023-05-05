from server import Bot
from services.logger import logger
import requests
import time
from storage.settings.config import token, group_id


@logger.catch
def main():
    while True:
        try:
            bot = Bot(token, group_id)
            logger.info("Запуск бота")
            bot.start()
        except requests.exceptions.RequestException:
            logger.error("Бот остановлен. err: ConnectionError")
        except Exception as e:
            logger.error("Бот остановлен. err: " + repr(e))
        except BaseException as be:
            logger.error("Бот остановлен. err be: " + repr(be))
        finally:
            time.sleep(1)


if __name__ == '__main__':
    main()
