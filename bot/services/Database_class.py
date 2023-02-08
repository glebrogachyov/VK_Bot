import pandas as pd
import os
import re
import requests

from storage.settings.db_config import *
from storage.settings.messages import balance_found, balance_not_found, multiple_balance_found, too_many_balances


class Database:
    def __init__(self):
        self.incorrect_numbers = 0
        self.tmp_table = None
        self.database: pd.DataFrame = pd.DataFrame({"phone": [None], "balance": [None]})

    def init_table(self, db_path=data_folder + excel_filename, first_load=False):
        try:
            self.tmp_table = pd.read_excel(io=db_path,
                                           header=None,
                                           skiprows=excel_first_useful_row-1,
                                           usecols=excel_useful_columns,
                                           names=["phone", "balance"],
                                           converters={"phone": str, "balance": str})
            self.tmp_table["balance"].fillna("0", inplace=True)
            rows_read = len(self.tmp_table)
        except FileNotFoundError as e:
            return False, f"Не найден файл.\nОшибка: {e}"
        except Exception as e:
            return False, f"Не удалось прочитать таблицу.\nОшибка: {e}"
        self.normalize_table(self.tmp_table)
        if first_load is True:
            self.database, self.tmp_table = self.tmp_table, None
        resp_text = f"Таблица балансов успешно обновлена.\n" \
                    f"Число записей: {rows_read}.\n" \
                    f"Число номеров, которые не удалось нормализовать: {self.incorrect_numbers}.\n" \
                    f"- - -\nТестовые запросы к таблице:\n- - -"
        return True, resp_text

    def update_table(self, doc_url):
        # Блок инициализации новой таблицы - если её получится прочитать, то она будет сохранена как временная
        try:
            tmp_file = requests.get(doc_url)
            open(data_folder + tmp_filename, "wb").write(tmp_file.content)
            resp_flag, resp_text = self.init_table(data_folder + tmp_filename)
        except OSError as e:
            return False, f"Ошибка обновления таблицы:\n{e}"
        except Exception as e:
            return False, f"Ошибка обновления таблицы:\n{e}"

        if resp_flag is False:
            os.remove(data_folder + tmp_filename)  # удаляем старую таблицу
            return resp_flag, resp_text

        # Блок тестовых запросов к новой таблице - если они не выпадут с ошибкой, тогда вряд ли она вообще упадёт
        try:
            for test_number in test_phones:
                test_res = self.get_balance_by_phone(phone_number=test_number, df=self.tmp_table)[0]
                resp_text += f'\n\nВведённый номер:  "{test_number}"\nРезультат:\n{test_res}- - - '
        except pd.errors.IndexingError as e:
            resp_flag, resp_text = False, f"Ошибка обновления таблицы:\n{e}"
        except Exception as e:
            resp_flag, resp_text = False, f"Ошибка обновления таблицы:\n{e}"

        # Если на предыдущих этапах таблица не упала, тогда удаляем старую. Иначе удаляем новую и ничего не меняем
        if resp_flag:
            self.database, self.tmp_table = self.tmp_table, None
            if excel_filename in os.listdir(data_folder):
                os.remove(data_folder + excel_filename)
            os.rename(data_folder + tmp_filename, data_folder + excel_filename)
        else:
            os.remove(data_folder + tmp_filename)  # удаляем новую таблицу
        return resp_flag, resp_text

    def normalize_phone(self, phone_number: str) -> str:
        if type(phone_number) is not str:
            self.incorrect_numbers += 1
            # print("incorrect number:", phone_number)
            return phone_number
        phone_number = re.sub(r"[^\d]", "", phone_number)
        if re.search(r"[^-+() \t\d]", phone_number) is None:
            if len(phone_number) == 11:
                if phone_number[0] == "7":
                    phone_number = "8" + phone_number[1:]
                if phone_number[0] != "8":
                    # print("incorrect number:", phone_number)
                    self.incorrect_numbers += 1
            elif len(phone_number) == 10:
                if phone_number[0] == "9":
                    phone_number = "8" + phone_number
                if phone_number[0] != "8":
                    self.incorrect_numbers += 1
                    # print("incorrect number:", phone_number)
            else:
                self.incorrect_numbers += 1
                # print("incorrect number:", phone_number)
        return phone_number

    def normalize_table(self, database):
        self.incorrect_numbers = 0
        database["phone"] = database["phone"].apply(self.normalize_phone)

    def get_balance_by_phone(self, phone_number: str, df=...) -> int or None:
        phone_number = self.normalize_phone(phone_number)
        if df is ...:
            df = self.database
        index = df.index[df["phone"] == phone_number]
        query = df.loc[index]
        if len(query) == 1:
            return balance_found.format(phone_number, query.iloc[0]['balance']), False
        elif 1 < len(query) < 6:
            return multiple_balance_found.format(phone_number, ', '.join([q for q in query['balance']])), True
        elif len(query) > 5:
            return too_many_balances.format(phone_number), True
        else:
            return balance_not_found.format(phone_number), False
