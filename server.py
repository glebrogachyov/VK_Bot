import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.utils import get_random_id

from settings.keyboards import *
from settings.messages import *

from tools.functions import get_attachments_links
from tools.Admin_class import Admin
from tools.Database_class import Database
from tools.Waitlist_class import WaitList

import json


class Bot:
    def __init__(self, api_token, group_id):
        self.vk = vk_api.VkApi(token=api_token)
        self.long_poll = VkBotLongPoll(self.vk, group_id)
        self.vk_api = self.vk.get_api()
        self.waitlist = WaitList()
        self.admin = Admin()
        self.admin.load_from_json()
        self.database = Database("")
        self.menu_functions = {'buy_cert': self.initialize_buy_certificate,
                               'reg_bonus': self.initialize_user_registration,
                               'get_balance': self.initialize_get_bonus_balance,
                               'ask_manager': self.initialize_ask_manager
                               }

    def send_msg(self, to_user, message="Выберите:", keyboard=None, attachments=None):
        msg_content = {"peer_id": to_user,
                       "message": message,
                       "random_id": get_random_id(),
                       }
        if keyboard:
            msg_content["keyboard"] = keyboard.get_keyboard()
        if attachments:
            msg_content["attachment"] = attachments
        self.vk_api.messages.send(**msg_content)

    def send_default_keyboard(self, user_id):
        # Добавить ветвление на клавиатуру обычного юзера и админа
        if user_id in self.admin.admin_list:
            self.send_msg(to_user=user_id, keyboard=default_admin_keyboard)
        else:
            self.send_msg(to_user=user_id, keyboard=default_keyboard)

    def initialize_buy_certificate(self, user_id):
        self.send_msg(to_user=user_id, message=certificate_select_value, keyboard=buy_certificate_keyboard)

    def initialize_user_registration(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "reg")
        self.send_msg(to_user=user_id, message=registration_message)

    def initialize_get_bonus_balance(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "phone")
        self.send_msg(to_user=user_id, message=get_balance_message)

    def initialize_ask_manager(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "ask")
        self.send_msg(to_user=user_id, message=ask_manager_message)

    def process_buy_certificate(self, user_id, text, cert_price):
        print(f"{cert_price=} {text}")
        self.waitlist.add_user_to_waitlist(user_id, "email", text)
        self.waitlist.add_user_to_waitlist(user_id, "cheque", cert_price)
        name = " ".join(self.get_user_name_lastname(user_id))
        email = self.waitlist.get_user_data(user_id, "email")
        m = to_admin_processing_certificate.format(name, user_id, email, cert_price)
        self.send_msg(to_user=self.admin.manager, message=m)
        self.send_msg(to_user=user_id,
                      message=certificate_go_to_payment.format(text),
                      keyboard=pay_link_keyboard(cert_price))

    def process_ask_manager(self, user_id, text):
        name = " ".join(self.get_user_name_lastname(user_id))
        msg = to_admin_customer_question.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=msg)
        self.send_msg(to_user=user_id, message=ask_manager_confirmation)

    def process_user_registration(self, user_id, text):
        name = " ".join(self.get_user_name_lastname(user_id))
        msg = to_admin_customer_registration.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=msg)
        self.send_msg(to_user=user_id, message=registration_confirmation)

    def process_get_bonus_balance(self, user_id, text):
        result = self.database.get_balance_by_phone(text)
        if result is None:
            response = get_balance_incorrect_number
        else:
            response = get_balance_response.format(text, result)
        self.send_msg(to_user=user_id, message=response)

    def process_cheque(self, user_id, text, message):
        print("Процессим чек")
        name = " ".join(self.get_user_name_lastname(user_id))
        tmp = to_admin_buy_certificate.format(name, user_id, self.waitlist.get_user_data(user_id, "email"),
                                              self.waitlist.get_user_data(user_id, "cheque"), text)
        self.send_msg(to_user=self.admin.manager, message=tmp, attachments=get_attachments_links(message.attachments))
        self.send_msg(to_user=user_id, message=certificate_after_payment, keyboard=default_keyboard)

    def process_attachments(self, user_id, text, message):
        print("Процессим прикрепленки")
        name = " ".join(self.get_user_name_lastname(user_id))
        tmp = to_admin_photo_attachment.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=tmp, attachments=get_attachments_links(message.attachments))

    # Менеджер сообщений, которые пользователь написал сам, а не сгенерировал нажатием кнопки
    def controller_text(self, user_id, text, message):

        # Если ожидаем от пользователя информацию для дальнейшей обработки
        if self.waitlist.get_user_data(user_id, "cheque"):
            print("-\nentered process cheque")
            self.process_cheque(user_id, text, message)

        elif cert_price := self.waitlist.get_user_data(user_id, "email"):
            self.process_buy_certificate(user_id, text, cert_price)
            return

        elif self.waitlist.get_user_data(user_id, "ask"):
            self.process_ask_manager(user_id, text)

        elif self.waitlist.get_user_data(user_id, "reg"):
            self.process_user_registration(user_id, text)

        elif self.waitlist.get_user_data(user_id, "phone"):
            self.process_get_bonus_balance(user_id, text)

        # Если пользователь просто так что-то написал, то высылаем дефолтную клавиатуру
        # А если что-то прикрепил к сообщению, тогда пересылаем администратору
        else:
            if message.attachments:
                self.process_attachments(user_id, text, message)
                # Добавить ветку на прикрепленку xlsx документа от админа
            self.send_default_keyboard(user_id)

        self.waitlist.user_waitlist_reset(user_id)

    # Обработчик кнопок главного меню
    def payload_menu(self, user_id, option):
        self.waitlist.user_waitlist_reset(user_id)
        handler = self.menu_functions.get(option)
        print(f"Payload - menu\n{handler=}")
        handler(user_id)

    # Обработчик кнопок покупки сертификата
    def payload_buy_certificate(self, user_id, price):
        print(f"Payload - buy certificate, {price=}")
        self.waitlist.add_user_to_waitlist(user_id, "email", price)
        self.send_msg(to_user=user_id, message=certificate_enter_email, keyboard=back_keyboard)

    # обработчик кнопок "Назад"
    def payload_back_button(self, user_id, command):
        print(f"Payload - back, {command=}")
        if command == "to_menu":
            self.send_default_keyboard(user_id)
        elif command == "to_cert":
            # Сообщение админу об отмене покупки на этапе оплаты
            name = " ".join(self.get_user_name_lastname(user_id))
            self.send_msg(to_user=self.admin.manager, message=to_admin_cancel_certificate.format(
                name, user_id, self.waitlist.get_user_data(user_id, "cheque")))

            # Сообщение пользователю с клавиатурой выбора номинала сертификата
            self.send_msg(to_user=user_id, message=certificate_select_value, keyboard=buy_certificate_keyboard)
        self.waitlist.user_waitlist_reset(user_id)

    def payload_admin(self, user_id, command):
        self.waitlist.user_waitlist_reset(user_id)
        if user_id not in self.admin.admin_list:
            self.send_default_keyboard(user_id)
            return

        if command == "get_admin_menu":
            self.send_msg(user_id, message="Админ панель:", keyboard=admin_menu_keyboard)

        elif command == "new_database":
            self.send_msg(to_user=user_id, message="Отправьте .xlsx файл в ответном сообщении.")

        elif command == "set_manager":
            admin_names = [self.get_user_name_lastname(admin) for admin in self.admin.admin_list]
            print(f"{admin_names=}")
            self.send_msg(to_user=user_id,
                          message="Выберите, кому будут приходить уведомления",
                          keyboard=admin_set_manager_keyboard(admin_names))

        elif type(command) is str and command.startswith("set_"):
            print(command, command[4:])
            response = self.admin.change_manager(int(command[4:]))
            self.send_msg(to_user=user_id, message=response, keyboard=default_admin_keyboard)

        else:
            self.send_default_keyboard(user_id)

    # Менеджер нажатия кнопок клавиатуры
    def controller_payload(self, user_id, payload):
        if option := payload.get("menu"):
            self.payload_menu(user_id, option)
        elif price := payload.get("buy_cert"):
            self.payload_buy_certificate(user_id, price)
        elif command := payload.get("back"):
            self.payload_back_button(user_id, command)
        elif admin_command := payload.get("admin"):
            self.payload_admin(user_id, admin_command)

        else:   # Если пришёл странный payload (например, могла устареть клавиатура при обновлении, либо ручной запрос)
            print(f"unknown {payload=}")
            self.send_default_keyboard(user_id)

    def controller(self, event):
        print("\n---\n", event)
        self.waitlist.printer()
        print(event.message.attachments)
        user_id = event.message.from_id
        text = event.message.text
        print(f"{text=}")

        # Если пользователь написал сообщение, передаём его контроллеру текста
        if event.message.payload is None:
            print("Payload - None")
            self.controller_text(user_id, text, event.message)

        # Если пользователь нажал на кнопку, передаём её контроллеру кнопок
        else:
            payload = json.loads(event.message.payload)
            self.controller_payload(user_id, payload)

    def get_user_name_lastname(self, user_id) -> tuple:
        user_info = self.vk_api.users.get(user_ids=user_id)[0]
        name = user_info['first_name']
        lastname = user_info['last_name']
        return name, lastname

    def start(self):
        for event in self.long_poll.listen():
            self.controller(event)

