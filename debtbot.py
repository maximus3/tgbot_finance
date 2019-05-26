# -*- coding: utf-8 -*-
import telebot
import sqlite3
from telebot import types
import time
import cherrypy
import os
from config import *
from func import *
from chatbase import Message
from diag import *
import operator
#import matplotlib as mpl
#import matplotlib.pyplot as plt


ERROR = 0
logins = loadlogins() #все существующие в системе логины
users = dict() #шаги пользователей
kods = dict() #id + логины залогинившихся пользователей
kods, users = loadkods()
vr = dict() #временные данные
vr1 = dict() #^2
vr2 = dict()
vr3 = dict()
vr4 = dict()
spend = dict() #счет в расходах и доходах
tme = dict() #время для записи расходов/доходов
catg = dict() #доходы/расходы

bot = telebot.TeleBot(TOKEN)

#WEBHOOOK_START

# Наш вебхук-сервер
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # Эта функция обеспечивает проверку входящего сообщения
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)

#WEBHOOK_FINISH

@bot.message_handler(commands=['admin'])
def admin(message):
    mid = message.chat.id
    if mid == admin_id:
        bot.send_message(mid, 'Добро пожаловать! Всего пользователей: ' + str(len(logins)))

# Подключение к Алисе от Яндекса
@bot.message_handler(commands=['alice'])
def alice(message):
    mid = message.chat.id
    
    if ERROR != 0:
        bot.send_message(mid, 'Проводятся технические работы')
        return
    
    if users.get(mid) == None:
        users[mid] = 'mainUS'
    if users.get(mid) == 'main':
        users[mid] = 'main_account'

    # Метрика
    metrik_id = str(mid)
    msg = Message(api_key=metrik_key,
                  platform="telegram",
                  user_id=metrik_id,
                  message="/alice",
                  intent="bot_"+str(users.get(mid)),
                  not_handled=False)
    resp = msg.send()

    if users[mid] == 'mainUS':
        bot.send_message(mid, 'Сначала вам нужно авторизироваться')
        return
    if users[mid] != 'main_account':
        bot.send_message(mid, 'Сначала вам нужно зайти в меню "Аккаунт"')
        return
    users[mid] += '_alice'
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT phrase,answer FROM alice WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        phrase = row[0]
        answer = row[1]
        bot.send_message(mid, 'Ваша фраза: ' + phrase + '\nВаш ответ: ' + answer, reply_markup = MUP[users[mid]])
        cur.close()
        conn.close()
        return
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="alice_add_yes")
    cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="alice_add_no")
    keybGR.add(cbtn1, cbtn2)
    users[mid] += 'add'
    bot.send_message(mid, 'У вас не задана фраза и ответ. Хотите добавить ее сейчас?', reply_markup = keybGR)

# Добавление новой пары вопрос-ответ 1/2
def alice_add1(message):
    mid = message.chat.id
    text = (message.text).lower()
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[users[mid]])
        return
    if check_text(text, 'rus'):
        users[mid] = prev_step(users[mid])
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[users[mid]])
        return
    if phrase_in(text):
        users[mid] = prev_step(users[mid])
        bot.send_message(mid, 'К сожалению, данная фраза занята', reply_markup = MUP[users[mid]])
        return
    vr[mid] = text
    sent = bot.send_message(mid, "Напишите фразу-ответ (без знаков препинания)", reply_markup = markupCanc)
    bot.register_next_step_handler(sent, alice_add2)

# Добавление новой пары вопрос-ответ 2/2
def alice_add2(message):
    mid = message.chat.id
    text = message.text.lower()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[users[mid]])
        return
    if check_text(text, 'rus'):
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("INSERT INTO alice (login,phrase,answer) VALUES ('%s','%s','%s')"%(kods[mid],vr[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] += '_alice'
    bot.send_message(mid, 'Успешно добавлено!\nВаша фраза: ' + vr[mid] + '\nВаш ответ: ' + text, reply_markup = MUP[users[mid]])

# Смена фразы-вопроса
def alice_change1(message):
    mid = message.chat.id
    text = (message.text).lower()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[users[mid]])
        return
    if check_text(text, 'rus'):
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[users[mid]])
        return
    if phrase_in(text):
        users[mid] = prev_step(users[mid])
        bot.send_message(mid, 'К сожалению, данная фраза занята', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE alice SET phrase = '%s' WHERE login = '%s'"%(text,kods[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Успешно изменено!\nВаша фраза: ' + text, reply_markup = MUP[users[mid]])

# Смена фразы-ответа
def alice_change2(message):
    mid = message.chat.id
    text = (message.text).lower()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[users[mid]])
        return
    if check_text(text, 'rus'):
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE alice SET answer = '%s' WHERE login = '%s'"%(text,kods[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Успешно изменено!\nВаш ответ: ' + text, reply_markup = MUP[users[mid]])

# Аутентификация диалога 
def alice_auth(message):
    mid = message.chat.id
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT id,phrase FROM alice WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="alice_auth_yes")
        cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="alice_auth_no")
        keybGR.add(cbtn1, cbtn2)
        vr[mid] = row[0]
        cur.close()
        conn.close()
        bot.send_message(mid, row[1] + '\nАвторизировать данную сессию?', reply_markup = keybGR)
        return
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    bot.send_message(mid, 'Нет диалогов для авторизации', reply_markup = MUP[users[mid]])

@bot.message_handler(commands=['gcheck'])
def gcheck(message):
    mid = message.chat.id
    bot.send_message(mid, users[mid])
    
@bot.message_handler(commands=['errors'])
def errors1(message):
    mid = message.chat.id
    users[mid] += '_errors'
    sent = bot.send_message(mid, 'Введите кодовое слово:')
    bot.register_next_step_handler(sent, errors2)

def errors2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == code and ERROR != 0:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('**да**')
        markup1.row('**нет**')
        LOGS = ''
        sent = bot.send_message(mid, 'ERROR: ' + str(ERROR) + '\n\nЗапустить бота?', reply_markup = markup1)
        users[mid] += '_errors'
        bot.register_next_step_handler(sent, errors3)
    elif text == code and ERROR == 0:
        bot.send_message(mid, users[mid])
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('**да**')
        markup1.row('**нет**')
        sent = bot.send_message(mid, 'Остановить бота?', reply_markup = markup1)
        users[mid] += '_errors'
        bot.register_next_step_handler(sent, errors4)
    else:
        bot.send_message(mid, 'Кодовое слово не верно')

def errors3(message):
    global ERROR
    mid = message.chat.id
    text = message.text
    text = text.lower()
    users[mid] = prev_step(users[mid])
    if text == '**да**':
        ERROR = 0
        bot.send_message(mid, 'Бот запущен', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Бот не запущен', reply_markup = MUP[users[mid]])

def errors4(message):
    global ERROR
    mid = message.chat.id
    text = message.text
    text = text.lower()
    users[mid] = prev_step(users[mid])
    if text == '**да**':
        ERROR = 1
        bot.send_message(mid, 'Бот остановлен', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Бот работает', reply_markup = MUP[users[mid]])

@bot.message_handler(commands=['start', 'help'])
def start(message):
    mid = message.chat.id
    if (users.get(mid) == None):
        users[mid] = 'mainUS'
    try:
        bot.send_message(mid , desc + '\nВерсия бота: ' + str(version) + '\n\nСписок изменений:' + chng, reply_markup = MUP[users[mid]])
    except Exception:
        bot.send_message(mid , desc + '\nВерсия бота: ' + str(version) + '\n\nСписок изменений:' + chng)

@bot.message_handler(content_types=['text'])
def main(message):
    mid = message.chat.id
    text = message.text
    text = text.lower()
    if users.get(mid) == None:
        users[mid] = 'mainUS'

    # Метрика
    metrik_id = str(mid)
    msg = Message(api_key=metrik_key,
                platform="telegram",
                user_id=metrik_id,
                message=text,
                intent="bot_"+str(users.get(mid)),
                not_handled=False)
    resp = msg.send()

    if ERROR != 0:
        bot.send_message(mid, 'Проводятся технические работы')
        return

    if users[mid] == 'mainUS':
        
        if text == '**регистрация**':
            sent = bot.send_message(mid, 'Пожалуйста, введите новый логин и пароль через пробел или в два разных сообщения:')
            users[mid] = 'mainUS_reg'
            bot.register_next_step_handler(sent, reg1)

        elif text == '**вход**':
            sent = bot.send_message(mid, 'Пожалуйста, введите свой логин и пароль через пробел или в два разных сообщения:')
            users[mid] = 'mainUS_login'
            bot.register_next_step_handler(sent, login1)

        elif text == '**о боте**':
            start(message)
        
    elif users[mid] == 'main':

        if kods.get(mid) == None:
            bot.send_message(admin_id, 'ERROR')
                
        elif text == '**о боте**':
            start(message)

        elif text == '**мои долги**':
            users[mid] = 'main_debt'
            watch_debts(message)

        elif text == '**мой кошелек**' or text == '**мой кошелёк**':
            users[mid] = 'main_bank'
            watch_bank(message)

        elif text == '**аккаунт**':
            users[mid] = 'main_account'
            bot.send_message(mid, 'Что вы хотите сделать?', reply_markup = MUP[users[mid]])

    elif users[mid] == 'main_account':
        
        if text == '**удалить аккаунт**':
            bot.send_message(mid, 'В разработке', reply_markup = MUP[users[mid]])####################################################################

        elif text == '**смена пароля**':
            sent = bot.send_message(mid, 'Введите старый пароль')
            users[mid] = 'main_account_changepass' 
            bot.register_next_step_handler(sent, chngpass1)

        elif text == '**выход**':
            kods.pop(mid)
            del_kod(mid)
            users[mid] = 'mainUS'
            bot.send_message(mid, 'Выход выполнен', reply_markup = MUP[users[mid]])

        elif text == '**назад**':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == '**алиса**':
            alice(message)

    elif users[mid] == 'main_account_alice':
         
        if text == '**поменять вопрос**':
            users[mid] += '_change'
            sent = bot.send_message(mid, "Напишите новую фразу-вопрос", reply_markup = markupCanc)
            bot.register_next_step_handler(sent, alice_change1)

        elif text == '**поменять ответ**':
            users[mid] += '_change'
            sent = bot.send_message(mid, "Напишите новую фразу-ответ", reply_markup = markupCanc)
            bot.register_next_step_handler(sent, alice_change2)

        elif text == '**авторизация диалога**':
            users[mid] += '_auth'
            alice_auth(message)

        elif text == '**активные сессии**':
            kol = 0
            stroka = "Количество активных сессий: "
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT id FROM zalog_alice WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
            cur.close()
            conn.close()
            if kol == 0:
                stroka = "Нет активных сессий"
                bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])
            else:
                stroka += str(kol) + "\nОтключить все активные сессии?"
                keybGR = types.InlineKeyboardMarkup()
                cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="alice_deauth_yes")
                cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="alice_deauth_no")
                keybGR.add(cbtn1, cbtn2)
                users[mid] += '_deauth'
                bot.send_message(mid, stroka, reply_markup = keybGR)
                

        elif text == '**помощь**':
            bot.send_message(mid, """
Итак, вы должны сказать кодовую фразу-вопрос Алисе. Она должна понять вас и сказать вашу фразу-ответ.
После этого вы опять долны сказать Алисе какую-то фразу, которую она отправит сюда.
Далее вы нажимаете на книпку "Авторизация диалога". Он присылает вам фразу.
Если фраза совпадает с той, что вы сказали Алисе, то вам нужно нажать кнопку "Да" и все заработает!
Теперь вы можете пользоваться ботом через Алису!
Удачи!
            """, reply_markup = MUP[users[mid]])

        elif text == '**назад**':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

    elif users[mid] == 'main_debt':

        if text == '**добавить долг**':
            vr[mid] = []
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].lower())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите счет, с которого вы даете долг', reply_markup = markup1)
            users[mid] = 'main_debt_add'
            bot.register_next_step_handler(sent, addcredit1)

        elif text == '**мои долги**':
            watch_debts(message)

        elif text == '**редактировать**':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("SELECT cred FROM credits WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Введите фамилию и имя должника, у которого хотите изменить долг или отмена', reply_markup = markup1)
            users[mid] = 'main_debt_edit'
            bot.register_next_step_handler(sent, edit1)

        elif text == '**назад**':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == '**мои группы**':####################################################################################################################
            return
            bot.send_message(mid, "Данная функция пока недоступна", reply_markup = MUP[users[mid]])
            return
            stroka = ""
            stroka += 'Ваши группы:\n'
            markupGR = types.ReplyKeyboardMarkup()
            markupGR.row('**Добавить группу**')
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            i = 1
            cur.execute("SELECT name, kol FROM groups WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                stroka += str(i) + ') ' + row[0] + '\nКоличество людей: ' + str(row[1]) + '\n\n'
                markupGR.row(row[0])
                i = i + 1
            markupGR.row('**Назад**')
            cur.close()
            conn.close()
            if i == 1:
                stroka = 'У вас нет групп'
            sent = bot.send_message(mid, stroka, reply_markup = markupGR)
            users[mid] = 'main_debt_group'
            bot.register_next_step_handler(sent, group1)

    elif users[mid] == 'main_bank':

        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == '**баланс**':
            watch_bank(message)

        elif text == '**доходы**':
            catg[kods[mid]] = 'fin'
            bank_fin(mid)
            
        elif text == '**расходы**':
            catg[kods[mid]] = 'spend'
            bank_fin(mid)

        elif text == '**новый счет**':
            new_bank(mid)

        elif text == '**удалить счет**':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                markup1.row(row[0])
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, 'У вас нет счетов', reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_del'
            sent = bot.send_message(mid, 'Выберите счет, который хотите удалить или отмена', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_del)

        elif text == '**перевод**':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            vr[mid] = []
            vr1[mid] = []
            vr2[mid] = []
            vr3[mid] = []
            vr4[mid] = []
            cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                vr1[mid].append(row[0].lower())
                vr4[mid].append(row[0])
                vr3[mid].append(row[1])
                if row[1] > 0:		
                    markup1.row(row[0])
                    vr[mid].append(row[0].lower())
                    vr2[mid].append(row[1])
            cur.close()
            conn.close()
            if kol < 2:
                bot.send_message(mid, 'У вас недостаточно счетов', reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_tr'
            sent = bot.send_message(mid, 'Выберите счет, с которого хотите перевести средства (показаны счета с положительным балансом)', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_tr1)

    elif users[mid] == 'main_bank_spend' or users[mid] == 'main_bank_fin':

        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == '**новый расход**' or text == '**новый доход**':
            if spend[mid] == 'все':
                users[mid] += '_add'
                markup1 = types.ReplyKeyboardMarkup()
                markup1.row('**все**')
                conn = sqlite3.connect(user_db(kods[mid]))
                cur = conn.cursor()
                cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
                vr[mid] = []
                for row in cur:
                    markup1.row(row[0])
                    vr[mid].append(row[0].lower())
                cur.close()
                conn.close()
                vr1[mid] = 'new'
                sent = bot.send_message(mid, 'Для начала выберите счет для добавления позиции', reply_markup = markup1)
                bot.register_next_step_handler(sent, bank_fin_change)
                return
            
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            vr[mid] = []
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                markup1.row(row[0])
                vr[mid].append(row[0].lower())
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий, чтобы добавить новую позицию", reply_markup = MUP[users[mid]])
                return
            users[mid] += '_add'
            sent = bot.send_message(mid, "Выберите категорию\nТекущий счет: " + spend[mid], reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_add1)
            
        elif text == '**расходы за период**' or text == '**доходы за период**':
            users[mid] += '_his'
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**все**')
            vr[mid] = []
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].lower())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите категорию', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_his1)
                        
        elif text == '**поменять счет**':
            users[mid] += '_change'
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**все**')
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
            vr[mid] = []
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].lower())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите другой счет', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_change)

        elif text == '**категории**':
            users[mid] += '_cat'
            watch_cat(mid)

        elif text == '**редактировать расход**' or text == '**редактировать доход**':
            if spend[mid] == 'все':
                users[mid] += '_edit'
                markup1 = types.ReplyKeyboardMarkup()
                markup1.row('**все**')
                conn = sqlite3.connect(user_db(kods[mid]))
                cur = conn.cursor()
                cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
                vr[mid] = []
                for row in cur:
                    markup1.row(row[0])
                    vr[mid].append(row[0].lower())
                cur.close()
                conn.close()
                vr1[mid] = 'edit'
                sent = bot.send_message(mid, 'Для начала выберите счет для редактирования позиции', reply_markup = markup1)
                bot.register_next_step_handler(sent, bank_fin_change)
                return
            
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            vr[mid] = []
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                markup1.row(row[0])
                vr[mid].append(row[0].lower())
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[users[mid]])
                return
            users[mid] += '_edit'
            sent = bot.send_message(mid, "Выберите категорию, позицию из которой вы хотите редактировать\nТекущий счет: " + spend[mid], reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_edit1) 

    elif users[mid] == 'main_bank_spend_cat' or users[mid] == 'main_bank_fin_cat':

        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == '**добавить**':
            users[mid] += '_add'
            sent = bot.send_message(mid, 'Введите название новой категории', reply_markup = markupCanc)
            bot.register_next_step_handler(sent, bank_fin_cat_add)

        elif text == '**удалить**':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            vr[mid] = []
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].lower())
                kol += 1
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, 'У вас нет категорий', reply_markup = MUP[users[mid]])
                return
            users[mid] += '_del'
            sent = bot.send_message(mid, 'Внимание! Пока в истории есть операции с этой категорией, удаление невозможно.\nВыберите категорию, которую хотите удалить', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_cat_del)

        elif text == '**категории**':
            watch_cat(mid)

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

# Обработка регистрации 1/2
def reg1(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    try:
        log, pas = text.split()
    except Exception:
        if ' ' in text:
            bot.send_message(mid, 'Некорректный ввод')
            return
        else:
            log = text.lower()
            if len(log) > 32:
                bot.send_message(mid, 'Некорректный ввод. Слишком много символов')
                return
            if log not in logins:
                for i in range(len(log)):
                    if ((log[i]<'a' or log[i]>'z') and (log[i]<'0' or log[i]>'9')):
                        bot.send_message(mid, 'Некорректный ввод. Используйте только символы a...z или цифры')
                        return
                vr[mid] = log
                sent = bot.send_message(mid, 'Введите пароль')
                users[mid] = 'mainUS_reg'
                bot.register_next_step_handler(sent, reg2)
                return
            else:
                bot.send_message(mid, 'Пользователь с таким именем уже существует')
                return
    log = log.lower()
    if len(log) > 32:
        bot.send_message(mid, 'Некорректный ввод. Слишком много символов')
        return
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

        os.chdir('/root/debt/users/')
        os.mkdir(log)
        conn = sqlite3.connect(user_db(log))
        cur = conn.cursor()
        cur.execute("CREATE TABLE bank (login TEXT, name TEXT, bal REAL)")
        cur.execute("CREATE TABLE cats (login TEXT, cat TEXT)")
        cur.execute("CREATE TABLE credits (login TEXT, cred TEXT, time TEXT, sz	REAL)")
        cur.execute("CREATE TABLE fcats (login TEXT, cat TEXT)")
        cur.execute("CREATE TABLE groups (login TEXT, name TEXT, kol INTEGER, pep TEXT)")
        cur.execute("CREATE TABLE inc (login TEXT, year INTEGER, month INTEGER, day INTEGER, cat TEXT, bank TEXT, name TEXT, sum REAL)")
        cur.execute("CREATE TABLE spend (login TEXT, year INTEGER, month INTEGER, day INTEGER, cat TEXT, bank TEXT, name TEXT, sum REAL)")
        cur.execute("CREATE TABLE alice (id TEXT, phrase TEXT, login TEXT)")
        cur.close()
        conn.close()
        
        logins.append(log)
        
        #keybSET = types.InlineKeyboardMarkup()
        #cbtn = types.InlineKeyboardButton(text="Настроить аккаунт", callback_data="set")
        #keybSET.add(cbtn)
        #\nВы можете пройти первоначальную настройку нажав кнопку ниже
        bot.send_message(mid, 'Регистрация успешно пройдена! Рекомендуем вам удалить сообщение с паролем.')
    else:
        bot.send_message(mid, 'Пользователь с таким именем уже существует')
        
# Обработка регистрации 2/2
def reg2(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
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

    os.chdir('/root/debt/users/')
    os.mkdir(log)
    conn = sqlite3.connect(user_db(log))
    cur = conn.cursor()
    cur.execute("CREATE TABLE bank (login TEXT, name TEXT, bal REAL)")
    cur.execute("CREATE TABLE cats (login TEXT, cat TEXT)")
    cur.execute("CREATE TABLE credits (login TEXT, cred TEXT, time TEXT, sz	REAL)")
    cur.execute("CREATE TABLE fcats (login TEXT, cat TEXT)")
    cur.execute("CREATE TABLE groups (login TEXT, name TEXT, kol INTEGER, pep TEXT)")
    cur.execute("CREATE TABLE inc (login TEXT, year INTEGER, month INTEGER, day INTEGER, cat TEXT, bank TEXT, name TEXT, sum REAL)")
    cur.execute("CREATE TABLE spend (login TEXT, year INTEGER, month INTEGER, day INTEGER, cat TEXT, bank TEXT, name TEXT, sum REAL)")
    cur.execute("CREATE TABLE alice (id TEXT, phrase TEXT)")
    cur.close()
    conn.close()
    
    logins.append(log)

    ##########################################################################################################################################################
    #keybSET = types.InlineKeyboardMarkup()
    #cbtn = types.InlineKeyboardButton(text="Настроить аккаунт", callback_data="set")
    #keybSET.add(cbtn)
    #\nВы можете пройти первоначальную настройку нажав кнопку ниже
    bot.send_message(mid, 'Регистрация успешно пройдена! Рекомендуем вам удалить сообщение с паролем.')


# Вход в аккаунт 1/2
def login1(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
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
                users[mid] = 'mainUS_login'
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
            if row[0] == log:
                if row[1] == pas:
                    kods[mid] = log
                    cur.execute("INSERT INTO zalog (id,login) VALUES ('%d','%s')"%(mid,kods[mid]))
                    conn.commit()
                    users[mid] = 'main'
                    bot.send_message(mid, 'Авторизация пройдена! Рекомендуем вам удалить сообщение с паролем.', reply_markup = MUP[users[mid]])
                else:
                    bot.send_message(mid, 'Пара логин/пароль не верна')
                cur.close()
                conn.close()
                return
        cur.close()
        conn.close()
    else:
        bot.send_message(mid, 'Такого логина не существует')

# Вход в аккаунт 2/2
def login2(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    log = vr.pop(mid)
    pas = text
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    for row in cur:
        if row[0] == log:
            if row[1] == pas:
                kods[mid] = log
                cur.execute("INSERT INTO zalog (id,login) VALUES ('%d','%s')"%(mid,log))
                conn.commit()
                users[mid] = 'main'
                bot.send_message(mid, 'Авторизация пройдена! Рекомендуем вам удалить сообщение с паролем.', reply_markup = MUP[users[mid]])
            else:
                bot.send_message(mid, 'Пара логин/пароль не верна')
            cur.close()
            conn.close()
            return
    cur.close()
    conn.close()

# Смена пароля 1/2
def chngpass1(message):
    text = message.text
    mid = message.chat.id
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    for row in cur:
        if row[0] == kods[mid]:
            if row[1] == text:
                sent = bot.send_message(mid, 'Введите новый пароль')
                bot.register_next_step_handler(sent, chngpass2)
            else:
                bot.send_message(mid, 'Пароль набран неправильно')
                users[mid] = prev_step(users[mid])
            cur.close()
            conn.close()
            return

# Смена пароля 2/2
def chngpass2(message):
    pas = message.text
    users[mid] = prev_step(users[mid])
    for i in range(len(pas)):
        if ((pas[i]<'a' or pas[i]>'z') and (pas[i]<'0' or pas[i]>'9') and (pas[i]<'A' or pas[i]>'Z')):
            bot.send_message(mid, 'Некорректный ввод. Используйте только символы a..z, A..Z или цифры для пароля')
            return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = '%s' WHERE login = '%s'"%(pas,kods[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Пароль успешно изменен на ' + text + '\nРекомендуем удалить сообщение с паролем.')

# Добавление долга 1/2
def addcredit1(message):
    mid = message.chat.id
    text = message.text
    text = text.lower()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    if text not in vr[mid]:
        bot.send_message(mid, 'Такого счета нет', reply_markup = MUP[users[mid]])
        return
    vr[mid] = text
    sent = bot.send_message(mid, 'Введите фамилию, имя и размер долга через пробел', reply_markup = markupCanc)
    users[mid] = 'main_debt_add'
    bot.register_next_step_handler(sent, addcredit2)
    
# Добавление долга 2/2
def addcredit2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() != '**отмена**':
        try:
            fam, im, dolg = text.split()
            dolg = round(float(check_num(dolg)),2)
            dolg = str(dolg)
            fam, im = fam + ' ' + im, im + ' ' + fam
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
            return
        if check_text(fam.lower(), 'rus'):
            bot.send_message(mid, 'Используйте только русские буквы', reply_markup = MUP[users[mid]])
            return
        conn = sqlite3.connect(user_db(kods[mid]))
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            if (row[0].lower() == fam.lower()) or (row[0].lower() == im.lower()):
                bot.send_message(mid, 'Данный участник уже есть в базе. Пожалуйста, воспользуйтесь командой РЕДАКТИРОВАТЬ для изменения размера долга', reply_markup = MUP[users[mid]])
                cur.close()
                conn.close()
                return
        cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],vr[mid]))
        for row in cur:
            if row[0] < round(float(dolg),2):
                bot.send_message(mid, 'У вас нет столько денег', reply_markup = MUP[users[mid]])
                cur.close()
                conn.close()
                return
            sz = row[0]
        sz -= round(float(dolg),2)
        cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(sz,kods[mid],vr[mid]))
        tme[mid] = stday()
        cur.execute("INSERT INTO credits (login,cred,time,sz) VALUES ('%s','%s','%s','%f' )"%(kods[mid],fam,tme[mid],round(float(dolg),2)))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(mid, 'Долг успешно добавлен', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

# Редактирование долгов 1/3
def edit1(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    try:
        fam, im = text.split()
    except Exception:
        bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
        return
    vr[mid] = fam + ' ' + im
    vr1[mid] = []
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        markup1.row(row[0])
        vr1[mid].append(row[0].lower())
    cur.close()
    conn.close()
    sent = bot.send_message(mid, 'Выберите счет, на который будут положены деньги', reply_markup = markup1)
    users[mid] = 'main_debt_edit'
    bot.register_next_step_handler(sent, edit2)
    
# Редактирование долгов 2/3
def edit2(message):
    text = message.text.lower()
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    if text.lower() not in vr1[mid]:
        bot.send_message(mid, 'Такого счета нет', reply_markup = MUP[users[mid]])
        return
    vr1[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT sz FROM credits WHERE cred = '%s' AND login = '%s'"%(vr[mid],kods[mid]))
    for row in cur:
        markup1.row(str(-row[0]))
    cur.close()
    conn.close()
    sent = bot.send_message(mid, 'Введите сумму', reply_markup = markup1)
    users[mid] = 'main_debt_edit'
    bot.register_next_step_handler(sent, edit3)

# Редактирование долгов 3/3
def edit3(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text.lower() != '**отмена**':
        fam, im = vr[mid].split()
        fam, im = fam + ' ' + im, im + ' ' + fam
        vr.pop(mid)
        try:
            text = round(float(check_num(text)),2)
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
            return
        conn = sqlite3.connect(user_db(kods[mid]))
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
            bot.send_message(mid, 'Участник не найден', reply_markup = MUP[users[mid]])
            return
        else:
            if kdk == 2:
                fam = im
            zn = zn + text
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            if text > 0:
                cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],vr1[mid]))
                for row in cur:
                    if row[0] < text:
                        bot.send_message(mid, 'У вас нет столько денег', reply_markup = MUP[users[mid]])
                        cur.close()
                        conn.close()
                        return
            if zn == 0:
                cur.execute("DELETE FROM credits WHERE login = '%s' AND cred = '%s'"%(kods[mid],fam))
            else:
                cur.execute("UPDATE credits SET sz = '%f' WHERE login = '%s' AND cred = '%s'"%(zn,kods[mid],fam))
            cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],vr1[mid]))
            for row in cur:
                zn = row[0]
            zn -= text
            cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(zn,kods[mid],vr1[mid]))
            conn.commit()
            cur.close()
            conn.close()
            bot.send_message(mid, 'Операция успешно выполнена', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

# Группы 1/6
def group1(message):
    text = message.text
    mid = message.chat.id
    text = text.lower()
    users[mid] = prev_step(users[mid])
    if text != '**назад**':
        if text == '**добавить группу**':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            sent =bot.send_message(mid, 'Введите название группы', reply_markup = markup1)
            users[mid] = 'main_debt_group_add'
            bot.register_next_step_handler(sent, group2)
        else:
            stroka = 'Такой группы нет'
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("SELECT name,kol,pep FROM groups WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                if text.lower() == row[0].lower():
                    stroka = row[0] + '\nКоличество людей: ' + str(row[1]) + '\n' + row[2] + '\n\nВыберите действие'
                    users[mid] = 'main_debt_group_opr'
                    sent = bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])
                    vr[mid] = row[0]
                    bot.register_next_step_handler(sent, group4)
                    cur.close()
                    conn.close()
                    return
            cur.close()
            conn.close()
            bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])
    else:
      bot.send_message(mid, 'Выберите действие:', reply_markup = MUP[users[mid]])

# Группы 2/6
def group2(message):
    text = message.text
    mid = message.chat.id
    text1 = text.lower()
    users[mid] = prev_step(users[mid])
    if text != '**отмена**':
        conn = sqlite3.connect(user_db(kods[mid]))
        cur = conn.cursor()
        cur.execute("SELECT name FROM groups WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            if text1 == row[0].lower():
                bot.send_message(mid, 'Данная группа уже есть', reply_markup = MUP[users[mid]])
                cur.close()
                conn.close()
                return
        cur.close()
        conn.close()
        vr[mid] = text
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('**Отмена**')
        sent = bot.send_message(mid, 'Введите участников группы (имя и фамилия через пробел) в разных строчках', reply_markup = markup1)
        users[mid] = 'main_debt_group_add'
        bot.register_next_step_handler(sent, group3)
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

# Группы 3/6
def group3(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text != '**отмена**':
        text1 = text.split('\n')
        i = 0
        for row in text1:
            i = i + 1
            try:
                fam, im = row.split()
            except Exception:
                bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
                vr.pop(mid)
                return
        conn = sqlite3.connect(user_db(kods[mid]))
        cur = conn.cursor()
        cur.execute("INSERT INTO groups (login,name,kol,pep) VALUES ('%s','%s','%d','%s')"%(kods[mid],vr[mid],i,text))
        conn.commit()
        cur.close()
        conn.close()
        vr.pop(mid)
        bot.send_message(mid, 'Группа создана' + users[mid], reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

# Группы 4/6
def group4(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text.lower() == '**меню**':
        bot.send_message(mid, 'Вот меню:', reply_markup = MUP[users[mid]])
    elif text.lower() == 'УДАЛИТЬ ГРУППУ':
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="gr_del_yes")
        cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="gr_del_no")
        keybGR.add(cbtn1, cbtn2)
        users[mid] = 'main_debt_group_del'
        bot.send_message(mid, 'Удалить группу "' + vr[mid] + '"?', reply_markup = keybGR)
    elif text.lower() == 'ДОБАВИТЬ ДОЛГ':
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="gr_yes")
        cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="gr_no")
        keybGR.add(cbtn1, cbtn2)
        users[mid] = 'main_debt_group_newdebt'
        bot.send_message(mid, 'Вы хотите добавить существующим учасиникам долг или оставить их долг таким же?', reply_markup = keybGR)  
    else:
        bot.send_message(mid, 'Я вас не понимаю. Вот меню:', reply_markup = MUP[users[mid]])

# Группы 5/6
def group5(message):
    text = message.text
    mid = message.chat.id
    if text != '**отмена**':
        try:
            text = round(float(check_num(text)),2)
        except Exception:
            users[mid] = 'main_debt_group'
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return
        pep1 = []
        pep2 = []
        conn = sqlite3.connect(user_db(kods[mid]))
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
            tme[mid] = stday()
            cur.execute("INSERT INTO credits (login,cred,time,sz) VALUES ('%s','%s','%s','%f')"%(kods[mid],row,tme[mid],text))
            conn.commit()
        for fam in pep1:
            cur.execute("SELECT sz FROM credits WHERE login = '%s' AND cred = '%s'"%(kods[mid],fam))
            zn = 0
            for row in cur:
                zn = row[0] + text
            if zn == 0:
                cur.execute("DELETE FROM credits WHERE login = '%s' AND cred = '%s'"%(kods[mid],fam))
            else:
                cur.execute("UPDATE credits SET sz = '%f' WHERE login = '%s' AND cred = '%s'"%(zn,kods[mid],fam))
            conn.commit()
        cur.close()
        conn.close()
        users[mid] = 'main_debt'
        bot.send_message(mid, 'Операция выполнена', reply_markup = MUP[users[mid]])
    else:
        users[mid] = 'main_debt'
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

# Группы 6/6
def group6(message):
    text = message.text
    mid = message.chat.id
    if text != '**отмена**':
        try:
            text = round(float(check_num(text)),2)
        except Exception:
            users[mid] = 'main_debt_group'
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return
        pep2 = []
        conn = sqlite3.connect(user_db(kods[mid]))
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
            tme[mid] = stday()
            cur.execute("INSERT INTO credits (login,cred,time,sz) VALUES ('%s','%s','%s','%f')"%(kods[mid],row,tme[mid],text))
            conn.commit()
        cur.close()
        conn.close()
        users[mid] = 'main_debt_group'
        bot.send_message(mid, 'Операция выполнена', reply_markup = MUP[users[mid]])
    else:
        users[mid] = 'main_debt_group'
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

# Просмотр должников
def watch_debts(message):
    mid = message.chat.id
    kol = 0
    osum = 0
    stroka = ""
    stroka += 'Ваши должники:\n'
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT cred, sz, time FROM credits WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        stroka += row[0] + ' ' + str(row[1]) + ' от ' + row[2] + '\n'
        kol = kol + 1
        osum += row[1]
    stroka += 'Всего человек: ' + str(kol) + '\nСумма: ' + str(round(osum,2))
    if kol == 0:
        stroka = 'У вас нет должников'
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])
    cur.close()
    conn.close()

# Просмотр счетов
def watch_bank(message):
    mid = message.chat.id
    kol = 0
    osum = 0
    sdebt = 0
    stroka = ""
    stroka += 'Ваши счета:\n'
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        kol += 1
        stroka += str(kol) + ') ' + row[0] + '\nБаланс: ' + str(row[1]) + '\n\n'
        osum += row[1]
    stroka += 'Сумма: ' + str(round(osum,2))

    cur.execute("SELECT sz FROM credits WHERE login = '%s'"%(kods[mid]))    
    for row in cur:
        sdebt += row[0]
    stroka += '\nСумма, учитывая долги: ' + str(round(osum+sdebt,2))
    cur.close()
    conn.close()
    
    if kol == 0:
        stroka = 'У вас нет счетов'
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])

# Создание нового счета 1/3
def new_bank(mid):
    sent = bot.send_message(mid, 'Введите название счета (до 32 символов)', reply_markup = markupCanc)
    users[mid] = 'main_bank_add'
    bot.register_next_step_handler(sent, bank_add1)

# Создание нового счета 2/3
def bank_add1(message):
    mid = message.chat.id
    text = message.text
    text = text.lower()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    if text == '**все**':
        bot.send_message(mid, 'Пожалуйста, выберите другое имя', reply_markup = MUP[users[mid]])
        return
    if len(text) > 32:
        bot.send_message(mid, 'Слишком длинное название', reply_markup = MUP[users[mid]])
        return
    if check_text(text.lower(), 'rus1'):
        bot.send_message(mid, 'Используйте только русские буквы, пробел или цифры', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].lower() == text.lower():
            bot.send_message(mid, 'Данный счет уже есть в базе', reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    cur.close()
    conn.close()
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('0')
    sent = bot.send_message(mid, 'Введите начальный баланс счета', reply_markup = markup1)
    users[mid] = 'main_bank_add'
    bot.register_next_step_handler(sent, bank_add2)

# Создание нового счета 3/3
def bank_add2(message):
    mid = message.chat.id
    text = message.text
    text = text.lower()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    if text[0] == '-':
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
        return
    try:
        text = round(float(check_num(text)),2)
    except Exception:
        bot.send_message(mid, 'Неверный формат ввода', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("INSERT INTO bank (login,name,bal) VALUES ('%s','%s',%f)"%(kods[mid],vr[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Счет добавлен', reply_markup = MUP[users[mid]])

# Удаление счета
def bank_del(message):
    mid = message.chat.id
    text = message.text.lower()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE name = '%s' AND login = '%s'"%(text,kods[mid]))
    kod = 1
    for row in cur:
        kod = 0
    if kod == 1:
        bot.send_message(mid, 'Данного счета не существует', reply_markup = MUP[users[mid]])
        cur.close()
        conn.close()
        return
    cur.execute("SELECT bank FROM spend WHERE bank = '%s'"%(text))
    for row in cur:
        bot.send_message(mid, 'Сначала необходимо удалить операции с данным счетом', reply_markup = MUP[users[mid]])
        cur.close()
        conn.close()
        return
    cur.execute("SELECT bank FROM inc WHERE bank = '%s'"%(text))
    for row in cur:
        bot.send_message(mid, 'Сначала необходимо удалить операции с данным счетом', reply_markup = MUP[users[mid]])
        cur.close()
        conn.close()
        return
    cur.close()
    conn.close()    
    if text.lower() == spend[mid].lower():
        bot.send_message(mid, 'Сначала выберите другой счет', reply_markup = MUP[users[mid]])
        return
    users[mid] = 'main_bank_del'
    vr[mid] = text
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="bank_del_yes")
    cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="bank_del_no")
    keybGR.add(cbtn1, cbtn2)
    bot.send_message(mid, 'Вы уверены, что хотите удалить счет? Его баланс будет удален!', reply_markup = keybGR)

# Главная расходы/доходы
def bank_fin(mid):
    kol = 0
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        kol += 1
    cur.close()
    conn.close()
    if kol == 0:
        bot.send_message(mid, 'У вас нет счетов', reply_markup = MUP[users[mid]])
        return
    users[mid] += '_' + catg[kods[mid]]
    if spend.get(mid) == None:
        spend[mid] = 'все'
    bot.send_message(mid, "Выберите действие. Текущий счет: " + spend[mid], reply_markup = MUP[users[mid]])

# Смена счета
def bank_change(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == '**все**':
        spend[mid] = 'все'
        bot.send_message(mid, "Выбраны все счета", reply_markup = MUP[users[mid]])
    elif text.lower() not in vr[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[users[mid]])
    else:
        spend[mid] = text
        bot.send_message(mid, "Выбран счет: " + spend[mid], reply_markup = MUP[users[mid]])
    vr.pop(mid)

# Смена счета для добавления/редактирования расходов/доходов
def bank_fin_change(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == '**все**':
        spend[mid] = 'все'
        bot.send_message(mid, "Нельзя выбрать все счета", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    elif text.lower() not in vr[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    vr.pop(mid)
    spend[mid] = text

    if vr1[mid] == 'new':
        vr1.pop(mid)
        kol = 0
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('**Отмена**')
        vr[mid] = []
        conn = sqlite3.connect(user_db(kods[mid]))
        cur = conn.cursor()
        if catg[kods[mid]] == 'spend':
            cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
        elif catg[kods[mid]] == 'fin':
            cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            kol += 1
            markup1.row(row[0])
            vr[mid].append(row[0].lower())
        cur.close()
        conn.close()
        if kol == 0:
            bot.send_message(mid, "У вас нет категорий, чтобы добавить новую позицию", reply_markup = MUP[users[mid]])
            return
        users[mid] += '_add'
        sent = bot.send_message(mid, "Выберите категорию\nТекущий счет: " + spend[mid], reply_markup = markup1)
        bot.register_next_step_handler(sent, bank_fin_add1)

    elif vr1[mid] == 'edit':
        vr1.pop(mid)
        kol = 0
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('**Отмена**')
        vr[mid] = []
        conn = sqlite3.connect(user_db(kods[mid]))
        cur = conn.cursor()
        if catg[kods[mid]] == 'spend':
            cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
        elif catg[kods[mid]] == 'fin':
            cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            kol += 1
            markup1.row(row[0])
            vr[mid].append(row[0].lower())
        cur.close()
        conn.close()
        if kol == 0:
            bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[users[mid]])
            return
        users[mid] += '_edit'
        sent = bot.send_message(mid, "Выберите категорию, позицию из которой вы хотите редактировать\nТекущий счет: " + spend[mid], reply_markup = markup1)
        bot.register_next_step_handler(sent, bank_fin_edit1) 

# Просмотр категорий
def watch_cat(mid):
    kol = 0
    stroka = ""
    stroka += 'Ваши категории:\n'
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    if catg[kods[mid]] == 'spend':
        cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
    elif catg[kods[mid]] == 'fin':
        cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        kol += 1
        stroka += str(kol) + ') ' + row[0] + '\n\n'
    cur.close()
    conn.close()
    if kol == 0:
        stroka = 'У вас нет категорий'
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])

# Создание новой категории
def bank_fin_cat_add(message):
    mid = message.chat.id
    text = message.text
    text = text.lower()
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.lower() == '**все**':
        bot.send_message(mid, "Данное имя выбрать невозможно", reply_markup = MUP[users[mid]])
        return
    if check_text(text.lower(), 'rus1'):
        bot.send_message(mid, 'Используйте только русские буквы, пробел или цифры', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    if catg[kods[mid]] == 'spend':
        cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
    elif catg[kods[mid]] == 'fin':
        cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].lower() == text.lower():
            bot.send_message(mid, "Данная категория уже существует", reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    if catg[kods[mid]] == 'spend':
        cur.execute("INSERT INTO cats (login,cat) VALUES ('%s','%s')"%(kods[mid],text))
    elif catg[kods[mid]] == 'fin':
        cur.execute("INSERT INTO fcats (login,cat) VALUES ('%s','%s')"%(kods[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Категория добавлена", reply_markup = MUP[users[mid]])

# Удаление категории
def bank_fin_cat_del(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.lower() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    if catg[kods[mid]] == 'spend':
        cur.execute("SELECT cat FROM spend WHERE login = '%s'"%(kods[mid]))
    elif catg[kods[mid]] == 'fin':
        cur.execute("SELECT cat FROM inc WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].lower() == text.lower():
            bot.send_message(mid, "Данная категория используется, удаление невозможно", reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    if catg[kods[mid]] == 'spend':
        cur.execute("DELETE FROM cats WHERE login = '%s' AND cat = '%s'"%(kods[mid],text))
    elif catg[kods[mid]] == 'fin':
        cur.execute("DELETE FROM fcats WHERE login = '%s' AND cat = '%s'"%(kods[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Удаление выполнено", reply_markup = MUP[users[mid]])

# История 1/3
def bank_fin_his1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() not in vr[mid] and text.lower() != '**все**':
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    if text == '**все**':
        text = 'все'
    vr[mid] = text
    users[mid] += '_his'
    sent = bot.send_message(mid, 'Выберите период просмотра.\nДопустимый формат ввода: гггг (расходы будут показываться по месяцам); мм гггг; дд мм гггг; мм гггг мм гггг (расходы будут показываться по месяцам); дд мм гггг дд мм гггг (последние два подразумевают ввод момента С и момента ДО)', reply_markup = MUP[users[mid]])
    bot.register_next_step_handler(sent, bank_fin_his2)

# История 2/3
def bank_fin_his2(message):
    mid = message.chat.id
    text = message.text
    text = text.lower()
    show = 1
    tm = tday()
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    kod_mon = 0
    if text == '**сегодня**':
        sday = int(tm[0])
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])
        
    elif text == '**вчера**':
        tm = lday()
        sday = int(tm[0])
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])
        
    elif text == '**этот месяц**':
        sday = 1
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])

    elif text == '**прошлый месяц**':
        tm = lmon()
        sday = 1
        fday = 31
        smon = int(tm[0])
        fmon = int(tm[0])
        syear = int(tm[1])
        fyear = int(tm[1])

    elif text == '**эта неделя**':
        sday, smon, syear, fday, fmon, fyear = tweek()

    elif text == '**прошлая неделя**':
        sday, smon, syear, fday, fmon, fyear = tweek(7)

    elif text == '**позапрошлая неделя**':
        sday, smon, syear, fday, fmon, fyear = tweek(14)

    elif 'недел' in text:
        text = text.split()
        try:
            k = int(text[0])
        except Exception:
            bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return
        show = 0
        for i in range(k, -1, -1):
            sday, smon, syear, fday, fmon, fyear = tweek(7 * i)
            stroka, diag = bank_fin_his3(sday, smon, syear, fday, fmon, fyear, mid, kod_mon, show)
            if diag == 1:
                try:
                    diag = open(user_res(kods[mid]) + 'diag.png','rb')
                    bot.send_photo(mid, diag)
                except Exception as e:
                    bot.send_message(admin_id, str(e))
            bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])
        return

    else:
        try:
            text = text.split()
            if len(text) == 1:
                sday = 1
                fday = 31
                smon = 1
                fmon = 12
                syear = int(text[0])
                fyear = int(text[0])
                kod_mon = 1
            elif len(text) == 2:
                sday = 1
                fday = 31
                smon = int(text[0])
                fmon = int(text[0])
                syear = int(text[1])
                fyear = int(text[1])
            elif len(text) == 3:
                sday = int(text[0])
                fday = int(text[0])
                smon = int(text[1])
                fmon = int(text[1])
                syear = int(text[2])
                fyear = int(text[2])
            elif len(text) == 4:
                sday = 1
                fday = 31
                smon = int(text[0])
                fmon = int(text[2])
                syear = int(text[1])
                fyear = int(text[3])
                kod_mon = 1
            elif len(text) == 6:
                sday = int(text[0])
                fday = int(text[3])
                smon = int(text[1])
                fmon = int(text[4])
                syear = int(text[2])
                fyear = int(text[5])
        except Exception:
            bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return

    if sday < 1 or sday > 31 or fday < 1 or fday > 31 or smon < 1 or smon > 12 or fmon < 1 or fmon > 12 or syear < 2000 or fyear < syear or (fyear == syear and fmon < smon) or (fyear == syear and fmon == smon and fday < sday):
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    stroka, diag = bank_fin_his3(sday, smon, syear, fday, fmon, fyear, mid, kod_mon, show)
    if diag == 1:
        try:
            diag = open(user_res(kods[mid]) + 'diag.png','rb')
            bot.send_photo(mid, diag)
        except Exception as e:
            bot.send_message(admin_id, str(e)) 
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])

# История 3/3
def bank_fin_his3(sday, smon, syear, fday, fmon, fyear, mid, kod_mon, show):
    if catg[kods[mid]] == 'spend':
        stroka = "Ваши расходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear) + "\n"
        title = "Расходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear)
    elif catg[kods[mid]] == 'fin':
        stroka = "Ваши доходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear) + "\n"
        title = "Доходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear)
    if spend[mid] != 'все':
        stroka += "Счет: " + spend[mid] + "\n"
        title += "\nСчет: " + spend[mid]
    if vr[mid] != 'все':
        stroka += "Категория: " + vr[mid] + "\n"
    stroka += "\n"
    year = syear
    mon = smon
    day = sday
    osum = 0
    kod = 0
    kodK = 0
    kol1 = 0
    cat_s = dict()
    mon_s = dict()
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    while kod == 0:
        if spend[mid] == 'все' and vr[mid] == 'все':
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d'"%(kods[mid],year,mon,day))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d'"%(kods[mid],year,mon,day))
        elif spend[mid] != 'все' and vr[mid] == 'все':
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(kods[mid],year,mon,day,spend[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(kods[mid],year,mon,day,spend[mid]))
        elif spend[mid] == 'все' and vr[mid] != 'все':
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(kods[mid],year,mon,day,vr[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(kods[mid],year,mon,day,vr[mid]))
        elif spend[mid] != 'все' and vr[mid] != 'все':
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT name, sum FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],year,mon,day,spend[mid],vr[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT name, sum FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],year,mon,day,spend[mid],vr[mid]))
        stroka1 = str(day) + "." + str(mon) + "." + str(year) + ":\n"
        kol = 0
        for row in cur:
            osum += round(row[1],2)
            kol += 1
            kol1 += 1
            if vr[mid] == 'все':
                if kod_mon == 1:
                    if mon_s.get(str(year) + ' ' + str(mon)) == None:
                        mon_s[str(year) + ' ' + str(mon)] = dict()
                stroka1 += "Категория: " + row[2] + "\n"
                if cat_s.get(row[2]) != None:
                    cat_s[row[2]] += round(row[1],2)
                else:
                    cat_s[row[2]] = round(row[1],2)
                if kod_mon == 1:
                    try:
                        mon_s[str(year) + ' ' + str(mon)][row[2]] += round(row[1],2)
                    except KeyError:
                        mon_s[str(year) + ' ' + str(mon)][row[2]] = round(row[1],2)
            else:
                try:
                    if kod_mon == 1:
                        mon_s[str(year) + ' ' + str(mon)] += round(row[1],2)
                except KeyError:
                    if kod_mon == 1:
                        mon_s[str(year) + ' ' + str(mon)] = round(row[1],2)
            if spend[mid] == 'все':
                stroka1 += "Счет: " + row[3] + "\n"
            txt = row[0]
            txt = txt.split('%')
            if len(txt[0]) == 0:
                stroka1 +=  "Сумма: " + str(round(row[1],2)) + "\n\n"
            else:
                stroka1 +=  "Сумма: " + str(round(row[1],2)) + "\n" + txt[0] + "\n\n"

            
        if kol > 0 and kodK == 0 and kod_mon != 1 and show == 1:
            stroka += stroka1 + "\n"
        if year == fyear and mon == fmon and day == fday:
            kod = 1
        day += 1
        if day > 31:
            day = 1
            mon += 1
            if mon > 12:
                mon = 1
                year += 1
        if len(stroka) >= 4000:
            stroka = "Слишком много элементов\n"
            kodK = 1

    cur.close()
    conn.close()

    if kol1 == 0:
        stroka =  "В период с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear) + " по данным категориям и счету ничего нет"
        return stroka, 0
    
    if kod_mon == 1:
        if vr[mid] == 'все':
            for i in sorted(mon_s):
                stroka += 'Месяц: ' + i + '\n'
                osum1 = 0
                for j in sorted(mon_s[i]):
                    stroka += str(j) + ': ' + str(round(mon_s[i][j],2)) + '\n'
                    osum1 += mon_s[i][j]
                stroka += 'Итого за месяц: ' + str(round(osum1,2)) + '\n'
                stroka += '\n'
        else:
            for i in sorted(mon_s):
                stroka += 'Месяц: ' + i + '\n'
                stroka += 'Сумма: ' + str(round(mon_s[i],2)) + '\n'
                stroka += '\n'
    diag = 0
    if vr[mid] == 'все':
        diag = 1
        data_names = []
        data_values = []
        cat_s = list(cat_s.items())
        for i in range(len(cat_s)):
            cat_s[i] = list(cat_s[i])
            cat_s[i][0], cat_s[i][1] = cat_s[i][1], cat_s[i][0]
        cat_s.sort()
        cat_s.reverse()
        stroka += 'Всего по категориям:\n'
        for elem in cat_s:
            data_names.append(elem[1])
            data_values.append(round(elem[0],2))
            stroka += elem[1] + ': ' + str(round(elem[0],2)) + '\n'
        try:
            make_diag(kods[mid], title, data_names, data_values)
        except Exception as e:
            diag = -1
            bot.send_message(admin_id, str(e)) 
            #make_diag(kods[mid], title, data_names, data_values)
    #vr.pop(mid)        
    stroka += 'Итого: ' + str(round(osum,2))
    while len(stroka) >= 4000:
            bot.send_message(mid, stroka[:4000], reply_markup = MUP[users[mid]])
            stroka = stroka[4000:]
            #stroka = "Слишком много элементов\n"
    #bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])
    return stroka, diag

# Добавление 1/3
def bank_fin_add1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.lower() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    vr[mid] = text.lower()
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('**Сегодня**')
    markup1.row('**Вчера**')
    users[mid] += '_add'
    if catg[kods[mid]] == 'spend':
        sent = bot.send_message(mid, "За какое число расход? (Формат: дд мм гггг", reply_markup = markup1)
    elif catg[kods[mid]] == 'fin':
        sent = bot.send_message(mid, "За какое число доход? (Формат: дд мм гггг", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_fin_add2)

# Добавление 2/3
def bank_fin_add2(message): #дата
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.lower() == '**сегодня**':
        tme[mid] = tday()
    elif text.lower() == '**вчера**':
        tme[mid] = lday()
    else:
        text = text.split()
        try:
            for i in range(len(text)):
                text[i] = int(text[i])
            tme[mid] = text
        except Exception:
            bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return
    if tme[mid][0] < 1 or tme[mid][0] > 31 or tme[mid][1] < 1 or tme[mid][1] > 12:
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    users[mid] += '_add'
    if catg[kods[mid]] == 'spend':
        sent = bot.send_message(mid, "Напишите расход в формате: описание (не обязательно, не должно начинаться с числа) + сумма расхода")
    elif catg[kods[mid]] == 'fin':
        sent = bot.send_message(mid, "Напишите доход в формате: описание (не обязательно, не должно начинаться с числа) + сумма дохода")
    bot.register_next_step_handler(sent, bank_fin_add3)

# Добавление 3/3
def bank_fin_add3(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    text = text.split()
    ras = 0
    if text[len(text)-1] == '-':
        if catg[kods[mid]] == 'spend':
            bot.send_message(mid, "Отрицательный расход? Хаха, нет", reply_markup = MUP[users[mid]])
        elif catg[kods[mid]] == 'fin':
            bot.send_message(mid, "Отрицательный доход? Хаха, нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    try:
        ras = round(float(check_num((text[len(text)-1]))),2)
    except Exception:
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    text.pop()
    if len(text) == 0:
        text = '%' + str(nums())
    else:
        text = ' '.join(text)
        if '%' in text:
            bot.send_message(mid, "Не используйте % в описании", reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return
        if check_text(text.lower(), 'ruseng1'):
            bot.send_message(mid, 'Используйте только русские или латинские буквы, пробел или цифры', reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return
        text += '%' + str(nums())
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
    for row in cur:
        bal = round(float(row[0]),2)
    if catg[kods[mid]] == 'spend':
        bal -= ras
    elif catg[kods[mid]] == 'fin':
        bal += ras
    if bal < 0:
        bot.send_message(mid, "У вас столько нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        cur.close()
        conn.close()
        return
    tm = tme[mid]
    tme.pop(mid)
    cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(bal,kods[mid],spend[mid]))
    if catg[kods[mid]] == 'spend':
        cur.execute("INSERT INTO spend (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(kods[mid],tm[2],tm[1],tm[0],vr[mid],spend[mid],text.lower(),ras))
    elif catg[kods[mid]] == 'fin':
        cur.execute("INSERT INTO inc (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(kods[mid],tm[2],tm[1],tm[0],vr[mid],spend[mid],text.lower(),ras))
    conn.commit()
    cur.close()
    conn.close()
    vr.pop(mid)
    bot.send_message(mid, "Операция выполнена", reply_markup = MUP[users[mid]])

# Редактирование 1/5
def bank_fin_edit1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.lower() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('**Сегодня**')
    markup1.row('**Вчера**')
    users[mid] += '_edit'
    sent = bot.send_message(mid, "Позицию за какое число вы хотите редактировать? (Формат: дд мм гггг)", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_fin_edit2)

# Редактирование 2/5
def bank_fin_edit2(message): #дата
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.lower() == '**сегодня**':
        tme[mid] = tday()
    elif text.lower() == '**вчера**':
        tme[mid] = lday()
    else:
        text = text.split()
        try:
            for i in range(len(text)):
                text[i] = int(text[i])
            tme[mid] = text
        except Exception:
            bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return
    if tme[mid][0] < 1 or tme[mid][0] > 31 or tme[mid][1] < 1 or tme[mid][1] > 12:
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    if catg[kods[mid]] == 'spend':
        stroka = "Ваши расходы по данным параметрам\n\n"
    elif catg[kods[mid]] == 'fin':
        stroka = "Ваши доходы по данным параметрам\n\n"
    kol = 0
    vr1[mid] = {}
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    if catg[kods[mid]] == 'spend':
        cur.execute("SELECT name, sum FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid]))
    elif catg[kods[mid]] == 'fin':
        cur.execute("SELECT name, sum FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid]))
    for row in cur:
        kol += 1
        txt = row[0]
        txt = txt.split('%')
        markup1.row(str(kol))
        stroka += 'Номер ' + str(kol) + '\n' + 'Сумма: ' + str(row[1]) + '\n' + txt[0] + '\n\n'
        vr1[mid][str(kol)] = row[0] #номер и описание
    cur.close()
    conn.close()
    if kol == 0:
        bot.send_message(mid, "Нет таких позиций", reply_markup = MUP[users[mid]])
        return
    users[mid] += '_edit'
    stroka += "Выберите номер позиции, которую хотите редактировать"
    sent = bot.send_message(mid, stroka, reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_fin_edit3)

# Редактирование 3/5
def bank_fin_edit3(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr1.pop(mid)
        return
    if text not in vr1[mid]:
        bot.send_message(mid, "Неверный формат или такой позиции нет", reply_markup = MUP[users[mid]])
        vr1.pop(mid)
        return
    txt = vr1[mid][text]
    vr2[mid] = txt
    txt = txt.split('%')
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    if catg[kods[mid]] == 'spend':
        cur.execute("SELECT sum FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    elif catg[kods[mid]] == 'fin':
        cur.execute("SELECT sum FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    for row in cur:
        vr3[mid] = row[0]
        stroka = 'Что вы хотите сделать?\nДата:' + str(tme[mid][0]) + '.' + str(tme[mid][1]) + '.' + str(tme[mid][2]) + '\n'
        stroka += 'Счет: ' + spend[mid] + '\nКатегория: ' + vr[mid] + '\nСумма: ' + str(vr3[mid]) + '\n'
        if len(txt[0]) != 0:
            stroka += txt[0]
    cur.close()
    conn.close()
    users[mid] += '_edit'
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Удалить", callback_data="bank_fin_del_yes")###
    cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="bank_fin_del_no")###
    keybGR.add(cbtn1, cbtn2)
    cbtn1 = types.InlineKeyboardButton(text="Поменять категорию", callback_data="bank_fin_chngcat")###
    keybGR.add(cbtn1)
    cbtn1 = types.InlineKeyboardButton(text="Поменять сумму", callback_data="bank_fin_chngsum")###
    keybGR.add(cbtn1)
    bot.send_message(mid, stroka, reply_markup = keybGR)

# Редактирование 4/5
def bank_fin_edit4(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text not in vr1[mid]:
        bot.send_message(mid, "У вас нет такой категории", reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    if catg[kods[mid]] == 'spend':
        cur.execute("UPDATE spend SET cat = '%s' WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND name = '%s'"%(text,kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr2[mid]))
    elif catg[kods[mid]] == 'fin':
        cur.execute("UPDATE inc SET cat = '%s' WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND name = '%s'"%(text,kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr2[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Категория изменена", reply_markup = MUP[users[mid]])

# Редактирование 5/5
def bank_fin_edit5(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    ras = 0
    if text[0] == '-':
        if catg[kods[mid]] == 'spend':
            bot.send_message(mid, "Отрицательный расход? Хаха, нет", reply_markup = MUP[users[mid]])
        if catg[kods[mid]] == 'inc':
            bot.send_message(mid, "Отрицательный доход? Хаха, нет", reply_markup = MUP[users[mid]])
        return
    try:
        ras = round(float(check_num((text))),2)
    except Exception:
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
    for row in cur:
        bal = round(float(row[0]),2)
    if catg[kods[mid]] == 'spend':
        bal += (vr3[mid]-ras)
    elif catg[kods[mid]] == 'fin':
        bal -= (vr3[mid]-ras)
    if bal < 0:
        bot.send_message(mid, "Операция невозможна, так как баланс стал отрицательным", reply_markup = MUP[users[mid]])
        cur.close()
        conn.close()
        return
    cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(bal,kods[mid],spend[mid]))
    if catg[kods[mid]] == 'spend':
        cur.execute("UPDATE spend SET sum = '%f' WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(ras,kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    elif catg[kods[mid]] == 'fin':
        cur.execute("UPDATE inc SET sum = '%f' WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(ras,kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Сумма изменена", reply_markup = MUP[users[mid]])

# Перевод 1/3
def bank_tr1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.lower() not in vr[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[users[mid]])
        return
    vr2[mid] = vr2[mid][vr[mid].index(text.lower())]
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    for i in vr4[mid]:
        if i != vr[mid]:
            markup1.row(i)            
    users[mid] = 'main_bank_tr'
    sent = bot.send_message(mid, 'Выберите счет, на который хотите перевести средства', reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_tr2)

# Перевод 2/3
def bank_tr2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.lower() not in vr1[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[users[mid]])
        return
    vr3[mid] = vr3[mid][vr1[mid].index(text.lower())]
    vr1[mid] = text
    users[mid] = 'main_bank_tr'
    sent = bot.send_message(mid, 'Напишите сумму перевода', reply_markup = markupCanc)
    bot.register_next_step_handler(sent, bank_tr3)

# Перевод 3/3
def bank_tr3(message): #сумма перевода
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.lower() == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text[0] == '-':
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])	
        return
    try:
        text = round(float(check_num(text)),2)
    except Exception:
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])	
        return
    vr2[mid] -= text
    vr3[mid] += text
    if vr2[mid] < 0:
        bot.send_message(mid, "У вас нет столько", reply_markup = MUP[users[mid]])	
        return
    conn = sqlite3.connect(user_db(kods[mid]))
    cur = conn.cursor()
    cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(vr2[mid],kods[mid],vr[mid]))
    cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(vr3[mid],kods[mid],vr1[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Выполнено", reply_markup = MUP[users[mid]])
	
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
            users[mid] = 'main_debt_group'
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("DELETE FROM groups WHERE name = '%s' AND login = '%s'"%(vr[mid],kods[mid]))
            conn.commit()
            cur.close()
            conn.close()
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удвление выполнено")
            bot.send_message(mid, "Вот меню:", reply_markup = MUP[users[mid]])
            
        if call.data == "gr_del_no":
            users[mid] = 'main_debt_group_opr'
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Вот меню:", reply_markup = MUP[users[mid]])
            
        if call.data == "gr_yes":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Будем добавлять еще долг уже существующим")
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            sent = bot.send_message(mid, 'Введите размер долга', reply_markup = markup1)
            bot.register_next_step_handler(sent, group5)
            
        if call.data == "gr_no":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Оставим у существующих все как есть")
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            sent = bot.send_message(mid, 'Введите размер долга', reply_markup = markup1)
            bot.register_next_step_handler(sent, group6)
            
        if call.data == "bank_del_yes":
            users[mid] = prev_step(users[mid])
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("DELETE FROM bank WHERE name = '%s' AND login = '%s'"%(vr[mid],kods[mid]))
            conn.commit()
            cur.close()
            conn.close()
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удвление выполнено")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
            
        if call.data == "bank_del_no":
            users[mid] = prev_step(users[mid])
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])

        if call.data == "bank_fin_del_yes":
            users[mid] = prev_step(users[mid])
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
            for row in cur:
                bal = row[0]
            if catg[kods[mid]] == 'spend':
                bal += vr3[mid]
                cur.execute("DELETE FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
            elif catg[kods[mid]] == 'fin':
                bal -= vr3[mid]
                if bal < 0:
                    vr.pop(mid)
                    vr1.pop(mid)
                    vr2.pop(mid)
                    tme.pop(mid)
                    bot.send_message(mid, "Удаление невозможно, так как баланс станет отрицательным", reply_markup = MUP[users[mid]])
                    cur.close()
                    conn.close()
                    return
                cur.execute("DELETE FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
            cur.execute("UPDATE bank SET bal = '%f' WHERE login = '%s' AND name = '%s'"%(bal,kods[mid],spend[mid]))
            conn.commit()
            cur.close()
            conn.close()
            vr.pop(mid)
            vr1.pop(mid)
            vr2.pop(mid)
            tme.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удвление выполнено, состояние счета изменено")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        
        if call.data == "bank_fin_del_no":
            users[mid] = prev_step(users[mid])
            vr.pop(mid)
            vr1.pop(mid)
            vr2.pop(mid)
            tme.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])

        if call.data == "bank_fin_chngcat":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Выберите новую категорию")
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            if catg[kods[mid]] == 'spend':
                cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            elif catg[kods[mid]] == 'fin':
                cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            vr1[mid] = []
            for row in cur:
                markup1.row(row[0])
                vr1[mid].append(row[0])
            cur.close()
            conn.close()
            sent = bot.send_message(mid, "Список категорий ниже", reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_edit4)

        if call.data == "bank_fin_chngsum":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Не забудьте, что у вас изменится и счет")
            sent = bot.send_message(mid, "Напишите новую сумму", reply_markup = markupCanc)
            bot.register_next_step_handler(sent, bank_fin_edit5)

        if call.data == "alice_add_yes":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо")
            sent = bot.send_message(mid, "Напишите фразу-вопрос (без знаков препинания)", reply_markup = markupCanc)
            bot.register_next_step_handler(sent, alice_add1)

        if call.data == "alice_add_no":
            users[mid] = prev_step(users[mid])
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Ладно. Чтобы добавить фразы напишите еще раз /alice")

        if call.data == "alice_auth_yes":
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("DELETE FROM alice WHERE id = '%s'"%(vr[mid]))
            conn.commit()
            cur.close()
            conn.close()
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("INSERT INTO zalog_alice (id,login) VALUES ('%s','%s')"%(vr[mid],kods[mid]))
            conn.commit()
            cur.close()
            conn.close()
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Добавление выполнено выполнено")
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])

        if call.data == "alice_auth_no":
            conn = sqlite3.connect(user_db(kods[mid]))
            cur = conn.cursor()
            cur.execute("DELETE FROM alice WHERE id = '%s'"%(vr[mid]))
            conn.commit()
            cur.close()
            conn.close()
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удаление выполнено")
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])

        if call.data == "alice_deauth_yes":
            
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("DELETE FROM zalog_alice WHERE login = '%s'"%(kods[mid]))
            conn.commit()
            cur.close()
            conn.close()
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удаление сессий выполнено")
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])

        if call.data == "alice_deauth_no":
            users[mid] = prev_step(users[mid])
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, сессии работают")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])

        if call.data == "set":
            return
            users[mid] = 'main_account_set'
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, сессии работают")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])


#WEBHOOK_START

# Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
bot.remove_webhook()

 # Ставим заново вебхук
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))

# Указываем настройки сервера CherryPy
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})

 # Собственно, запуск!
cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})

#WEBHOOK_FINISH

#bot.polling(none_stop=True)
