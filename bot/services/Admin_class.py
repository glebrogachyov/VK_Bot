import json
import os


data_folder = "storage/settings/"
admin_filename = "admin_list.json"
manager_filename = "admin_manager.json"


class Admin:
    def __init__(self):
        self.admin_file = data_folder + admin_filename
        self.manager_file = data_folder + manager_filename
        self.admin_list = []
        self.manager = None
        self.load_from_json()
        if not self.manager:
            self.manager = self.admin_list[0]

    def load_from_json(self):
        if admin_filename not in os.listdir(data_folder):
            exit("Ошибка. Файл 'admins.json' отсутствует в папке settings")

        try:
            with open(self.admin_file, "r") as fp:
                data = json.load(fp)
                self.admin_list = data.get("admin_list")
                if not self.admin_list:
                    exit("Пустой список администраторов.")
            if admin_filename in os.listdir(data_folder):
                with open(self.manager_file, "r") as fp:
                    data = json.load(fp)
                    self.manager = data.get("manager_id")

        except json.JSONDecodeError:
            exit("Ошибка во время чтения файла 'admin_list.json' или 'admin_manager.json'.")
        except Exception as e:
            exit(f"Ошибка во время чтения файла 'admin_list.json' или 'admin_manager.json'.\n{repr(e)}")

    def write_to_json(self):
        # with open(self.admin_file, "w") as fp:        # Раскомментировать если понадобится создать файл списка админов
        #     data = {"admin_list": self.admin_list}
        #     json.dump(data, fp)
        with open(self.manager_file, "w") as fp:
            data = {"manager_id": self.manager}
            json.dump(data, fp)

    def change_manager(self, index_in_admin_list: int):
        if index_in_admin_list < len(self.admin_list):
            self.manager = self.admin_list[index_in_admin_list]
            self.write_to_json()
            return "Менеджер назначен."
        return "Ошибка. Повторите ещё раз или проверьте файлы настроек."
