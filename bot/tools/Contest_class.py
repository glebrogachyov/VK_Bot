import os
import pandas as pd

from settings.messages import contest_already_in_list, contest_added_to_list


class Contest:
    def __init__(self):
        if "contest_participants.csv" in os.listdir("tmp_files/contest"):
            print("Прочитан файл участников конкурса")
            self.participants = pd.read_csv("tmp_files/contest/contest_participants.csv", dtype=int)
        else:
            print("Создана таблица участников конкурса")
            self.participants = pd.Series(name="user id", dtype=int)

    def add_participant(self, user_id):
        if user_id in self.participants.values:
            return contest_already_in_list
        else:
            self.participants.loc[len(self.participants)] = user_id
            self.participants.to_csv("tmp_files/contest/contest_participants.csv", index=False)
            return contest_added_to_list
