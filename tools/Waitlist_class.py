from typing import Literal
import pickle
import os
allowed_values = Literal["email", "phone", "reg", "ask", "cheque", "admin_new_db"]
pkl_path = {"email": "email.pkl",
            "phone": "phone_number.pkl",
            "reg": "register_info.pkl",
            "ask": "ask_manager.pkl",
            "cheque": "cheque.pkl",
            "admin_new_db": "new_db.pkl"}


class WaitList:
    def __init__(self):
        self.email = unpickle(pkl_path["email"])
        self.phone_number = unpickle(pkl_path["phone"])
        self.register_info = unpickle(pkl_path["reg"])
        self.ask_manager = unpickle(pkl_path["ask"])
        self.cheque = unpickle(pkl_path["cheque"])
        self.new_db = unpickle(pkl_path["admin_new_db"])
        self.aliases = {"email": self.email,
                        "phone": self.phone_number,
                        "reg": self.register_info,
                        "ask": self.ask_manager,
                        "cheque": self.cheque,
                        "admin_new_db": self.new_db}
        # self.printer()

    def add_user_to_waitlist(self, user_id, list_alias: allowed_values, val=True):
        self.aliases[list_alias][user_id] = val
        with open("pickles/" + pkl_path[list_alias], "wb") as file:
            pickle.dump(self.aliases[list_alias], file)

    def user_waitlist_reset(self, user_id):
        for list_alias, waitlist in self.aliases.items():
            if user_id in waitlist:
                waitlist.pop(user_id)
                with open("pickles/" + pkl_path[list_alias], "wb") as file:
                    pickle.dump(self.aliases[list_alias], file)

    def get_user_data(self, user_id, list_alias: allowed_values):
        return self.aliases[list_alias].get(user_id)

    def printer(self):
        for alias in self.aliases:
            print(f"{alias: <7}: {self.aliases[alias]}")


def unpickle(filename):
    if filename in os.listdir("pickles"):
        with open("pickles/"+filename, "rb") as file:
            return pickle.load(file)
    return dict()
