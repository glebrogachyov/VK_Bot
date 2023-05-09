db_folder = "shared_folder/"
# db_folder = "/home/grogachev/bot_test/"

csv_encoding = "cp1252"

csv_separator = ";"

date_format = "%d.%m.%Y"
timezone_hours = 3

''' Номера телефонов для проверки загруженной в бота таблицы '''
test_phones = ["text", "89513492570", "+7 (900) 521-06-86", "1423"]

"""
Как обрабатываются номера:
 1) Из номера удаляются все символы кроме цифр 
 
 2) у оставшихся цифр длина должна быть 10 или 11 символов (в начале может быть 7 или 8 или ничего, затем 10 цифр),
        - если это так, то он приводится к виду 89XXXXXXXXX и в таком виде перезаписывается в таблицу
        - если это не так, то остаётся без изменений, т.к. либо там ошибка, либо это не мобильный номер
 
 3) Когда пользователь присылает свой номер для запроса баллов, он нормализуется по такой же схеме и ищется в таблице.

"""
