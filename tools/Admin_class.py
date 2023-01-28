import json
import os


class Admin:
    def __init__(self):
        self.admin_file = "settings/admin_list.json"
        self.manager_file = "settings/admin_manager.json"
        self.admin_list = []
        self.manager = None
        self.load_from_json()
        if not self.manager:
            self.manager = self.admin_list[0]

    def load_from_json(self):
        if "admin_list.json" not in os.listdir("settings"):
            exit("Ошибка. Файл 'admins.json' отсутствует в папке settings")

        try:
            with open(self.admin_file, "r") as fp:
                data = json.load(fp)
                self.admin_list = data.get("admin_list")
                if not self.admin_list:
                    exit("Пустой список администраторов.")
            if "admin_manager.json" in os.listdir("settings"):
                with open(self.manager_file, "r") as fp:
                    data = json.load(fp)
                    self.manager = data.get("manager_id")

        except json.JSONDecodeError:
            exit("Ошибка во время чтения файла 'settings/admin_list.json' или 'settings/admin_manager.json'.")
        except Exception as e:
            exit(f"Ошибка во время чтения файла 'settings/admin_list.json' или 'settings/admin_manager.json'.\n{e}")

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
