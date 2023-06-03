from time import sleep

from storage.settings.messages import mailer_msg
from storage.settings.mailer_config import mailer_folder
from storage.settings.time_settings import mailing_hour, mailing_minutes
from services.utilities import remove_files, get_files_list_sorted, get_file_creation_date, get_correct_datetime
from services.logger import logger


class Mailer:
    def __init__(self, sender_function):
        self.mailing_list = set()
        self.folder_path = mailer_folder
        self.sender = sender_function

    def get_file_created_today_and_remove_other(self, filename_startswith):
        csv_files = get_files_list_sorted(mailer_folder, filename_startswith)
        if not csv_files:
            return None

        latest_file_name = csv_files[-1]
        file_creation_date = get_file_creation_date(mailer_folder+latest_file_name)
        is_file_created_today = get_correct_datetime().date() == file_creation_date.date()

        files_to_remove = csv_files[:-1] if is_file_created_today else csv_files
        remove_files(folder=mailer_folder, filenames=files_to_remove)

        res = latest_file_name if is_file_created_today else None
        return res

    def get_set_from_csv(self, filename):
        with open(self.folder_path + filename) as file:
            result = set()
            for row in file:
                row = row.strip()
                if row:
                    split_row = row.strip().split(";")
                    result.add(tuple(map(int, split_row)))
            return result

    def write_mailed_user_to_file(self, user_id, phone_number):
        with open(mailer_folder + "tmp.csv", "a") as file:
            file.write(f"{user_id};{phone_number}\n")

    def build_current_day_mailing_list(self):
        time_now = get_correct_datetime()
        if time_now.hour * 60 + time_now.minute < mailing_hour * 60 + mailing_minutes:
            self.mailing_list = set()
            return

        mailing_list_csv = self.get_file_created_today_and_remove_other(filename_startswith='День рождения')
        already_mailed_csv = self.get_file_created_today_and_remove_other(filename_startswith='tmp')

        mailing_list_set = self.get_set_from_csv(mailing_list_csv) if mailing_list_csv else set()
        already_mailed_set = self.get_set_from_csv(already_mailed_csv) if already_mailed_csv else set()

        self.mailing_list = mailing_list_set - already_mailed_set
        return

    def do_mailing(self):
        logger.info("[Mailer] Сборка списка рассылки.")

        self.build_current_day_mailing_list()
        if not self.mailing_list:
            logger.info("[Mailer] Список рассылки пуст.")

        while self.mailing_list:  # выход из цикла произойдёт, когда в списке отправленных будут все запланированные
            for user_id, phone_number in self.mailing_list:
                logger.info(f"[Mailer] Попытка отправки сообщения пользователю id{user_id}.")
                self.sender(to_user=user_id, message=mailer_msg.format(phone_number))
                sleep(0.05)
                self.write_mailed_user_to_file(user_id, phone_number)
            self.build_current_day_mailing_list()

        logger.info("[Mailer] Выход из функции рассылки.")

