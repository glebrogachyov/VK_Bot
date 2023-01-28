import json
import os


class Admin:
    def __init__(self):
        self.file_path = "settings/admins.json"
        self.admin_list = []
        self.manager = None
        self.load_from_json()

    def load_from_json(self):
        if "admins.json" not in os.listdir("settings"):
            exit("Ошибка. Файл 'admins.json' отсутствует в папке settings")
        try:
            with open(self.file_path, "r") as fp:
                data = json.load(fp)
            self.admin_list = data.get("admin_id_list")
            self.manager = data.get("manager_id")
            return "Список администраторов прочитан успешно."
        except json.JSONDecodeError:
            exit("Ошибка во время чтения файла 'settings/admins.json'.")

    def write_to_json(self):
        data = {"admin_id_list": self.admin_list, "manager_id": self.manager}
        with open(self.file_path, "w") as fp:
            json.dump(data, fp)

    def change_manager(self, index_in_admin_list: int):
        if index_in_admin_list < len(self.admin_list):
            self.manager = self.admin_list[index_in_admin_list]
            self.write_to_json()
            return "Менеджер назначен."
        return "Ошибка. Повторите ещё раз или проверьте файлы настроек."
