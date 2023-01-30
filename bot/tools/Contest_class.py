import os
import pandas as pd

from storage.settings.messages import contest_already_in_list, contest_added_to_list

contest_folder = "storage/contest/"
contest_filename = "contest_participants.csv"


class Contest:
    def __init__(self):
        if contest_filename in os.listdir(contest_folder):
            print("Прочитан файл участников конкурса")
            self.participants = pd.read_csv(contest_folder + contest_filename, dtype=int)
        else:
            print("Создана таблица участников конкурса")
            self.participants = pd.Series(name="user id", dtype=int)

    def add_participant(self, user_id):
        if user_id in self.participants.values:
            return contest_already_in_list
        else:
            self.participants.loc[len(self.participants)] = user_id
            self.participants.to_csv(contest_folder + contest_filename, index=False)
            return contest_added_to_list
