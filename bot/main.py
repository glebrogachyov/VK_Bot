from server import Bot, logger
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
            logger.error("Бот остановлен. e: ConnectionError")
            time.sleep(1)
            continue
        except Exception as e:
            time.sleep(1)
            logger.error("Бот остановлен. e: " + repr(e))
            continue
        except BaseException as be:
            time.sleep(1)
            logger.error("Бот остановлен. be: " + repr(be))
            continue


if __name__ == '__main__':
    main()
