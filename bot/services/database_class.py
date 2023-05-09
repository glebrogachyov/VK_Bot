import os
from datetime import datetime
import pandas as pd
import re

from storage.settings.db_config import db_folder, csv_encoding, csv_separator, date_format, test_phones
from storage.settings.messages import balance_found, balance_not_found, multiple_balance_found, too_many_balances
from services.utilities import remove_files, get_files_list_sorted, get_file_creation_date

keep_files_amount = 2


class Database:
    def __init__(self, logger=None, notification_sender=None):
        self.incorrect_numbers = 0
        self.tmp_table = None
        self.database: pd.DataFrame = pd.DataFrame({"phone": [None], "balance": [None]})
        self.day_created = None

        self.logger = logger
        self.notification_sender = notification_sender

    def load_data(self, admin_update_notify_by=None, auto_update=False):
        try:
            csv_files = get_files_list_sorted(db_folder, "Остатки по дисконтным картам на")
            remove_files(db_folder, csv_files[:-keep_files_amount])

            db_path = db_folder + csv_files[-1]
            file_date = get_file_creation_date(db_path)
            table_day_created = datetime.date(file_date).strftime(date_format)

            if table_day_created == self.day_created and not admin_update_notify_by:
                self.logger.info("[Database] В директории не появилось файла новее, чем тот, что был загружен в память")
                return

            self.tmp_table = pd.read_csv(filepath_or_buffer=db_path, sep=csv_separator, encoding=csv_encoding,
                                         names=["phone", "balance"], converters={"phone": str, "balance": str})
            self.tmp_table["balance"].fillna("0", inplace=True)

            rows_read = self.tmp_table["phone"].describe()["count"]
            unique_rows = self.tmp_table["phone"].describe()["unique"]

        except FileNotFoundError as e:
            error_text = f"[Database] Не найден файл с балансами пользователей.\n\tОшибка: {e}"
            self.logger.error(error_text)
            if admin_update_notify_by:
                self.notification_sender(to_user=admin_update_notify_by, message=error_text)
            return
        except Exception as e:
            error_text = f"[Database] Не удалось прочитать таблицу.\n\tОшибка: {e}"
            self.logger.error(error_text)
            if admin_update_notify_by:
                self.notification_sender(to_user=admin_update_notify_by, message=error_text)
            return

        self.normalize_table(self.tmp_table)

        resp_text = f"Таблица балансов успешно обновлена.\n" \
                    f"Прочитано строк: {rows_read}.\n" \
                    f"Найдено уникальных номеров: {unique_rows}.\n" \
                    f"Число номеров, которые не удалось нормализовать: {self.incorrect_numbers}.\n" \
                    f"- - -\nТестовые запросы к таблице:\n- - -"

        # Блок тестовых запросов к новой таблице - если они не выпадут с ошибкой, тогда вряд ли она вообще упадёт
        try:
            for test_number in test_phones:
                test_res = self.get_balance_by_phone(phone_number=test_number, df=self.tmp_table)[0]
                resp_text += f'\nВведённый номер:  "{test_number}"\n{test_res}- - - '
        except pd.errors.IndexingError as e:
            error_text = f"[Database] pandas: ошибка обновления таблицы, упала на тестах:\n\t{e}"
            self.logger.error(error_text)
            if admin_update_notify_by:
                self.notification_sender(to_user=admin_update_notify_by, message=error_text)
            return
        except Exception as e:
            error_text = f"[Database] Ошибка обновления таблицы на этапе тестовых запросов:\n\t{e}"
            self.logger.error(error_text)
            if admin_update_notify_by:
                self.notification_sender(to_user=admin_update_notify_by, message=error_text)
            return

        self.database, self.tmp_table = self.tmp_table, None
        self.day_created = table_day_created

        if admin_update_notify_by:
            self.logger.info("[Database] Обновление базы данных, запущенное администратором, прошло успешно")
            self.notification_sender(to_user=admin_update_notify_by, message=resp_text)
        elif auto_update:
            self.logger.info("[Database] Автоматическое обновление базы данных прошло успешно")
        else:
            self.logger.info("[Database] База данных успешно загружена в память")
        return

    def normalize_phone(self, phone_number: str) -> str:
        if type(phone_number) is not str:
            self.incorrect_numbers += 1
            return phone_number
        phone_number = re.sub(r"[^\d]", "", phone_number)
        if re.search(r"[^-+() \t\d]", phone_number) is None:
            if len(phone_number) == 11:
                if phone_number[0] == "7":
                    phone_number = "8" + phone_number[1:]
                if phone_number[0] != "8":
                    self.incorrect_numbers += 1
            elif len(phone_number) == 10:
                if phone_number[0] == "9":
                    phone_number = "8" + phone_number
                if phone_number[0] != "8":
                    self.incorrect_numbers += 1
            else:
                self.incorrect_numbers += 1
        return phone_number

    def normalize_table(self, database):
        self.incorrect_numbers = 0
        database["phone"] = database["phone"].apply(self.normalize_phone)

    def get_balance_by_phone(self, phone_number: str, df=...):
        phone_number = self.normalize_phone(phone_number)
        if df is ...:
            df = self.database
        index = df.index[df["phone"] == phone_number]
        query = df.loc[index]
        if len(query) == 1:
            return balance_found.format(phone_number, query.iloc[0]['balance']), False
        elif 1 < len(query) < 4:
            return multiple_balance_found.format(phone_number, '; '.join([q for q in query['balance']])), True
        elif len(query) > 3:
            return too_many_balances.format(phone_number), True
        else:
            return balance_not_found.format(phone_number), False
