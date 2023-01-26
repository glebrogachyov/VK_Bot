from typing import Literal


class WaitList:
    def __init__(self):
        self.email = dict()
        self.phone_number = dict()
        self.register_info = dict()
        self.ask_manager = dict()
        self.cheque_photo = dict()
        self.aliases = {"email": self.email,
                        "phone": self.phone_number,
                        "reg": self.register_info,
                        "ask": self.ask_manager,
                        "cheque": self.cheque_photo}

    def add_user_to_waitlist(self, user_id, list_alias: Literal["email", "phone", "reg", "ask", "cheque"], val=True):
        self.aliases[list_alias][user_id] = val

    def user_waitlist_reset(self, user_id):
        for waitlist in (self.email, self.cheque_photo, self.register_info, self.ask_manager, self.phone_number):
            if user_id in waitlist:
                waitlist.pop(user_id)

    def get_user_data(self, user_id, list_alias: Literal["email", "phone", "reg", "ask", "cheque"]):
        return self.aliases[list_alias].get(user_id)

    def printer(self):
        for alias in self.aliases:
            print(f"{alias: <7}: {self.aliases[alias]}")
