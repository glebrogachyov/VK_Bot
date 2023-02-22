import os
from datetime import datetime, timedelta
import pandas as pd
import re

from storage.settings.db_config import *
from storage.settings.messages import balance_found, balance_not_found, multiple_balance_found, too_many_balances


class Database:
    def __init__(self):
        self.incorrect_numbers = 0
        self.tmp_table = None
        self.database: pd.DataFrame = pd.DataFrame({"phone": [None], "balance": [None]})
        self.day_created = None

    @staticmethod
    def remove_db_files(filenames):
        for file in filenames:
            os.remove(data_folder + file)

    def init_table(self, force_update=False):
        try:
            csv_files = [filename for filename in os.listdir(data_folder) if "Остатки по дисконтным картам на"
                         in filename and filename.endswith(".csv")]
            if not csv_files:
                return False, f"В директории нет файлов с балансами пользователей"

            csv_files.sort(key=lambda f: os.path.getmtime(data_folder + f))

            db_path = data_folder + csv_files[-1]
            self.remove_db_files(csv_files[:-2])
            file_date = datetime.utcfromtimestamp(os.path.getmtime(db_path)) + timedelta(hours=timezone_hours)
            table_day_created = datetime.date(file_date).strftime(date_format)
            if table_day_created == self.day_created and not force_update:
                return False, "В директории не появилось файла новее, чем тот, что был загружен в память"

            self.tmp_table = pd.read_csv(filepath_or_buffer=db_path,
                                         sep=csv_separator,
                                         encoding=csv_encoding,
                                         names=["phone", "balance"],
                                         converters={"phone": str, "balance": str})

            self.tmp_table["balance"].fillna("0", inplace=True)

            rows_read = self.tmp_table["phone"].describe()["count"]
            unique_rows = self.tmp_table["phone"].describe()["unique"]

        except FileNotFoundError as e:
            return False, f"Не найден файл с балансами пользователей.\nОшибка: {e}"
        except Exception as e:
            return False, f"Не удалось прочитать таблицу.\nОшибка: {e}"

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
            resp_flag, resp_text = False, f"pandas: ошибка обновления таблицы, упала на тестах:\n{e}"
        except Exception as e:
            resp_flag, resp_text = False, f"Ошибка обновления таблицы:\n{e}"

        self.database, self.tmp_table = self.tmp_table, None
        self.day_created = table_day_created

        return True, resp_text

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
