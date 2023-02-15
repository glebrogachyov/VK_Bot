from os import path
import pandas as pd

from storage.settings.messages import contest_already_in_list, contest_added_to_list

from services.logger import logger

contest_folder = "storage/contest/"
contest_filename = "contest_participants.csv"
filepath = contest_folder + contest_filename


class Contest:
    def __init__(self):
        if path.isfile(filepath) and path.getsize(filepath) > 0:
            logger.info("Прочитан файл участников конкурса")
            self.participants = pd.read_csv(filepath, dtype=int)
        else:
            logger.info("Создана таблица участников конкурса")
            self.participants = pd.Series(name="user id", dtype=int)

    def add_participant(self, user_id):
        if user_id in self.participants.values:
            return contest_already_in_list
        else:
            self.participants.loc[len(self.participants)] = user_id
            self.participants.to_csv(filepath, index=False)
            return contest_added_to_list
