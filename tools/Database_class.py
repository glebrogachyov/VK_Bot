import pandas as pd
import os
import re
import requests
from settings.db_config import *
from settings.messages import balance_found, balance_not_found, multiple_balance_found


class Database:
    def __init__(self):
        self.incorrect_numbers = 0
        self.database: pd.DataFrame = pd.DataFrame({"phone": [None], "balance": [None]})

    def init_table(self, db_path=excel_file_path):
        try:
            tmp_table = pd.read_excel(io=db_path,
                                      header=None,
                                      sheet_name=excel_sheet_name,
                                      skiprows=excel_first_useful_row-1,
                                      usecols=excel_useful_columns,
                                      names=["phone", "balance"],
                                      converters={"phone": str, "balance": str})
            tmp_table["balance"].fillna("0", inplace=True)
        except FileNotFoundError as e:
            return False, f"Не найден файл.\nОшибка: {e}"
        except Exception as e:
            return False, f"Не удалось прочитать таблицу.\nОшибка: {e}"
        self.database = tmp_table
        self.normalize_table()
        resp_text = f"Таблица балансов успешно обновлена.\n" \
                    f"Число записей: {len(self.database)}.\n" \
                    f"Число номеров, которые не удалось нормализовать: {self.incorrect_numbers}.\n"
        return True, resp_text

    def update_table(self, doc_url):
        try:
            tmp_file = requests.get(doc_url)
            open(tmp_file_path, "wb").write(tmp_file.content)
            response = self.init_table(tmp_file_path)
            os.remove(excel_file_path)  # удаляем старую таблицу
            os.rename(tmp_file_path, excel_file_path)   # переименовываем файл новой таблицы, делаем его основным
        except OSError as e:
            return False, f"Ошибка обновления таблицы:\n{e}"
        except Exception as e:
            return False, f"Ошибка обновления таблицы:\n{e}"

        return response

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

    def normalize_table(self):
        self.incorrect_numbers = 0
        self.database["phone"] = self.database["phone"].apply(self.normalize_phone)

    def get_balance_by_phone(self, phone_number: str) -> int or None:
        phone_number = self.normalize_phone(phone_number)
        df = self.database
        index = df.index[df["phone"] == phone_number]
        query = self.database.loc[index]
        if len(query) == 1:
            return balance_found.format(phone_number, query.iloc[0]['balance'])
        elif len(query) > 1:
            return multiple_balance_found.format(phone_number, ', '.join([q for q in query['balance']]))
        else:
            return balance_not_found.format(phone_number)
