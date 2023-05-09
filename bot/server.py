import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.utils import get_random_id

from threading import Lock

import json

from storage.settings.keyboards import *
from storage.settings.messages import *
from storage.settings.config import contest_running
from storage.settings.time_settings import db_update_hour, db_update_minutes, mailing_hour, mailing_minutes

from services.admin_class import Admin
from services.database_class import Database
from services.waitlist_class import WaitList
from services.contest_class import Contest
from services.mailer_class import Mailer
from services.daemons import DailyTaskDaemon

from services.logger import logger


class Bot:
    def __init__(self, api_token, group_id):
        self.vk = vk_api.VkApi(token=api_token)
        self.long_poll = VkBotLongPoll(self.vk, group_id)
        self.vk_api = self.vk.get_api()
        self.waitlist = WaitList()
        self.admin = Admin()
        self.database = Database(logger=logger, notification_sender=self.send_msg)
        self.mailer = Mailer(self.send_msg)
        self.thread_lock = Lock()
        if contest_running:
            try:
                self.contest = Contest()
            except BaseException as e:
                exit_text = f"Ошибка чтения 'contest_participants.csv'. Удалите его перед запуском бота.\n{repr(e)}"
                logger.error(exit_text)
                exit(exit_text)

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
        try:
            self.vk_api.messages.send(**msg_content)
        except vk_api.ApiError:
            logger.error(f"Ошибка API. Сообщение пользователю id{to_user} не отправлено. "
                         f"Возможно, пользователь запретил сообщения от бота.")
        else:
            logger.info(f"Отправлено сообщение пользователю id{to_user}.")

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

    def process_cheque(self, user_id, text, message):
        name = " ".join(self.get_first_name_last_name(user_id))
        tmp = to_admin_buy_certificate.format(name, user_id, self.waitlist.get_user_data(user_id, "email"),
                                              self.waitlist.get_user_data(user_id, "cheque"), text)
        self.send_msg(to_user=self.admin.manager, message=tmp,
                      attachments=self.extract_attachments_from_message(message.attachments))
        self.send_default_keyboard(to_user=user_id, message=certificate_after_payment)

    def initialize_user_registration(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "reg")
        self.send_default_keyboard(to_user=user_id, message=registration_message)

    def process_user_registration(self, user_id, text):
        name = " ".join(self.get_first_name_last_name(user_id))
        msg_to_manager = to_admin_customer_registration.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=msg_to_manager)
        self.send_default_keyboard(to_user=user_id, message=registration_confirmation)

    def initialize_get_bonus_balance(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "phone")
        self.send_default_keyboard(to_user=user_id, message=get_balance_message)

    def process_get_bonus_balance(self, user_id, text):
        result, error_happened = self.database.get_balance_by_phone(text)
        response = get_balance_response.format(result)
        if error_happened and user_id not in self.admin.admin_list:
            self.send_msg(to_user=self.admin.manager,
                          message=f"Ошибка поиска номера {text} в базе данных. Ответ на запрос: {response}")
        self.send_default_keyboard(to_user=user_id, message=response)

    def initialize_ask_manager(self, user_id):
        self.waitlist.add_user_to_waitlist(user_id, "ask")
        self.send_default_keyboard(to_user=user_id, message=ask_manager_message)

    def process_ask_manager(self, user_id, text):
        name = " ".join(self.get_first_name_last_name(user_id))
        msg_to_manager = to_admin_customer_question.format(name, user_id, text)
        self.send_msg(to_user=self.admin.manager, message=msg_to_manager)
        self.send_default_keyboard(to_user=user_id, message=ask_manager_confirmation)

    def process_contest(self, user_id):
        if not contest_running:
            self.send_default_keyboard(to_user=user_id, message=text_contest_closed)
            return
        response = self.contest.add_participant(user_id)
        self.send_default_keyboard(to_user=user_id, message=response)

    @staticmethod
    def extract_attachments_from_message(attachments):
        result = []
        attachments_description = []
        photo_links = None
        for attachment in attachments:
            att_type = attachment["type"]
            if att_type == "photo":                                             # Если тип - фото, тогда прикрепляем
                att = attachment[att_type]
                access_key = att["access_key"]
                owner_id = att["owner_id"]
                att_id = att["id"]
                result.append(f"{att_type}{owner_id}_{att_id}_{access_key}")
            photo_links = ",".join(result)
            attachments_description.append(att_type)                            # И формируем список типов всех вложений
        attachments_description = ", ".join(attachments_description)
        return photo_links, attachments_description

    def process_attachments(self, user_id, text, message):
        name = " ".join(self.get_first_name_last_name(user_id))
        photo_links, attachments_description = self.extract_attachments_from_message(message.attachments)
        tmp = to_admin_photo_attachment.format(name, user_id, text, attachments_description)
        self.send_msg(to_user=self.admin.manager, message=tmp, attachments=photo_links)

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

        # Если пользователь что-то прикрепил к сообщению, тогда пересылаем администратору
        else:
            if message.attachments:
                self.process_attachments(user_id, text, message)

        self.waitlist.user_waitlist_reset(user_id)

    # Обработчик кнопок главного меню
    def payload_menu(self, user_id, option):
        self.waitlist.user_waitlist_reset(user_id)
        if option == "buy_cert":
            self.initialize_buy_certificate(user_id)
        elif option == "reg_bonus":
            self.initialize_user_registration(user_id)
        elif option == "get_balance":
            self.initialize_get_bonus_balance(user_id)
        elif option == "ask_manager":
            self.initialize_ask_manager(user_id)
        elif option == "contest":
            self.process_contest(user_id)
        else:
            self.send_default_keyboard(user_id)

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
            self.send_msg(to_user=user_id, message="Запущена процедура обновления таблицы.")
            self.database.load_data(admin_update_notify_by=user_id)

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
        else:  # Если пришёл странный payload (например, могла устареть клавиатура при обновлении, либо ручной запрос)
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

    def start_daemons(self):
        database_daemon = DailyTaskDaemon(target_obj=self.database, func_to_call='load_data', lock=self.thread_lock)
        mailer_daemon = DailyTaskDaemon(target_obj=self.mailer, func_to_call='do_mailing', lock=self.thread_lock)

        database_daemon.run_daily_task(action_time_hour=db_update_hour, action_time_minutes=db_update_minutes,
                                       auto_update=True)
        mailer_daemon.run_daily_task(action_time_hour=mailing_hour, action_time_minutes=mailing_minutes)

    def start_listen(self):
        try:
            for event in self.long_poll.listen():
                with self.thread_lock:  # блокируем переключение потоков на время обработки сообщения
                    logger.debug(f"from: {event.message.from_id} | "
                                 f"text: {event.message.text} | "
                                 f"payload: {event.message.payload} | "
                                 f"attached:{[att['type'] for att in event.message.attachments]}")
                    self.controller(event)
        except Exception as e:
            logger.error(f"Ошибка в главном модуле бота. Возможно, пропало подключение.")
            logger.error(f"Бот умирает в надежде, что докер не отвалится и переподнимет его.\n{repr(e)}")
            exit()

    def start(self):
        self.start_daemons()
        self.start_listen()
