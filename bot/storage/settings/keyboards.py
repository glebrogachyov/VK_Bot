from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from storage.settings.config import link_one, link_two, link_buy_cert, contest_running


def default_keyboard_constructor(keyboard):
    keyboard.add_button(label="Купить электронный подарочный сертификат",
                        color=VkKeyboardColor.PRIMARY,
                        payload={"menu": "buy_cert"})
    keyboard.add_line()
    keyboard.add_button(label="Зарегистрироваться в бонусной программе",
                        color=VkKeyboardColor.PRIMARY,
                        payload={"menu": "reg_bonus"})
    keyboard.add_line()
    keyboard.add_button(label="Узнать баланс бонусных баллов",
                        color=VkKeyboardColor.PRIMARY,
                        payload={"menu": "get_balance"})
    keyboard.add_line()
    keyboard.add_button(label="Задать вопрос менеджеру",
                        color=VkKeyboardColor.PRIMARY,
                        payload={"menu": "ask_manager"})
    keyboard.add_line()
    if contest_running:
        keyboard.add_button(label="Принять участие в конкурсе",
                            color=VkKeyboardColor.POSITIVE,
                            payload={"menu": "contest"})
        keyboard.add_line()

    keyboard.add_openlink_button(label="Посмотреть коллекцию", link=link_one)
    keyboard.add_line()
    keyboard.add_openlink_button(label="Адреса магазинов", link=link_two)

# ----------------------------------------------------------------------------------------------------------------------
# Клавиатура главного меню


default_keyboard = VkKeyboard(one_time=False)
default_keyboard_constructor(default_keyboard)

# ----------------------------------------------------------------------------------------------------------------------
# Клавиатура главного меню для админов


default_admin_keyboard = VkKeyboard(one_time=False)
default_admin_keyboard.add_button(label="Администрирование бота",
                                  color=VkKeyboardColor.POSITIVE,
                                  payload={"admin": "get_admin_menu"})
default_admin_keyboard.add_line()
default_keyboard_constructor(default_admin_keyboard)


# ----------------------------------------------------------------------------------------------------------------------
# Клавиатура выбора стоимости сертификата

buy_certificate_keyboard = VkKeyboard(one_time=False)

for value in link_buy_cert:
    buy_certificate_keyboard.add_button(label=value, color=VkKeyboardColor.POSITIVE, payload={"buy_cert": value})
    buy_certificate_keyboard.add_line()

buy_certificate_keyboard.add_button(label="Назад", color=VkKeyboardColor.NEGATIVE, payload={"back": "to_menu"})


# ----------------------------------------------------------------------------------------------------------------------
# Клавиатура со ссылкой на страницу оплаты

def pay_link_keyboard(certificate_amount):
    keyboard = VkKeyboard()
    pay_link = link_buy_cert.get(certificate_amount)
    if pay_link:
        keyboard.add_openlink_button(label="Оплатить", link=link_buy_cert[certificate_amount])
    else:
        keyboard.add_button(label="Некорректная сумма. Повторите заново.", payload={"back": "to_cert"})
    keyboard.add_line()
    keyboard.add_button(label="Отмена", color=VkKeyboardColor.NEGATIVE, payload={"back": "to_cert"})
    return keyboard


# ----------------------------------------------------------------------------------------------------------------------
# Клавиатура возврата в главное меню

back_keyboard = VkKeyboard(one_time=False)

back_keyboard.add_button(label="Выбрать другую сумму", color=VkKeyboardColor.PRIMARY, payload={"back": "to_cert"})
back_keyboard.add_line()
back_keyboard.add_button(label="Главное меню", color=VkKeyboardColor.NEGATIVE, payload={"back": "to_menu"})


# ----------------------------------------------------------------------------------------------------------------------
# Клавиатура для админов

admin_menu_keyboard = VkKeyboard(one_time=False)

admin_menu_keyboard.add_button(label="Перезагрузить базу данных",
                               color=VkKeyboardColor.PRIMARY,
                               payload={"admin": "new_database"})
admin_menu_keyboard.add_line()
admin_menu_keyboard.add_button(label="Сменить менеджера",
                               color=VkKeyboardColor.PRIMARY,
                               payload={"admin": "set_manager"})
admin_menu_keyboard.add_line()
admin_menu_keyboard.add_button(label="Назад",
                               color=VkKeyboardColor.NEGATIVE,
                               payload={"back": "to_menu"})


# ----------------------------------------------------------------------------------------------------------------------
# Админская клавиатура для выбора менеджера

def admin_set_manager_keyboard(admin_list, current_manager_id):
    tmp_keyboard = VkKeyboard(one_time=False)
    for index, admin_name in enumerate(admin_list[:9]):
        if index == current_manager_id:
            admin_name = *admin_name, "(выбрано)"
        tmp_keyboard.add_button(label=" ".join(admin_name),
                                color=VkKeyboardColor.PRIMARY,
                                payload={"admin": f"set_{index}"})
        tmp_keyboard.add_line()

    tmp_keyboard.add_button(label="Назад",
                            color=VkKeyboardColor.NEGATIVE,
                            payload={"admin": "get_admin_menu"})
    return tmp_keyboard

