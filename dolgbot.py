# -*- coding: utf-8 -*-
import telebot
import sqlite3
from telebot import types
from time import sleep
from time import ctime

"""
Планирующиеся изменения:
Непрекращающаяся работа
"""

__version__ = '0.2.0.3'
__chng__ = """
0.2.0.0:
Команды теперь не через слеш и на русском!
Усовершенствованы системы хранения и обраотки данных
0.2.0.1:
Вместо CANCEL теперь ОТМЕНА (полный перевод)
Команды можно писать и большими и маленькими буквами
0.2.0.2:
Ввод логина и пароля при регистрации и авторизации теперь возможен и через два разных сообщения!
0.2.0.3:
Пароль должен состоять только из символов A..Z, a..z или цифр
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

ERROR = 0

logins = [] #все существующие в системе логины
users = dict() #шаги пользователей
kods = dict() #id + логины залогинившихся пользователей
vr = dict() #временные данные


def loadlogins():
    conn = sqlite3.connect('my.db')
    cur = conn.cursor()
    global logins
    cur.execute('SELECT * FROM users')
    for row in cur:
        logins.append(row[1])
    cur.close()
    conn.close()

def loadkods():
    conn = sqlite3.connect('my.db')
    cur = conn.cursor()
    global logins
    cur.execute('SELECT * FROM zalog')
    for row in cur:
        kods[row[0]] = row[1]
    cur.close()
    conn.close()

def del_kod(kd):
    conn = sqlite3.connect('my.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM zalog WHERE id = '%d'"%(kd))
    conn.commit()
    cur.close()
    conn.close()

loadlogins()
loadkods()

markup = types.ReplyKeyboardMarkup()
markup.row('ВХОД', 'ВЫХОД')
markup.row('ДОЛГИ','ДОБАВИТЬ')
markup.row('РЕДАКТИРОВАТЬ','РЕГИСТРАЦИЯ')
markup.row('СМЕНА ПАРОЛЯ','О БОТЕ')

@bot.message_handler(commands=['start'])
def start(message):
    mid = message.chat.id
    bot.send_message(mid , __desc__ + '\nВерсия бота: ' + str(__version__) + '\n\nСписок изменений:' + __chng__, reply_markup=markup)
    if(users.get(mid) == None):
        users[mid] = 0
    start1(message)
    

def start1(message):
    conn = sqlite3.connect('my.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    row = cur.fetchone()
    while row is not None:
        if row[1] == 'user':
            pas = row[2]
            row = None
        else:
            row = cur.fetchone()
    bot.send_message(message.chat.id, "Привет, мне срочно нужна помощь! Потести моего бота. Здесь есть аккаунт: user. Пароль у него: " + pas)
    cur.close()
    conn.close()


@bot.message_handler(content_types=['text'])
def main(message):
    mid = message.chat.id
    text = message.text
    if((users.get(mid) == None) or (users[mid] == 0)):
        users[mid] = 0
        text = text.upper()
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
                conn = sqlite3.connect('my.db')
                cur = conn.cursor()
                cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods[mid]))
                for row in cur:
                    stroka += row[0] + ' ' + str(row[1]) + '\n'
                    kol = kol + 1
                    osum += row[1]
                stroka += 'Всего человек: ' + str(kol) + '\nСумма: ' + str(osum)
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
                conn = sqlite3.connect('my.db')
                cur = conn.cursor()
                cur.execute("SELECT cred FROM credits WHERE login = '%s'"%(kods[mid]))
                for row in cur:
                    markup1.row(row[0])
                cur.close()
                conn.close()
                sent = bot.send_message(mid, 'Введите фамилию и имя должника, у которого хотите изменить долг или ОТМЕНА', reply_markup=markup1)
                users[mid] = 1
                bot.register_next_step_handler(sent, edit1)

        else:
            bot.send_message(mid, 'Команда не найдена')






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
        conn = sqlite3.connect('my.db')
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
    conn = sqlite3.connect('my.db')
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
        conn = sqlite3.connect('my.db')
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
    conn = sqlite3.connect('my.db')
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
    conn = sqlite3.connect('my.db')
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
    conn = sqlite3.connect('my.db')
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
        conn = sqlite3.connect('my.db')
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
        conn = sqlite3.connect('my.db')
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
    if text != 'ОТМЕНА':
        try:
            fam, im = text.split()
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup=markup)
            users[mid] = 0
            return
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('ОТМЕНА')
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute("SELECT sz FROM credits WHERE cred = '%s'"%(fam + ' ' + im))
        for row in cur:
            markup1.row(str(-row[0]))
        cur.close()
        conn.close()
        vr[mid] = fam + ' ' + im
        sent = bot.send_message(mid, 'Введите сумму или ОТМЕНА', reply_markup=markup1)
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
        conn = sqlite3.connect('my.db')
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
            conn = sqlite3.connect('my.db')
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


bot.polling()
