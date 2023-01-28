from typing import Literal
import pickle
import os
allowed_values = Literal["email", "phone", "reg", "ask", "cheque", "admin_new_db"]


class WaitList:
    def __init__(self):
        self.email = unpickle("email.pkl")
        self.phone_number = unpickle("phone_number.pkl")
        self.register_info = unpickle("register_info.pkl")
        self.ask_manager = unpickle("ask_manager.pkl")
        self.cheque = unpickle("cheque.pkl")
        self.new_db = unpickle("new_db.pkl")
        self.aliases = {"email": self.email,
                        "phone": self.phone_number,
                        "reg": self.register_info,
                        "ask": self.ask_manager,
                        "cheque": self.cheque,
                        "admin_new_db": self.new_db}
        self.printer()

    def add_user_to_waitlist(self, user_id, list_alias: allowed_values, val=True):
        self.aliases[list_alias][user_id] = val

    def user_waitlist_reset(self, user_id):
        for waitlist in self.aliases.values():
            if user_id in waitlist:
                waitlist.pop(user_id)

    def serialize_current_state(self):
        with open("pickles/email.pkl", "wb") as file:
            pickle.dump(self.email, file)
        with open("pickles/phone_number.pkl", "wb") as file:
            pickle.dump(self.phone_number, file)
        with open("pickles/register_info.pkl", "wb") as file:
            pickle.dump(self.register_info, file)
        with open("pickles/ask_manager.pkl", "wb") as file:
            pickle.dump(self.ask_manager, file)
        with open("pickles/cheque.pkl", "wb") as file:
            pickle.dump(self.cheque, file)
        with open("pickles/new_db.pkl", "wb") as file:
            pickle.dump(self.new_db, file)
        print("pickled")

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
