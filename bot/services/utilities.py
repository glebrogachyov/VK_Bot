import os
from datetime import date, datetime, timedelta

from storage.settings.time_settings import timezone_hours


def remove_files(folder, filenames):
    for file in filenames:
        os.remove(folder + file)


def clear_folder(folder):
    for file in os.listdir(folder):
        os.remove(folder + file)


def get_files_list_sorted(folder, filename_part):
    csv_files = [filename for filename in os.listdir(folder) if filename_part in filename and filename.endswith(".csv")]
    csv_files.sort(key=lambda f: os.path.getmtime(folder + f))
    return csv_files


def get_file_creation_date(path_to_file):
    return datetime.utcfromtimestamp(os.path.getmtime(path_to_file)) + timedelta(hours=timezone_hours)


def get_correct_datetime():
    return datetime.utcnow() + timedelta(hours=timezone_hours)


def get_object_classname(obj):
    return str(obj.__class__).strip("<>'").split(".", 1)[-1]


def calculate_sleep_time(wake_up_hour, wake_up_minute):
    dt_now = get_correct_datetime()

    current_time_in_secs = dt_now.hour * 60 * 60 + dt_now.minute * 60 + dt_now.second
    wake_up_time_in_secs = wake_up_hour * 60 * 60 + wake_up_minute * 60

    time_difference_abs = abs(current_time_in_secs - wake_up_time_in_secs)

    if current_time_in_secs < wake_up_time_in_secs:
        return time_difference_abs

    else:
        return 24 * 60 * 60 - time_difference_abs
