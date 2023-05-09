from threading import Thread, Lock
from time import sleep

from services.utilities import get_object_classname, calculate_sleep_time
from services.logger import logger


class DailyTaskDaemon:
    def __init__(self, target_obj, func_to_call: str, lock=Lock()):
        """
        :param worker_instance: Объект, с которым будет работать демон.
        :param function_to_call: Имя метода, который демон будет вызывать.
        """
        self.worker_instance = target_obj
        self.action_method = func_to_call
        self.lock = lock
        self.daemon = None

    def do_action_then_sleep(self, action_time_hour, action_time_minutes, *args, **kwargs):
        while True:
            try:
                action_func = getattr(self.worker_instance, self.action_method)
                logger.info(f"[Daemon] Запуск процесса {self.action_method}")
                with self.lock:
                    action_func()
                while True:
                    time_to_sleep = calculate_sleep_time(action_time_hour, action_time_minutes)
                    hours_to_sleep = time_to_sleep // 3600
                    minutes_to_sleep = (time_to_sleep % 3600) // 60
                    worker_name = get_object_classname(self.worker_instance)
                    logger.info(f"[Daemon] {worker_name} засыпает на {hours_to_sleep} ч. {minutes_to_sleep} мин.")
                    sleep(time_to_sleep)
                    with self.lock:
                        action_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[Daemon] Ошибка во время работы процесса {get_object_classname(self.worker_instance)}.\n"
                             f"\terror: {repr(e)}\n"
                             f"\tПовторный перезапуск потока через минуту. Если не оживает - надо перезапускать бота.")

                sleep(60)

    def run_daily_task(self, action_time_hour: int, *args, action_time_minutes: int = 0, **kwargs):
        """
        Запускает демона
        :param action_time_hour: Час, в который каждый день будет вызываться указанный метод
        :param action_time_minutes: Минута, опциональный параметр, дефолт = 0
        :param args: Позиционные аргументы для проксирования в метод
        :param kwargs: Именованные аргументы для проксирования в метод
        :return:
        """
        logger.info(f"[Daemon] Старт демона {get_object_classname(self.worker_instance)}. "
                    f"Настроен ежедневный запуск в {action_time_hour:02}:{action_time_minutes:02}")
        args = (action_time_hour, action_time_minutes) + args
        self.daemon = Thread(target=self.do_action_then_sleep, args=args, kwargs=kwargs, daemon=True)
        self.daemon.start()
