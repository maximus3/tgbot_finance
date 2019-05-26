# -*- coding: utf-8 -*-
import telebot
import sqlite3
from telebot import types
from time import sleep
from time import ctime

__version__ = '0.1.0'

TOKEN = 'TGBOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

logins = [] #все существующие в системе логины
kods = [] #id у залогинившихся пользователей
kods1 = [] #залогинившиеся пользователи
vr_id = [] #id для временных данных
vr_zn = [] #временные данные

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
        kods.append(row[0])
        kods1.append(row[1])
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
markup.row('/login', '/out')
markup.row('/credits','/addcredit')
markup.row('/editcredit','/reg')
markup.row('/chngpass','/start','/help')

@bot.message_handler(commands=['start'])
def start(message):
    sent = bot.send_message(message.chat.id, 'Привет. Для помощи используй /help', reply_markup=markup)
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

@bot.message_handler(commands=['reg'])
def reg1(message):
    if kods.count(message.chat.id) == 0:
        sent = bot.send_message(message.chat.id, 'Пожалуйста, введите новый логин и пароль через пробел:')
        bot.register_next_step_handler(sent, reg2)
    else:
        bot.send_message(message.chat.id, 'Вы уже авторизированны. Используйте /help для помощи')

def reg2(message):
    val = message.text
    try:
        log, pas = val.split()
    except Exception:
        bot.send_message(message.chat.id, 'Некорректный ввод')
    log = log.lower()
    if log not in logins:
        for i in range(len(log)):
            if ((log[i]<'a' or log[i]>'z') and (log[i]<'0' or log[i]>'9')):
                bot.send_message(message.chat.id, 'Некорректный ввод')
                return
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (login,password) VALUES ('%s','%s')"%(log,pas))
        conn.commit()
        cur.close()
        conn.close()
        logins.append(log)
        bot.send_message(message.chat.id, 'Регистрация успешно пройдена!')
    else:
        bot.send_message(message.chat.id, 'Пользователь с таким именем уже существует')

@bot.message_handler(commands=['login'])
def logs(message):
    if kods.count(message.chat.id) == 0:
        sent = bot.send_message(message.chat.id, 'Пожалуйста, введите свой логин и пароль через пробел:')
        bot.register_next_step_handler(sent, login)
    else:
        bot.send_message(message.chat.id, 'Вы уже авторизированны. Используйте /help для помощи')

def login(message):
    log = message.text
    try:
        log, past = log.split()
    except Exception:
        bot.send_message(message.chat.id, 'Видимо вы ошиблись. Попробуйте еще раз /login. Используйте /help для помощи')
        return
    log = log.lower()
    if log in logins:
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute('SELECT * FROM users')
        for row in cur:
            if row[1] == log:
                if row[2] == past:
                    kods.append(message.chat.id)
                    kods1.append(log)
                    cur.execute("INSERT INTO zalog (id,login) VALUES ('%d','%s')"%(message.chat.id,log))
                    conn.commit()
                    bot.send_message(message.chat.id, 'Авторизация пройдена!', reply_markup=markup)
                else:
                    sent = bot.send_message(message.chat.id, 'Видимо вы ошиблись. Попробуйте еще раз /login. Используйте /help для помощи P')
                cur.close()
                conn.close()
                return
        cur.close()
        conn.close()
    else:
        bot.send_message(message.chat.id, 'Такого логина не существует')

@bot.message_handler(commands=['credits'])
def credits(message):
    if kods.count(message.chat.id) == 1:
        kol = 0
        osum = 0
        stroka = ""
        stroka += 'Ваши должники:\n'
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods1[kods.index(message.chat.id)]))
        for row in cur:
            stroka += row[0] + ' ' + str(row[1]) + '\n'
            kol = kol + 1
            osum += row[1]
        stroka += 'Всего человек: ' + str(kol) + '\nСумма: ' + str(osum)
        bot.send_message(message.chat.id, stroka, reply_markup=markup)
        cur.close()
        conn.close()
    else:
        bot.send_message(message.chat.id, 'Сначала вам нужно авторизоваться. Используйте команду /login')

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, """
/start - начнем
/login - авторизация
/reg - регистрация
/credits - ваши должники
/addcredit - добавить нового должника
/editcredit - изменить баланс существующего должника
/help - помощь
/out - выход из учетной записи
/chngpass - поменять пароль
""")

@bot.message_handler(commands=['out'])
def out(message):
    if message.chat.id in kods:
        i = kods.index(message.chat.id)
        kods.pop(i)
        kods1.pop(i)
        del_kod(message.chat.id)
        bot.send_message(message.chat.id, 'Выход выполнен')
    else:
        bot.send_message(message.chat.id, 'Сначала вам нужно авторизоваться. Используйте команду /login')

@bot.message_handler(commands=['chngpass'])
def chngpass1(message):
    if kods.count(message.chat.id) == 1:
        sent = bot.send_message(message.chat.id, 'Введите старый пароль')
        bot.register_next_step_handler(sent, chngpass2)
    else:
        bot.send_message(message.chat.id, 'Сначала вам нужно авторизоваться. Используйте команду /login')

def chngpass2(message):
    pas = message.text
    conn = sqlite3.connect('my.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    for row in cur:
        if row[1] == kods1[kods.index(message.chat.id)]:
            if row[2] == pas:
                sent = bot.send_message(message.chat.id, 'Введите новый пароль')
                bot.register_next_step_handler(sent, chngpass3)
            else:
                bot.send_message(message.chat.id, 'Пароль набран неправильно')
            cur.close()
            conn.close()
            return

def chngpass3(message):
    pas = message.text
    conn = sqlite3.connect('my.db')
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = '%s' WHERE login = '%s'"%(pas,kods1[kods.index(message.chat.id)]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(message.chat.id, 'Пароль успешно изменен на ' + pas)

@bot.message_handler(commands=['addcredit'])
def addcredit(message):
    if kods.count(message.chat.id) == 1:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('CANCEL')
        sent = bot.send_message(message.chat.id, 'Введите фамилию, имя и размер долга через пробел или CANCEL для отмены', reply_markup = markup1)
        bot.register_next_step_handler(sent, cradd)
    else:
        bot.send_message(message.chat.id, 'Сначала вам нужно авторизоваться. Используйте команду /login')

def cradd(message):
    mes = message.text
    if mes != 'CANCEL':
        try:
            fam, im, dolg = mes.split()
            dolg = int(dolg)
            dolg = str(dolg)
            fam, im = fam + ' ' + im, im + ' ' + fam
        except Exception:
            bot.send_message(message.chat.id, 'Некорректный ввод', reply_markup=markup)
            return
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods1[kods.index(message.chat.id)]))
        for row in cur:
            if row[0] == fam:
                bot.send_message(message.chat.id, 'Данный участник уже есть в базе. Пожалуйста, воспользуйтесь командой /editcredit для изменения размера долга', reply_markup=markup)
                cur.close()
                conn.close()
                return
            if row[0] == im:
                bot.send_message(message.chat.id, 'Данный участник уже есть в базе. Пожалуйста, воспользуйтесь командой /editcredit для изменения размера долга', reply_markup=markup)
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
        cur.execute("INSERT INTO credits (login,cred,sz) VALUES ('%s','%s','%d')"%(kods1[kods.index(message.chat.id)],fam,int(dolg)))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(message.chat.id, 'Долг успешно добавлен', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Отмена выполнена', reply_markup=markup)

@bot.message_handler(commands=['editcredit'])
def editcredit(message):
    if kods.count(message.chat.id) == 1:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('CANCEL')
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute("SELECT cred FROM credits WHERE login = '%s'"%(kods1[kods.index(message.chat.id)]))
        for row in cur:
            markup1.row(row[0])
        cur.close()
        conn.close()
        sent = bot.send_message(message.chat.id, 'Введите фамилию и имя должника, у которого хотите изменить долг или CANCEL для отмены', reply_markup=markup1)
        bot.register_next_step_handler(sent, edit0)
    else:
        bot.send_message(message.chat.id, 'Сначала вам нужно авторизоваться. Используйте команду /login')

def edit0(message):
    mes = message.text
    if mes != 'CANCEL':
        try:
            fam, im = mes.split()
        except Exception:
            bot.send_message(message.chat.id, 'Некорректный ввод', reply_markup=markup)
            return
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('CANCEL')
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute("SELECT sz FROM credits WHERE cred = '%s'"%(fam + ' ' + im))
        for row in cur:
            markup1.row(str(-row[0]))
        cur.close()
        conn.close()
        vr_id.append(message.chat.id)
        vr_zn.append(fam + ' ' + im)
        sent = bot.send_message(message.chat.id, 'Введите сумму или CANCEL для отмены', reply_markup=markup1)
        bot.register_next_step_handler(sent, edit)
    else:
        bot.send_message(message.chat.id, 'Отмена выполнена', reply_markup=markup)

def edit(message):
    r = message.text
    if r != 'CANCEL':
        i = vr_id.index(message.chat.id)
        fam, im = vr_zn[i].split()
        fam, im = fam + ' ' + im, im + ' ' + fam
        vr_id.pop(i)
        vr_zn.pop(i)
        #bot.send_message(message.chat.id, fam, reply_markup=markup)
        try:
            r = int(r)
        except Exception:
            bot.send_message(message.chat.id, 'Некорректный ввод', reply_markup=markup)
            return
        conn = sqlite3.connect('my.db')
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods1[kods.index(message.chat.id)]))
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
            bot.send_message(message.chat.id, 'Участник не найден', reply_markup=markup)
        else:
            if kdk == 2:
                fam = im
            zn = zn + r
            conn = sqlite3.connect('my.db')
            cur = conn.cursor()
            if zn == 0:
                cur.execute("DELETE FROM credits WHERE login = '%s' AND cred = '%s'"%(kods1[kods.index(message.chat.id)],fam))
            else:
                cur.execute("UPDATE credits SET sz = '%d' WHERE login = '%s' AND cred = '%s'"%(zn,kods1[kods.index(message.chat.id)],fam))
            conn.commit()
            cur.close()
            conn.close()
            bot.send_message(message.chat.id, 'Операция успешно выполнена', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, 'Отмена выполнена', reply_markup=markup)

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
bot.polling()
