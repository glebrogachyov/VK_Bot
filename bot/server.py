import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.utils import get_random_id

from storage.settings.keyboards import *
from storage.settings.messages import *
from storage.settings.config import contest_running

from tools.functions import get_attachments_links
from tools.Admin_class import Admin
from tools.Database_class import Database
from tools.Waitlist_class import WaitList
from tools.Contest_class import Contest

import json


class Bot:
    def __init__(self, api_token, group_id):
        self.vk = vk_api.VkApi(token=api_token)
        self.long_poll = VkBotLongPoll(self.vk, group_id)
        self.vk_api = self.vk.get_api()
        self.waitlist = WaitList()
        self.admin = Admin()
        self.database = Database()
        if contest_running:
            try:
                self.contest = Contest()
            except BaseException as e:
                exit(f"Ошибка во время чтения файла участников конкурса. Удалите его перед запуском бота.\n{e}")
        resp_flag, resp_text = self.database.init_table(first_load=True)
        if resp_flag is False:
            print("База номеров и балансов отсутствует.")
        self.menu_functions = {'buy_cert': self.initialize_buy_certificate,
                               'reg_bonus': self.initialize_user_registration,
                               'get_balance': self.initialize_get_bonus_balance,
                               'ask_manager': self.initialize_ask_manager,
                               'contest': self.process_contest
                               }

    def get_first_name_last_name(self, user_id) -> tuple:
        user_info = self.vk_api.users.get(user_ids=user_id)[0]
        first_name = user_info['first_name']
        last_name = user_info['last_name']
        return first_name, last_name

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

    def send_default_keyboard(self, to_user, message=None):
        if to_user in self.admin.admin_list:
            if message:
                self.send_msg(to_user=to_user, message=message, keyboard=default_admin_keyboard)
            else:
                self.send_msg(to_user=to_user, keyboard=default_admin_keyboard)
        else:
            if message:
                self.send_msg(to_user=to_user, message=message, keyboard=default_keyboard)
            else:
                self.send_msg(to_user=to_user, keyboard=default_keyboard)

    def initialize_buy_certificate(self, user_id):
        self.send_msg(to_user=user_id, message=certificate_select_value, keyboard=buy_certificate_keyboard)

    def initialize_user_registration(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "reg")
        # self.send_msg(to_user=user_id, message=registration_message)
        self.send_default_keyboard(to_user=user_id, message=registration_message)

    def initialize_get_bonus_balance(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "phone")
        # self.send_msg(to_user=user_id, message=get_balance_message)
        self.send_default_keyboard(to_user=user_id, message=get_balance_message)

    def initialize_ask_manager(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "ask")
        # self.send_msg(to_user=user_id, message=ask_manager_message)
        self.send_default_keyboard(to_user=user_id, message=ask_manager_message)

    def process_buy_certificate(self, user_id, text, cert_price):
        self.waitlist.add_user_to_waitlist(user_id, "email", text)
        self.waitlist.add_user_to_waitlist(user_id, "cheque", cert_price)
        name = " ".join(self.get_first_name_last_name(user_id))
        email = self.waitlist.get_user_data(user_id, "email")
        m = to_admin_processing_certificate.format(name, user_id, email, cert_price)
        self.send_msg(to_user=self.admin.manager, message=m)
        self.send_msg(to_user=user_id,
                      message=certificate_go_to_payment.format(text),
                      keyboard=pay_link_keyboard(cert_price))

    def process_ask_manager(self, user_id, text):
        name = " ".join(self.get_first_name_last_name(user_id))
        msg_to_manager = to_admin_customer_question.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=msg_to_manager)
        # self.send_msg(to_user=user_id, message=ask_manager_confirmation)
        self.send_default_keyboard(to_user=user_id, message=ask_manager_confirmation)

    def process_user_registration(self, user_id, text):
        name = " ".join(self.get_first_name_last_name(user_id))
        msg_to_manager = to_admin_customer_registration.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=msg_to_manager)
        # self.send_msg(to_user=user_id, message=registration_confirmation)
        self.send_default_keyboard(to_user=user_id, message=registration_confirmation)

    def process_get_bonus_balance(self, user_id, text):
        result, error = self.database.get_balance_by_phone(text)
        response = get_balance_response.format(result)
        if error and user_id not in self.admin.admin_list:
            self.send_msg(to_user=self.admin.manager,
                          message=f"Ошибка поиска номера {text} в базе данных. Ответ на запрос: {response}")
        # self.send_msg(to_user=user_id, message=response)
        self.send_default_keyboard(to_user=user_id, message=response)

    def process_cheque(self, user_id, text, message):
        name = " ".join(self.get_first_name_last_name(user_id))
        tmp = to_admin_buy_certificate.format(name, user_id, self.waitlist.get_user_data(user_id, "email"),
                                              self.waitlist.get_user_data(user_id, "cheque"), text)
        self.send_msg(to_user=self.admin.manager, message=tmp, attachments=get_attachments_links(message.attachments))
        # self.send_msg(to_user=user_id, message=certificate_after_payment)
        # self.send_default_keyboard(user_id)
        self.send_default_keyboard(to_user=user_id, message=certificate_after_payment)

    def process_contest(self, user_id):
        if not contest_running:
            self.send_default_keyboard(to_user=user_id, message=text_contest_closed)
            return
        response = self.contest.add_participant(user_id)
        self.send_default_keyboard(to_user=user_id, message=response)

    def process_attachments(self, user_id, text, message):
        name = " ".join(self.get_first_name_last_name(user_id))
        tmp = to_admin_photo_attachment.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=tmp, attachments=get_attachments_links(message.attachments))

    def process_new_db(self, user_id, message):
        for attachment in message.attachments:
            if attachment["type"] == "doc" and attachment["doc"]["ext"] == "xlsx":
                self.send_msg(to_user=user_id, message="Файл получен.", keyboard=default_admin_keyboard)
                self.waitlist.user_waitlist_reset(user_id)
                resp_flag, resp_text = self.database.update_table(attachment["doc"]["url"])
                if user_id != self.admin.manager:
                    self.send_msg(to_user=user_id, message=resp_text)
                self.send_msg(to_user=self.admin.manager, message=resp_text)
                break
        else:
            tmp = "В сообщении отсутствует документ .xlsx. Повторите ещё раз."
            self.waitlist.user_waitlist_reset(user_id)
            self.send_msg(to_user=user_id, message=tmp, keyboard=default_admin_keyboard)
            if user_id != self.admin.manager:
                self.send_msg(to_user=self.admin.manager, message=tmp)

    # Менеджер сообщений, которые пользователь написал сам, а не сгенерировал нажатием кнопки
    def controller_text(self, user_id, text, message):

        # Если ожидаем от пользователя информацию для дальнейшей обработки
        if self.waitlist.get_user_data(user_id, "cheque"):
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
                if user_id not in self.admin.admin_list:
                    self.process_attachments(user_id, text, message)
                    self.send_default_keyboard(user_id)
                else:
                    if self.waitlist.get_user_data(user_id, "admin_new_db"):
                        self.process_new_db(user_id, message)
                        return
                    else:
                        self.process_attachments(user_id, text, message)
                        self.send_msg(to_user=user_id, keyboard=default_admin_keyboard)
            # else:
            #     self.send_default_keyboard(user_id)

        self.waitlist.user_waitlist_reset(user_id)

    # Обработчик кнопок главного меню
    def payload_menu(self, user_id, option):
        self.waitlist.user_waitlist_reset(user_id)
        handler = self.menu_functions.get(option)
        handler(user_id)

    # Обработчик кнопок покупки сертификата
    def payload_buy_certificate(self, user_id, price):
        self.waitlist.add_user_to_waitlist(user_id, "email", price)
        self.send_msg(to_user=user_id, message=certificate_enter_email, keyboard=back_keyboard)

    # обработчик кнопок "Назад"
    def payload_back_button(self, user_id, command):
        if command == "to_menu":
            self.send_default_keyboard(user_id)
        elif command == "to_cert":
            # Сообщение админу об отмене покупки на этапе оплаты
            name = " ".join(self.get_first_name_last_name(user_id))
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
            self.send_msg(user_id, message="Панель администратора:", keyboard=admin_menu_keyboard)

        elif command == "new_database":
            self.send_msg(to_user=user_id, message="Отправьте .xlsx файл в ответном сообщении.")
            self.waitlist.add_user_to_waitlist(user_id, "admin_new_db")

        elif command == "set_manager":
            admin_names = [self.get_first_name_last_name(admin) for admin in self.admin.admin_list]
            if self.admin.manager in self.admin.admin_list:
                current_manager_id = self.admin.admin_list.index(self.admin.manager)
            else:
                current_manager_id = None
            self.send_msg(to_user=user_id,
                          message="Выберите, кому будут приходить уведомления",
                          keyboard=admin_set_manager_keyboard(admin_names, current_manager_id))

        elif type(command) is str and command.startswith("set_"):
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
            self.send_default_keyboard(user_id)

    def controller(self, event):
        user_id = event.message.from_id
        text = event.message.text

        # Если пользователь написал сообщение, передаём его контроллеру текста
        if event.message.payload is None:
            self.controller_text(user_id, text, event.message)

        # Если пользователь нажал на кнопку, передаём её контроллеру кнопок
        else:
            payload = json.loads(event.message.payload)
            self.controller_payload(user_id, payload)

    def start(self):
        for event in self.long_poll.listen():
            self.controller(event)
            # print("-------")
            # self.waitlist.printer()
