from typing import Literal
import pickle
import os

allowed_values = Literal["email", "phone", "reg", "ask", "cheque"]

pkl_folder = "storage/pickles/"
pkl_filename = {"email": "email.pkl",
                "phone": "phone_number.pkl",
                "reg": "register_info.pkl",
                "ask": "ask_manager.pkl",
                "cheque": "cheque.pkl"}


class WaitList:
    def __init__(self):
        self.email = unpickle(pkl_filename["email"])
        self.phone_number = unpickle(pkl_filename["phone"])
        self.register_info = unpickle(pkl_filename["reg"])
        self.ask_manager = unpickle(pkl_filename["ask"])
        self.cheque = unpickle(pkl_filename["cheque"])
        self.aliases = {"email": self.email,
                        "phone": self.phone_number,
                        "reg": self.register_info,
                        "ask": self.ask_manager,
                        "cheque": self.cheque}

    def add_user_to_waitlist(self, user_id, list_alias: allowed_values, val=True):
        self.aliases[list_alias][user_id] = val
        with open(pkl_folder + pkl_filename[list_alias], "wb") as file:
            pickle.dump(self.aliases[list_alias], file)

    def user_waitlist_reset(self, user_id):
        for list_alias, waitlist in self.aliases.items():
            if user_id in waitlist:
                waitlist.pop(user_id)
                with open(pkl_folder + pkl_filename[list_alias], "wb") as file:
                    pickle.dump(self.aliases[list_alias], file)

    def get_user_data(self, user_id, list_alias: allowed_values):
        return self.aliases[list_alias].get(user_id)

    def printer(self):
        for alias in self.aliases:
            print(f"{alias: <7}: {self.aliases[alias]}")
        print()


def unpickle(filename):
    if filename in os.listdir(pkl_folder):
        with open(pkl_folder+filename, "rb") as file:
            return pickle.load(file)
    return dict()
