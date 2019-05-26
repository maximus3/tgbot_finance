# -*- coding: utf-8 -*-
import telebot
import sqlite3
from telebot import types

"""
Планирующиеся изменения:
Повторяющиеся элементы в группе
"""

__version__ = '0.2.2'
__chng__ = """
2.0.0:
Команды теперь не через слеш и на русском!
Усовершенствованы системы хранения и обраотки данных
2.0.1:
Вместо CANCEL теперь ОТМЕНА (полный перевод)
Команды можно писать и большими и маленькими буквами
2.0.2:
Ввод логина и пароля при регистрации и авторизации теперь возможен и через два разных сообщения!
2.0.3:
Пароль должен состоять только из символов A..Z, a..z или цифр

2.1.0:
Бот будет работать без перебоев (я надеюсь)
2.1.1:
Теперь нельзя заходить по одному логину с разных аккаунтов одновременно
2.1.2:
Оптимизация кода

2.2.0:
Добавлены группы. Теперь вы можете создать свою группу должников и каждый раз не писать их отдельно, а добавлять долг сразу всем.
"""
__desc__ = """
Данный бот предназначени для того, чтобы вы не забыли кто и сколько вам должен)

Описание команд:
ВХОД - авторизация
РЕГИСТРАЦИЯ - регистрация
ДОЛГИ - ваши должники
ДОБАВИТЬ - добавить нового должника
РЕДАКТИРОВАТЬ - изменить баланс существующего должника
О БОТЕ - описание бота
ВЫХОД - выход из учетной записи
СМЕНА ПАРОЛЯ - поменять пароль
"""

TOKEN = 'TGBOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

db = 'my.db'
aid = 0 # ADMIN_TGID_HERE
code = 'пассажиры'
ERROR = 0
ERRORS_DESC = """
0 - все в порядке
1 - остановлено пользователем
"""

logins = [] #все существующие в системе логины
users = dict() #шаги пользователей
kods = dict() #id + логины залогинившихся пользователей
vr = dict() #временные данные

def loadlogins():
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    global logins
    cur.execute('SELECT * FROM users')
    for row in cur:
        logins.append(row[1])
    cur.close()
    conn.close()

def loadkods():
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    global logins
    cur.execute('SELECT * FROM zalog')
    for row in cur:
        kods[row[0]] = row[1]
    cur.close()
    conn.close()

def del_kod(kd):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("DELETE FROM zalog WHERE id = '%d'"%(kd))
    conn.commit()
    cur.close()
    conn.close()

loadlogins()
loadkods()

markup = types.ReplyKeyboardMarkup()
markup.row('Вход', 'Выход')
markup.row('Долги','Добавить')
markup.row('Редактировать','Группы')
markup.row('Регистрация')
markup.row('Смена пароля','О боте')

@bot.message_handler(commands=['errors'])
def errors1(message):
    mid = message.chat.id
    users[mid] = 1
    sent = bot.send_message(mid, 'Введите кодовое слово:')
    bot.register_next_step_handler(sent, errors2)

def errors2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = 0
    if text == code and ERROR != 0:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('ДА')
        markup1.row('НЕТ')
        try:
            FILE = open ("nohup.out","r")
            LOGS = FILE.read()
            FILE.close()
        except Exception:
            LOGS = ''
        sent = bot.send_message(mid, 'ERROR: ' + str(ERROR) + '\n\nLOGS:\n' + LOGS + '\n\nЗапустить бота?', reply_markup=markup1)
        users[mid] = 1
        bot.register_next_step_handler(sent, errors3)
    elif text == code and ERROR == 0:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('ДА')
        markup1.row('НЕТ')
        sent = bot.send_message(mid, 'Остановить бота?', reply_markup=markup1)
        users[mid] = 1
        bot.register_next_step_handler(sent, errors4)
    else:
        bot.send_message(mid, 'Кодовое слово не верно')

def errors3(message):
    global ERROR
    mid = message.chat.id
    text = message.text
    text = text.upper()
    users[mid] = 0
    if text == 'ДА':
        ERROR = 0
        bot.send_message(mid, 'Бот запущен', reply_markup=markup)
    else:
        bot.send_message(mid, 'Бот не запущен', reply_markup=markup)

def errors4(message):
    global ERROR
    mid = message.chat.id
    text = message.text
    text = text.upper()
    users[mid] = 0
    if text == 'ДА':
        ERROR = 1
        bot.send_message(mid, 'Бот остановлен', reply_markup=markup)
    else:
        bot.send_message(mid, 'Бот работает', reply_markup=markup)

@bot.message_handler(commands=['start'])
def start(message):
    mid = message.chat.id
    bot.send_message(mid , __desc__ + '\nВерсия бота: ' + str(__version__) + '\n\nСписок изменений:' + __chng__, reply_markup=markup)
    if(users.get(mid) == None):
        users[mid] = 0

@bot.message_handler(content_types=['text'])
def main(message):
    mid = message.chat.id
    text = message.text
    if((users.get(mid) == None) or (users[mid] == 0)):
        users[mid] = 0
        text = text.upper()
        if ERROR == 0:
            if text == 'РЕГИСТРАЦИЯ':
                if kods.get(mid) == None:
                    sent = bot.send_message(mid, 'Пожалуйста, введите новый логин и пароль через пробел или в два разных сообщения:')
                    users[mid] = 1
                    bot.register_next_step_handler(sent, reg1)
                else:
                    bot.send_message(mid, 'Вы уже авторизированны')
                
            elif text == 'ВХОД':
                if kods.get(mid) == None:
                    sent = bot.send_message(mid, 'Пожалуйста, введите свой логин и пароль через пробел или в два разных сообщения:')
                    users[mid] = 1
                    bot.register_next_step_handler(sent, login1)
                else:
                    bot.send_message(mid, 'Вы уже авторизированны')
                
            elif text == 'ВЫХОД':
                if kods.get(mid) == None:
                    bot.send_message(mid, 'Сначала вам нужно авторизоваться')
                else:
                    kods.pop(mid)
                    del_kod(mid)
                    bot.send_message(mid, 'Выход выполнен')
                
            elif text == 'ДОЛГИ':
                if kods.get(mid) == None:
                    bot.send_message(mid, 'Сначала вам нужно авторизоваться')
                else:
                    kol = 0
                    osum = 0
                    stroka = ""
                    stroka += 'Ваши должники:\n'
                    conn = sqlite3.connect(db)
                    cur = conn.cursor()
                    cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods[mid]))
                    for row in cur:
                        stroka += row[0] + ' ' + str(row[1]) + '\n'
                        kol = kol + 1
                        osum += row[1]
                    stroka += 'Всего человек: ' + str(kol) + '\nСумма: ' + str(osum)
                    if kol == 0:
                        stroka = 'У вас нет должников'
                    bot.send_message(mid, stroka, reply_markup=markup)
                    cur.close()
                    conn.close()
                
            elif text == 'О БОТЕ':
                start(message)

            elif text == 'СМЕНА ПАРОЛЯ':
                if kods.get(mid) == None:
                    bot.send_message(mid, 'Сначала вам нужно авторизоваться')
                else:
                    sent = bot.send_message(mid, 'Введите старый пароль')
                    users[mid] = 1
                    bot.register_next_step_handler(sent, chngpass1)

            elif text == 'ДОБАВИТЬ':
                if kods.get(mid) == None:
                    bot.send_message(mid, 'Сначала вам нужно авторизоваться')
                else:
                    markup1 = types.ReplyKeyboardMarkup()
                    markup1.row('ОТМЕНА')
                    sent = bot.send_message(mid, 'Введите фамилию, имя и размер долга через пробел или ОТМЕНА', reply_markup = markup1)
                    users[mid] = 1
                    bot.register_next_step_handler(sent, addcredit)

            elif text == 'РЕДАКТИРОВАТЬ':
                if kods.get(mid) == None:
                    bot.send_message(mid, 'Сначала вам нужно авторизоваться')
                else:
                    markup1 = types.ReplyKeyboardMarkup()
                    markup1.row('ОТМЕНА')
                    conn = sqlite3.connect(db)
                    cur = conn.cursor()
                    cur.execute("SELECT cred FROM credits WHERE login = '%s'"%(kods[mid]))
                    for row in cur:
                        markup1.row(row[0])
                    cur.close()
                    conn.close()
                    sent = bot.send_message(mid, 'Введите фамилию и имя должника, у которого хотите изменить долг или ОТМЕНА', reply_markup=markup1)
                    users[mid] = 1
                    bot.register_next_step_handler(sent, edit1)

            elif text == 'ГРУППЫ':
                if kods.get(mid) == None:
                    bot.send_message(mid, 'Сначала вам нужно авторизоваться')
                else:
                    stroka = ""
                    stroka += 'Ваши группы:\n'
                    markupGR = types.ReplyKeyboardMarkup()
                    markupGR.row('Назад')
                    markupGR.row('Добавить группу')
                    conn = sqlite3.connect(db)
                    cur = conn.cursor()
                    i = 1
                    cur.execute("SELECT name, kol FROM groups WHERE login = '%s'"%(kods[mid]))
                    for row in cur:
                        stroka += str(i) + ') ' + row[0] + '\nКоличество людей: ' + str(row[1]) + '\n\n'
                        markupGR.row(row[0])
                        i = i + 1
                    cur.close()
                    conn.close()
                    if i == 1:
                        stroka = 'У вас нет групп'
                    sent =bot.send_message(mid, stroka, reply_markup=markupGR)
                    users[mid] = 1
                    bot.register_next_step_handler(sent, group1)

        else:
            bot.send_message(mid, 'Проводятся технические работы')






"""
@bot.message_handler(content_types=['text'])
def otv(message):
    FILE = open ("log.txt","a")
    FILE.write(str(ctime()) + "\n" + str(message.chat.id) + ":\n" + message.text + "\n\n")
    FILE.close()

@bot.message_handler(content_types=['command'])
def otv1s(message):
    FILE = open ("log.txt","a")
    FILE.write(str(ctime()) + "\n" + str(message.chat.id) + ":\n" + message.text + "\n")
    FILE.close()
"""

def reg1(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    try:
        log, pas = text.split()
    except Exception:
        if ' ' in text:
            bot.send_message(mid, 'Некорректный ввод')
            return
        else:
            log = text.lower()
            if log not in logins:
                for i in range(len(log)):
                    if ((log[i]<'a' or log[i]>'z') and (log[i]<'0' or log[i]>'9')):
                        bot.send_message(mid, 'Некорректный ввод. Используйте только символы a...z или цифры')
                        return
                vr[mid] = log
                sent = bot.send_message(mid, 'Введите пароль')
                users[mid] = 1
                bot.register_next_step_handler(sent, reg2)
                return
            else:
                bot.send_message(mid, 'Пользователь с таким именем уже существует')   
    log = log.lower()
    if log not in logins:
        for i in range(len(log)):
            if ((log[i]<'a' or log[i]>'z') and (log[i]<'0' or log[i]>'9')):
                bot.send_message(mid, 'Некорректный ввод. Используйте только символы a...z или цифры для логина')
                return
        for i in range(len(pas)):
            if ((pas[i]<'a' or pas[i]>'z') and (pas[i]<'0' or pas[i]>'9') and (pas[i]<'A' or pas[i]>'Z')):
                bot.send_message(mid, 'Некорректный ввод. Используйте только символы a..z, A..Z или цифры для пароля')
                return
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (login,password) VALUES ('%s','%s')"%(log,pas))
        conn.commit()
        cur.close()
        conn.close()
        logins.append(log)
        bot.send_message(mid, 'Регистрация успешно пройдена!')
    else:
        bot.send_message(mid, 'Пользователь с таким именем уже существует')

def reg2(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    log = vr.pop(mid)
    pas = text
    for i in range(len(pas)):
        if ((pas[i]<'a' or pas[i]>'z') and (pas[i]<'0' or pas[i]>'9') and (pas[i]<'A' or pas[i]>'Z')):
            bot.send_message(mid, 'Некорректный ввод. Используйте только символы a..z, A..Z или цифры для пароля')
            return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("INSERT INTO users (login,password) VALUES ('%s','%s')"%(log,pas))
    conn.commit()
    cur.close()
    conn.close()
    logins.append(log)
    bot.send_message(mid, 'Регистрация успешно пройдена!')

def login1(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    pas = ''
    try:
        log, pas = text.split()
    except Exception:
        if ' ' in text:
            bot.send_message(mid, 'Некорректный ввод')
            return
        else:
            log = text.lower()
            if log in logins:
                if log in kods.values():
                    bot.send_message(mid, 'Данный участник уже авторизирован')
                    return
                vr[mid] = log
                sent = bot.send_message(mid, 'Введите пароль')
                users[mid] = 1
                bot.register_next_step_handler(sent, login2)
                return
            else:
                bot.send_message(mid, 'Такого логина не существует')
                return
    log = log.lower()
    if log in logins:
        if log in kods.values():
            bot.send_message(mid, 'Данный участник уже авторизирован')
            return
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        for row in cur:
            if row[1] == log:
                if row[2] == pas:
                    kods[mid] = log
                    cur.execute("INSERT INTO zalog (id,login) VALUES ('%d','%s')"%(mid,log))
                    conn.commit()
                    bot.send_message(mid, 'Авторизация пройдена!', reply_markup=markup)
                else:
                    bot.send_message(mid, 'Пара логин/пароль не верна')
                cur.close()
                conn.close()
                return
        cur.close()
        conn.close()
    else:
        bot.send_message(mid, 'Такого логина не существует')

def login2(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    log = vr.pop(mid)
    pas = text
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    for row in cur:
        if row[1] == log:
            if row[2] == pas:
                kods[mid] = log
                cur.execute("INSERT INTO zalog (id,login) VALUES ('%d','%s')"%(mid,log))
                conn.commit()
                bot.send_message(mid, 'Авторизация пройдена!', reply_markup=markup)
            else:
                bot.send_message(mid, 'Пара логин/пароль не верна')
            cur.close()
            conn.close()
            return
    cur.close()
    conn.close()

def chngpass1(message):
    text = message.text
    mid = message.chat.id
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    for row in cur:
        if row[1] == kods[mid]:
            if row[2] == text:
                sent = bot.send_message(mid, 'Введите новый пароль')
                bot.register_next_step_handler(sent, chngpass2)
            else:
                bot.send_message(mid, 'Пароль набран неправильно')
                users[mid] = 0
            cur.close()
            conn.close()
            return

def chngpass2(message):
    text = message.text
    users[mid] = 0
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = '%s' WHERE login = '%s'"%(text,kods[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Пароль успешно изменен на ' + text)

def addcredit(message):
    mid = message.chat.id
    text = message.text
    users[mid] = 0
    if text != 'ОТМЕНА':
        try:
            fam, im, dolg = text.split()
            dolg = int(dolg)
            dolg = str(dolg)
            fam, im = fam + ' ' + im, im + ' ' + fam
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup=markup)
            return
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            if (row[0] == fam) or (row[0] == im):
                bot.send_message(mid, 'Данный участник уже есть в базе. Пожалуйста, воспользуйтесь командой РЕДАКТИРОВАТЬ для изменения размера долга', reply_markup=markup)
                cur.close()
                conn.close()
                return
        try:
            cur.close()
            conn.close()
        except Exception:
            pass
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("INSERT INTO credits (login,cred,sz) VALUES ('%s','%s','%d')"%(kods[mid],fam,int(dolg)))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(mid, 'Долг успешно добавлен', reply_markup=markup)
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup=markup)

def edit1(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    if text != 'ОТМЕНА':
        try:
            fam, im = text.split()
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup=markup)
            return
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('ОТМЕНА')
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT sz FROM credits WHERE cred = '%s' AND login = '%s'"%(fam + ' ' + im,kods[mid]))
        for row in cur:
            markup1.row(str(-row[0]))
        cur.close()
        conn.close()
        vr[mid] = fam + ' ' + im
        sent = bot.send_message(mid, 'Введите сумму или ОТМЕНА', reply_markup=markup1)
        users[mid] = 1
        bot.register_next_step_handler(sent, edit2)
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup=markup)

def edit2(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    if text != 'ОТМЕНА':
        fam, im = vr[mid].split()
        fam, im = fam + ' ' + im, im + ' ' + fam
        vr.pop(mid)
        try:
            text = int(text)
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup=markup)
            return
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods[mid]))
        kdk = 0
        for row in cur:
            if row[0] == fam:
                kdk = 1
                zn = row[1]
                break
            if row[0] == im:
                kdk = 2
                zn = row[1]
                break
        cur.close()
        conn.close()
        if kdk == 0:
            bot.send_message(mid, 'Участник не найден', reply_markup=markup)
        else:
            if kdk == 2:
                fam = im
            zn = zn + text
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            if zn == 0:
                cur.execute("DELETE FROM credits WHERE login = '%s' AND cred = '%s'"%(kods[mid],fam))
            else:
                cur.execute("UPDATE credits SET sz = '%d' WHERE login = '%s' AND cred = '%s'"%(zn,kods[mid],fam))
            conn.commit()
            cur.close()
            conn.close()
            bot.send_message(mid, 'Операция успешно выполнена', reply_markup=markup)
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup=markup)

def group1(message):
    text = message.text
    mid = message.chat.id
    text = text.upper()
    users[mid] = 0
    if text != 'НАЗАД':
        if text == 'ДОБАВИТЬ ГРУППУ':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            sent =bot.send_message(mid, 'Введите название группы', reply_markup=markup1)
            users[mid] = 1
            bot.register_next_step_handler(sent, group2)
        else:
            stroka = 'Такой группы нет'
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT name,kol,pep FROM groups WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                if text.upper() == row[0].upper():
                    stroka = row[0] + '\nКоличество людей: ' + str(row[1]) + '\n' + row[2] + '\n\nВыберите действие'
                    markupG = types.ReplyKeyboardMarkup()
                    markupG.row('Меню')
                    markupG.row('Удалить группу')
                    markupG.row('Добавить долг')
                    sent = bot.send_message(mid, stroka, reply_markup=markupG)
                    users[mid] = 1
                    vr[mid] = row[0]
                    bot.register_next_step_handler(sent, group4)
                    cur.close()
                    conn.close()
                    return
            cur.close()
            conn.close()
            bot.send_message(mid, stroka, reply_markup=markup)
    else:
      bot.send_message(mid, 'Вот меню:', reply_markup=markup)

def group2(message):
    text = message.text
    mid = message.chat.id
    text1 = text.upper()
    users[mid] = 0
    if text != 'ОТМЕНА':
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM groups WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            if text1 == row[0].upper():
                bot.send_message(mid, 'Данная группа уже есть', reply_markup=markup)
                cur.close()
                conn.close()
                return
        cur.close()
        conn.close()
        vr[mid] = text
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('ОТМЕНА')
        sent = bot.send_message(mid, 'Введите участников группы (имя и фамилия через пробел) в разных строчках', reply_markup=markup1)
        users[mid] = 1
        bot.register_next_step_handler(sent, group3)
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup=markup)

def group3(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    if text != 'ОТМЕНА':
        text1 = text.split('\n')
        i = 0
        for row in text1:
            i = i + 1
            try:
                fam, im = row.split()
            except Exception:
                bot.send_message(mid, 'Некорректный ввод', reply_markup=markup)
                vr.pop(mid)
                return
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("INSERT INTO groups (login,name,kol,pep) VALUES ('%s','%s','%d','%s')"%(kods[mid],vr[mid],i,text))
        conn.commit()
        cur.close()
        conn.close()
        vr.pop(mid)
        bot.send_message(mid, 'Группа создана', reply_markup=markup)
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup=markup)

def group4(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 0
    if text.upper() == 'МЕНЮ':
        bot.send_message(mid, 'Вот меню:', reply_markup=markup)
    elif text.upper() == 'УДАЛИТЬ ГРУППУ':
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="gr_del_yes")
        cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="gr_del_no")
        keybGR.add(cbtn1, cbtn2)
        users[mid] = 1
        bot.send_message(mid, 'Удалить группу "' + vr[mid] + '"?', reply_markup = keybGR)
    elif text.upper() == 'ДОБАВИТЬ ДОЛГ':
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="gr_yes")
        cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="gr_no")
        keybGR.add(cbtn1, cbtn2)
        users[mid] = 1
        bot.send_message(mid, 'Вы хотите добавить существующим учасиникам долг или оставить их долг таким же?', reply_markup = keybGR)  
    else:
        bot.send_message(mid, 'Я вас не понимаю. Вот меню:', reply_markup=markup)

def group5(message):
    text = message.text
    mid = message.chat.id
    if text != 'ОТМЕНА':
        try:
            text = int(text)
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup=markup)
            vr.pop(mid)
            users[mid] = 0
            return
        pep1 = []
        pep2 = []
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT pep FROM groups WHERE login = '%s' AND name = '%s'"%(kods[mid],vr[mid]))
        vr.pop(mid)
        for row in cur:
            pep = row[0].split('\n')
        for row1 in pep:
            row1 = row1.split()
            ckod = 0
            cur.execute("SELECT cred FROM credits WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                if row1[0] + ' ' + row1[1] == row[0]:
                    pep1.append(row1[0] + ' ' + row1[1])
                    ckod = 1
                elif row1[1] + ' ' + row[0] == row[0]:
                    pep1.append(row1[1] + ' ' + row1[0])
                    ckod = 1
            if ckod == 0:
                pep2.append(row1[0] + ' ' + row1[1])
        for row in pep2:
            cur.execute("INSERT INTO credits (login,cred,sz) VALUES ('%s','%s','%d')"%(kods[mid],row,text))
            conn.commit()
        for fam in pep1:
            cur.execute("SELECT sz FROM credits WHERE login = '%s' AND cred = '%s'"%(kods[mid],fam))
            zn = 0
            for row in cur:
                zn = row[0] + text
            if zn == 0:
                cur.execute("DELETE FROM credits WHERE login = '%s' AND cred = '%s'"%(kods[mid],fam))
            else:
                cur.execute("UPDATE credits SET sz = '%d' WHERE login = '%s' AND cred = '%s'"%(zn,kods[mid],fam))
            conn.commit()
        cur.close()
        conn.close()
        users[mid] = 0
        bot.send_message(mid, 'Операция выполнена', reply_markup=markup)
    else:
        users[mid] = 0
        bot.send_message(mid, 'Отмена выполнена', reply_markup=markup)

def group6(message):
    text = message.text
    mid = message.chat.id
    if text != 'ОТМЕНА':
        try:
            text = int(text)
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup=markup)
            vr.pop(mid)
            users[mid] = 0
            return
        pep2 = []
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT pep FROM groups WHERE login = '%s' AND name = '%s'"%(kods[mid],vr[mid]))
        vr.pop(mid)
        for row in cur:
            pep = row[0].split('\n')
        for row1 in pep:
            row1 = row1.split()
            kod = 0
            cur.execute("SELECT cred FROM credits WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                if (row1[0] + ' ' + row1[1] == row[0]) or (row1[1] + ' ' + row1[0] == row[0]):
                    kod = 1
            if kod == 0:
                pep2.append(row1[0] + ' ' + row1[1])
        for row in pep2:
            cur.execute("INSERT INTO credits (login,cred,sz) VALUES ('%s','%s','%d')"%(kods[mid],row,text))
            conn.commit()
        cur.close()
        conn.close()
        users[mid] = 0
        bot.send_message(mid, 'Операция выполнена', reply_markup=markup)
    else:
        users[mid] = 0
        bot.send_message(mid, 'Отмена выполнена', reply_markup=markup)

"""
keybGR = types.InlineKeyboardMarkup()
cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="gr_yes")
cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="gr_no")
keybGR.add(cbtn1, cbtn2)
bot.send_message(mid, 'Вы хотите добавить существующим учасиникам долг или оставить их долг таким же?', reply_markup = keybGR)  
"""

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        mid = call.message.chat.id
        if call.data == "gr_del_yes":
            users[mid] = 0
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("DELETE FROM groups WHERE name = '%s'"%(vr[mid]))
            conn.commit()
            cur.close()
            conn.close()
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удвление выполнено")
            bot.send_message(mid, "Вот меню:", reply_markup=markup)
        if call.data == "gr_del_no":
            users[mid] = 0
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Вот меню:", reply_markup=markup)
        if call.data == "gr_yes":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Будем добавлять еще долг уже существующим")
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            sent = bot.send_message(mid, 'Введите размер долга', reply_markup=markup1)
            bot.register_next_step_handler(sent, group5)
        if call.data == "gr_no":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Оставим у существующих все как есть")
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            sent = bot.send_message(mid, 'Введите размер долга', reply_markup=markup1)
            bot.register_next_step_handler(sent, group6)
            
bot.polling(none_stop=True)

