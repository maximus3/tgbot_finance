# -*- coding: utf-8 -*-
import telebot
import sqlite3
from telebot import types
import time
import cherrypy
import os

import logging

# Мои файлы
from config import *
from func import *
from diag import *
from webhook import *
from get_data import *
from metrik import *
from watch import *

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO, filename = directory + 'finbot.log')

ERROR = 3
logins = loadlogins() #все существующие в системе логины
users = dict() #шаги пользователей
kods = dict() #id + логины залогинившихся пользователей
kods, users = loadkods()
vr = dict() #временные данные
vr1 = dict() #^2
vr2 = dict()
vr3 = dict()
event = dict() # флажок где обрабатывать сообщение
spend = dict() #счет в расходах и доходах
tme = dict() #время для записи расходов/доходов
catg = dict() #доходы/расходы
inline_mes = dict() # Инлайн сообщение, которое нужно изменить
dialogs = dict() # Токен яндекс.диалогов, который надо авторизовать после регистрации

NEW_TABLES = False # Нужно ли проверять наличие всех таблиц у каждого пользователя
# ADD_NOTIF = False # Добавление каждому участнику уведомления в 22:00


if NEW_TABLES:
    logging.info('Checking tables')
    create_tables(logins)
    logging.info('Checked')

    # if ADD_NOTIF:
    #     conn = sqlite3.connect(notif_db)
    #     cur = conn.cursor()
    #     cur.execute("SELECT login FROM notif")
    #     rows = cur.fetchall()
    #     cur.close()
    #     conn.close()
    #     not_logins = []
    #     for row in rows:
    #         not_logins.append(row[0])
    #     conn = sqlite3.connect(notif_db)
    #     cur = conn.cursor()
    #     for login in logins:
    #         if login not in not_logins:
    #             cur.execute("INSERT INTO notif (login,time) VALUES ('%s','%d')"%(login, 22))
    #     conn.commit()
    #     cur.close()
    #     conn.close()
        

for elem in admin_ids:
    if elem not in tester_ids:
        tester_ids.append(elem)

# WEBHOOK_START

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

# WEBHOOK_FINISH

bot = telebot.TeleBot(TOKEN)

# Проверка на наличие ошибок
# Вход: -
# Выход: True если ошибки есть, False иначе
def error_check(message):
    mid = message.chat.id
    
    login = kods.get(mid)
    if login != None:
        if message.chat.username:
            username = message.chat.username
            logging.info('error_check [%s]: Got username %s', login, username)
        else:
            username = ''
            logging.info('error_check [%s]: No username', login)
        text = message.text

        logging.info('error_check [%s]: Connecting to user database', login)
        conn = sqlite3.connect(user_db(login))
        logging.info('error_check [%s]: Connected', login)
        cur = conn.cursor()
        # cur.execute("DELETE FROM last_mes WHERE login = ?", [(login)])
        try:
            logging.info('error_check [%s]: Adding COLUMN username in TABLE last_mes', login)
            cur.execute("ALTER TABLE last_mes ADD COLUMN username TEXT")
            logging.info('error_check [%s]: Added', login)
        except sqlite3.OperationalError:
            logging.info('error_check [%s]: Column already exist', login)
        except Exception as e:
            logging.error(str(e))
        try:
            logging.info('error_check [%s]: Adding COLUMN text in TABLE last_mes', login)
            cur.execute("ALTER TABLE last_mes ADD COLUMN text TEXT")
            logging.info('error_check [%s]: Added', login)
        except sqlite3.OperationalError:
            logging.info('error_check [%s]: Column already exist', login)
        except Exception as e:
            logging.error(str(e))
        logging.info('error_check [%s]: Inserting values in last_mes', login)
        cur.execute("INSERT INTO last_mes (login,time, username, text) VALUES (?, ?, ?, ?)", [(login), (str(time.asctime())), (username), (text)])
        logging.info('error_check [%s]: Inserted', login)
        conn.commit()
        cur.close()
        conn.close()
        
    if 'errors' in users[mid]:
        return False
    if ERROR == 3 and mid in tester_ids:
        bot.send_message(mid, 'Бот работает в режиме "Только тест"')
        return False
    if ERROR != 0:
        if 'mainUS' in users[mid]:
            users[mid] = 'mainUS'
        else:
            users[mid] = 'main'
        bot.send_message(mid, 'Проводятся технические работы. Попробуйте позже', reply_markup = MUP[users[mid]])
        return True
    return False

# Описание добавления 
# Вход: Сообщение
# Выход: -
@bot.message_handler(commands=['help'])
def add_desc(message):
    mid = message.chat.id
    step = users.get(mid)
    text = """
- Добавление расходов и доходов одной строкой:
Наипшите описание (не обязательно), сумму (через "+", если это доход) и первые несколько букв категории.
Далее вы можете выбрать категорию, а также поменять счет.
Теперь вам остается нажать кнопку "Добавить" и все сделано!
Примеры:
300 пр
Далее выбираете категорию "продукты" и нажимаете кнопку добавить.
+10000 зар
Далее выбираете категорию "зарплата" и нажимаете кнопку добавить.

- Шаблоны:
Шаблоны используются при добавлении расходов и доходов одной строкой.
Сначала вы выбираете какой шаблон это будет (расхода или дохада).
Далее вы выбираете категорию, а затем пишите шаблон в формате *название* *сумма*
Сумму можно не указывать.
Примеры:
Пусть у вас есть шаблон "премия 5000" в категории "зарплата".
Чтобы добавить этот доход, напишите команду "премия" (или "пре"), а затем нажмите кнопку добавить.
Если сумма другая, например, 10000, то напишите команду "премия 10000" (или "пре 10000"). Тогда будет добавлен доход "премия" с суммой в 10000р.

- Лимиты:
Вы можете установить лимиты на расходы на определенные категории (или на все сразу).
Данная функция поможет вам контролировать свои расходы.
Вы можете следить, сколько денег можно еще потратить, а также каждый день в полночь бот будет присылать вам отчет о каждом лимите.

P.S. Возможны баги, поэтому если вы их вдруг обнаружите, то обязательно напишите об этом в @m3prod
"""
    try:
        bot.send_message(mid, text, reply_markup = MUP[step])
    except Exception:
        bot.send_message(mid, text)

# Добавление тестеров
# Вход: сообщение (/add_tester + кодовая фраза + имя)
# Выход: -
@bot.message_handler(commands=['add_tester'])
def add_tester(message):
    mid = message.chat.id
    text = message.text.split()
    logging.info('add_tester: Trying to add %s', str(mid))
    if len(text) < 3:
        logging.info('add_tester: Not enough parametrs')
        return
    text.pop(0)
    code = text.pop(0)
    if code != testers_code:
        logging.info(u'add_tester: Wrong tester code (%s)', code)
        return
    text = ' '.join(text)
    keybGR = types.InlineKeyboardMarkup()
    cbtn = types.InlineKeyboardButton(text="Добавить", callback_data="tester_add_"+str(mid))
    keybGR.add(cbtn)
    
    for aid in admin_ids:
        try:
            logging.info('add_tester: Sending message to admin %s', str(aid))
            sent = bot.send_message(aid, 'Добавление пользователя ' + text + '\nID: ' + str(mid), reply_markup = keybGR)
            logging.info('add_tester: Sent')
            inline_mes[aid] = sent.message_id
        except Exception as e:
            logging.info('add_tester: Send error: ', str(e))
    bot.send_message(mid, "Запрос отправлен")

# Удаление тестеров
# Вход: сообщение (/delete_tester)
# Выход: -
@bot.message_handler(commands=['delete_tester'])
def delete_tester(message):
    mid = message.chat.id

    if mid not in admin_ids:
        logging.info('delete_tester: Not admin')
        return

    if len(tester_ids) == len(admin_ids):
        logging.info('delete_tester: No testers')
        bot.send_message(mid, 'Тестеров нет')
        return

    logging.info('delete_tester: Creating markup')
    keybGR = types.InlineKeyboardMarkup()
    for tid in tester_ids:
        if tid in admin_ids:
            logging.info('delete_tester: %s in admin_ids', str(tid))
            continue
        cbtn = types.InlineKeyboardButton(text=str(tid), callback_data="tester_delete_"+str(tid))
        keybGR.add(cbtn)
    logging.info('delete_tester: Created')
    sent = bot.send_message(mid, 'Выберите пользователя, которого хотите удалить', reply_markup = keybGR)
    inline_mes[mid] = sent.message_id

# Количество пользователей в системе
# Вход: Сообщение
# Выход: Если это написал админ, то ему отправляется количество пользователей
@bot.message_handler(commands=['admin'])
def admin(message):
    mid = message.chat.id
    if mid in admin_ids:
        bot.send_message(mid, """
/admin - админ-панель
/last - список последних отправлений сообщений каждого пользователя
/null - обнуление event и step
/errors - остановка бота
/add_tester - добавление тестеров
/delete_tester - удаление тестеров
/gcheck - текущее состояниеs
""")
        bot.send_message(mid, 'Testers: ' + str(tester_ids) + '\nCode: ' + testers_code)
        bot.send_message(mid, 'Добро пожаловать! Всего пользователей: ' + str(len(logins)))

# Дата последнего сообщения пользователя
# Вход: Сообщение
# Выход: Если это написал админ, то ему отправляется дата последнего сообщения каждого пользователя
@bot.message_handler(commands=['last'])
def admin_last(message):
    mid = message.chat.id
    if mid in admin_ids:
        stroka = 'Добро пожаловать! Всего пользователей: ' + str(len(logins)) + '\n'
        last = []
        for num, login in enumerate(logins):

            kod = False
            
            for ad_id in admin_ids:
                ad_login = kods.get(ad_id)
                if ad_login != None and ad_login == login:
                    kod = True
                    break

            if kod:
                continue
                
            try:
                conn = sqlite3.connect(user_db(login))
                cur = conn.cursor()
                cur.execute("SELECT time, username, text FROM last_mes")
                rows = cur.fetchall()
                cur.close()
                conn.close()
                rows.reverse()
                for i, row in enumerate(rows):
                    tm = row[0].split()
                    tm = [login, int(tm[4]), month[tm[1]], int(tm[2]), tm[3], row[1], row[2]]
                    last.append(tm)
                    if i > 9:
                        break
            except Exception as e:
                if 'no such column' not in str(e):
                    logging.error(str(e))
        last.sort() # login, year, month, day, time, username, text
        last_logins = []
        for i, elem in enumerate(last):
            login, year, mon, day, time, username, text = elem
            if login in last_logins:
                stroka += month[mon] + ' ' + str(day) + ' ' + str(time) + ' ' + str(year) + '\n- ' + text + '\n'
            else:
                last_logins.append(login)
                stroka += '\n' + login + ' [' + str(username) + ']:\n' + month[mon] + ' ' + str(day) + ' ' + str(time) + ' ' + str(year) + '\n- ' + str(text) + '\n'
        if stroka[0] == '\n':
            stroka = stroka[1:]
        while len(stroka) > 4000:
            bot.send_message(mid, stroka[:4000])
            stroka = stroka[4000:]
        bot.send_message(mid, stroka)

# Обнуление
# Вход: сообщение
# Выход: -
@bot.message_handler(commands=['null'])
def null(message):
    mid = message.chat.id
    if mid in tester_ids:
        event[mid] = 0
        if 'mainUS' in users[mid]:
            users[mid] = 'mainUS'
        else:
            users[mid] = 'main'
        bot.send_message(mid, 'Выполнено')

# Подключение к Алисе от Яндекса
# Вход: Сообщение
# Выход: -
@bot.message_handler(commands=['alice'])
def alice(message):
    mid = message.chat.id

    if users.get(mid) == None:
        users[mid] = 'mainUS'

    step = users[mid]

    if inline_mes.get(mid) != None:
        bot.edit_message_text(chat_id = mid, message_id = inline_mes[mid], text = "Действие отменено")
        inline_mes.pop(mid)

    if error_check(message):
        return
    
    # Метрика
    send_metrik("telegram", str(mid), '/alice', str(step), False)

    if step == 'mainUS':
        bot.send_message(mid, 'Сначала вам нужно авторизироваться')
        return

    if event[mid] != 0:
        return

    users[mid] = 'main_account_alice'
    step = users[mid]

    login = kods[mid]
    
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT phrase,answer FROM alice WHERE login = '%s'"%(login))
    for row in cur:
        phrase = row[0]
        answer = row[1]
        bot.send_message(mid, 'Ваша фраза: ' + phrase + '\nВаш ответ: ' + answer, reply_markup = MUP[step])
        cur.close()
        conn.close()
        return
    users[mid] = prev_step(users[mid])
    step = users[mid]
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="alice_add_yes")
    cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="alice_add_no")
    keybGR.add(cbtn1, cbtn2)
    sent = bot.send_message(mid, 'У вас не задана фраза и ответ. Хотите добавить ее сейчас?', reply_markup = keybGR)
    inline_mes[mid] = sent.message_id
    event[mid] = 0

# Добавление новой пары вопрос-ответ 1/2
# Вход: Сообщение
# Выход: -
def alice_add1(message):
    mid = message.chat.id
    text = (message.text).lower()
    step = users[mid]
    login = kods[mid]
    
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[step])
        return
    if len(text) > 64:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Длина фразы не должна превышать 64 символа', reply_markup = MUP[step])
        return
    if check_text(text, 'rus'):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[step])
        return
    if phrase_in(text):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'К сожалению, данная фраза занята', reply_markup = MUP[step])
        return
    vr[mid] = text
    sent = bot.send_message(mid, "Напишите фразу-ответ (без знаков препинания)", reply_markup = markupCanc)
    event[mid] = 1
    bot.register_next_step_handler(sent, alice_add2)

# Добавление новой пары вопрос-ответ 2/2
# Вход: Сообщение
# Выход: -
def alice_add2(message):
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[step])
        return
    if len(text) > 64:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Длина фразы не должна превышать 64 символа', reply_markup = MUP[step])
        return
    if check_text(text, 'rus'):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[step])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("INSERT INTO alice (login,phrase,answer) VALUES ('%s','%s','%s')"%(login,vr[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    users[mid] += '_alice'
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, 'Успешно добавлено!\nВаша фраза: ' + vr[mid] + '\nВаш ответ: ' + text, reply_markup = MUP[step])

# Смена фразы-вопроса
# Вход: Сообщение
# Выход: -
def alice_change1(message):
    mid = message.chat.id
    text = (message.text).lower()
    step = users[mid]
    login = kods[mid]
    
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[step])
        return
    if len(text) > 64:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Длина фразы не должна превышать 64 символа', reply_markup = MUP[step])
        return
    if check_text(text, 'rus'):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[step])
        return
    if phrase_in(text):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'К сожалению, данная фраза занята', reply_markup = MUP[step])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE alice SET phrase = '%s' WHERE login = '%s'"%(text,login))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, 'Успешно изменено!\nВаша новая фраза: ' + text, reply_markup = MUP[step])

# Смена фразы-ответа
# Вход: Сообщение
# Выход: -
def alice_change2(message):
    mid = message.chat.id
    text = (message.text).lower()
    step = users[mid]
    login = kods[mid]
    
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите дествие', reply_markup = MUP[step])
        return
    if len(text) > 64:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Длина фразы не должна превышать 64 символа', reply_markup = MUP[step])
        return
    if check_text(text, 'rus'):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Используйте только русские буквы (пишите существующие слова) и пробел', reply_markup = MUP[step])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE alice SET answer = '%s' WHERE login = '%s'"%(text,login))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, 'Успешно изменено!\nВаш новый ответ: ' + text, reply_markup = MUP[step])

# Аутентификация диалога
# Вход: Сообщение
# Выход: -
def alice_auth(message):
    mid = message.chat.id
    text = (message.text).lower()
    step = users[mid]
    login = kods[mid]
    event[mid] = 0
    
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT id,phrase FROM alice")
    for row in cur:
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="alice_auth_yes")
        cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="alice_auth_no")
        keybGR.add(cbtn1, cbtn2)
        vr[mid] = row[0]
        cur.close()
        conn.close()
        sent = bot.send_message(mid, row[1] + '\nАвторизировать данную сессию?', reply_markup = keybGR)
        inline_mes[mid] = sent.message_id
        return
    cur.close()
    conn.close()
    bot.send_message(mid, 'Нет диалогов для авторизации', reply_markup = MUP[step])

# Текущий шаг пользователя
# Вход: Сообщение
# Выход: Сообщение пользователю с его текущим шагом
@bot.message_handler(commands=['gcheck'])
def gcheck(message):
    mid = message.chat.id
    bot.send_message(mid, users[mid] + '\n' + str(event[mid]))

# Ошибки 1/4
# Вход: Сообщение
# Выход: -
@bot.message_handler(commands=['errors'])
def errors1(message):
    mid = message.chat.id
    if mid not in admin_ids:
        return
    users[mid] += '_errors'
    sent = bot.send_message(mid, 'Введите кодовое слово:')
    event[mid] = 1
    bot.register_next_step_handler(sent, errors2)

# Ошибки 2/4
# Вход: Сообщение
# Выход: -
def errors2(message):
    mid = message.chat.id
    text = message.text
    step = users[mid]
    
    if text == code and ERROR != 0:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('**да**')
        markup1.row('**нет**')
        markup1.row('**admin_mode**')
        LOGS = ''
        sent = bot.send_message(mid, ERRORS_DESC + 'ERROR: ' + str(ERROR) + '\n\nЗапустить бота?', reply_markup = markup1)
        bot.register_next_step_handler(sent, errors3)
    elif text == code and ERROR == 0:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('**да**')
        markup1.row('**нет**')
        markup1.row('**admin_mode**')
        sent = bot.send_message(mid, 'Остановить бота?', reply_markup = markup1)
        bot.register_next_step_handler(sent, errors4)
    else:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Кодовое слово не верно')
        return

# Ошибки 3/4
# Вход: Сообщение
# Выход: -
def errors3(message):
    global ERROR
    mid = message.chat.id
    text = message.text.lower()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    
    if text == '**да**':
        ERROR = 0
        text = 'Бот запущен'
    elif text == '**admin_mode**':
        ERROR = 3
        text = 'Бот работает в режиме "Только для админа"'
    else:
        text = 'Бот не запущен'
    try:
        bot.send_message(mid, text, reply_markup = MUP[step])
    except Exception:
        bot.send_message(mid, text)

# Ошибки 4/4
# Вход: Сообщение
# Выход: -
def errors4(message):
    global ERROR
    mid = message.chat.id
    text = message.text.lower()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    
    if text == '**да**':
        ERROR = 1
        text = 'Бот остановлен'
    elif text == '**admin_mode**':
        ERROR = 3
        text = 'Бот работает в режиме "Только для админа"'
    else:
        text = 'Бот работает'
    try:
        bot.send_message(mid, text, reply_markup = MUP[step])
    except Exception:
        bot.send_message(mid, text)

# Приветствие
# Вход: Сообщение
# Выход: -
@bot.message_handler(commands=['start'])
def start(message):
    mid = message.chat.id
    login = kods.get(mid)

    if event.get(mid) == None:
        event[mid] = 0
    
    if users.get(mid) == None:
        users[mid] = 'mainUS'
    elif event[mid] == 0:
        users[mid] = 'main'

    step = users[mid]

    text = message.text.split()
    if len(text) > 1:
        text = text[1]
        if len(text) == 64:
            while text[len(text) -1] == 'q':
                text = text[:-1]
            if kods.get(mid) == None:
                dialogs[mid] = text
            else:
                bot.send_message(mid, alice_after_auth(text, login))
    
    try:
        bot.send_message(mid , desc + '\nВерсия бота: ' + str(version) + '\n\nСписок изменений:' + chng, reply_markup = MUP[step])
    except Exception:
        bot.send_message(mid , desc + '\nВерсия бота: ' + str(version) + '\n\nСписок изменений:' + chng)

# Главная функция, обработка всего приходящего текста
# Вход: Сообщение
# Выход: -
@bot.message_handler(content_types=['text'])
def main(message):
    mid = message.chat.id
    text = message.text.lower()

    if event.get(mid) == None:
        event[mid] = 0

    ev = event[mid]
    
    if users.get(mid) == None:
        users[mid] = 'mainUS'
    step = users[mid]

    login = kods.get(mid)

    if inline_mes.get(mid) != None:
        bot.edit_message_text(chat_id = mid, message_id = inline_mes[mid], text = "Действие отменено")
        inline_mes.pop(mid)

    if spend.get(mid) == None:
        spend[mid] = 'все'

    # Метрика
    send_metrik("telegram", str(mid), text, str(step), False)

    if error_check(message):
        return

    if ev != 0:
        return

    try:
        vr.pop(mid)
    except Exception:
        pass
    try:
        vr1.pop(mid)
    except Exception:
        pass
    try:
        vr2.pop(mid)
    except Exception:
        pass
    try:
        vr3.pop(mid)
    except Exception:
        pass

    # Пользователь не авторизован
    if step == 'mainUS':

        # Регистрация нового пользователя
        if text == '**регистрация**':
            sent = bot.send_message(mid, 'Пожалуйста, введите новый логин и пароль через пробел или в два разных сообщения:')
            users[mid] = 'mainUS_reg'
            event[mid] = 1
            bot.register_next_step_handler(sent, reg1)

        # Вход
        elif text == '**вход**':
            sent = bot.send_message(mid, 'Пожалуйста, введите свой логин и пароль через пробел или в два разных сообщения:')
            users[mid] = 'mainUS_login'
            event[mid] = 1
            bot.register_next_step_handler(sent, login1)

        # Информация
        elif text == '**о боте**':
            start(message)

        return

    # Добавление операции одной командой (проверка)
    if text[:2] != '**' and text[:1] != '/':
        short_add(mid, text)

    # Главное меню
    if step == 'main':

        # Информация
        if text == '**о боте**':
            start(message)

        # Меню Долги
        elif text == '**мои долги**':
            users[mid] += '_debt'
            step = users[mid]
            bot.send_message(mid, watch_debts(login), reply_markup = MUP[step])

        # Меню Банк
        elif text == '**мой кошелек**' or text == '**мой кошелёк**':
            users[mid] += '_bank'
            watch_bank(message)

        # Меню Аккаунт
        elif text == '**аккаунт**':
            users[mid] += '_account'
            step = users[mid]
            bot.send_message(mid, 'Что вы хотите сделать?', reply_markup = MUP[step])

    # Меню Аккаунт
    elif step == 'main_account':

        # Удаление аккаунта
        if text == '**удалить аккаунт**':
            keybGR = types.InlineKeyboardMarkup()
            cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="delete_yes")
            cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="delete_no")
            keybGR.add(cbtn1, cbtn2)
            sent = bot.send_message(mid, 'Вы уверены, что хотите удалить все данные? Отмена данной операции невозможна!', reply_markup = keybGR)
            inline_mes[mid] = sent.message_id

        # Сброс данных
        if text == '**сброс данных**':
            users[mid] += '_reset'
            step = users[mid]
            event[mid] = 1
            sent = bot.send_message(mid, 'Сброс данных предполагает полное удаление всех ваших данных, включая счета, операции, долги. Вы можете оставить только категории. Оставить?', reply_markup = MUP[step])
            bot.register_next_step_handler(sent, reset)

        # Смена пароля
        elif text == '**смена пароля**':
            sent = bot.send_message(mid, 'Введите старый пароль')
            users[mid] += '_changepass'
            event[mid] = 1
            bot.register_next_step_handler(sent, chngpass1)

        # Выход из аккаунта
        elif text == '**выход**':
            kods.pop(mid)
            del_kod(mid)
            users[mid] = 'mainUS'
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, 'Выход выполнен', reply_markup = MUP[step])

        # Предыдущее меню
        elif text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Подключение к Яндекс.Алисе
        elif text == '**алиса**':
            alice(message)

    # Меню Аккаунт - Алиса
    elif step == 'main_account_alice':

         # Смена фразы-вопроса
        if text == '**поменять вопрос**':
            users[mid] += '_change'
            sent = bot.send_message(mid, "Напишите новую фразу-вопрос", reply_markup = markupCanc)
            event[mid] = 1
            bot.register_next_step_handler(sent, alice_change1)

        # Смена фразы-ответа
        elif text == '**поменять ответ**':
            users[mid] += '_change'
            step = users[mid]
            sent = bot.send_message(mid, "Напишите новую фразу-ответ", reply_markup = markupCanc)
            event[mid] = 1
            bot.register_next_step_handler(sent, alice_change2)

        # Авторизация диалога
        elif text == '**авторизация диалога**':
            alice_auth(message)

        # Просмотр активных сессий
        elif text == '**активные сессии**':
            kol = 0
            stroka = "Количество активных сессий: "
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT id FROM zalog_alice WHERE login = '%s'"%(login))
            for row in cur:
                kol += 1
            cur.close()
            conn.close()
            
            if kol == 0:
                stroka = "Нет активных сессий"
                bot.send_message(mid, stroka, reply_markup = MUP[step])
                return

            stroka += str(kol) + "\nОтключить все активные сессии?"
            keybGR = types.InlineKeyboardMarkup()
            cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="alice_deauth_yes")
            cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="alice_deauth_no")
            keybGR.add(cbtn1, cbtn2)
            sent = bot.send_message(mid, stroka, reply_markup = keybGR)
            inline_mes[mid] = sent.message_id

        # Помощь
        elif text == '**помощь**':
            bot.send_message(mid, """
1) Вы говорите Алисе кодовую фразу-вопрос. Она должна понять вас и сказать вашу фразу-ответ.
2) Вы должны сказать Алисе любую кодовую фразу, которую она отправит сюда.
3) Нажмите на кнопку "Авторизация диалога". Бот пришлет вам кодовую фразу.
4) Если фраза совпадает с той, что вы сказали Алисе, то вам нужно нажать кнопку "Да" и все заработает!
5) Теперь вы можете пользоваться ботом через Алису!
Удачи!
            """, reply_markup = MUP[step])

        # Предыдущее меню
        elif text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

    # Меню Долги
    elif step == 'main_debt':

        # Добавление долга
        if text == '**добавить долг**':
            vr[mid] = []
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            banks, kol, osum = get_banks(login)
            for elem in banks:
                markup1.row(elem[0])
                vr[mid].append(elem[0].lower())
            sent = bot.send_message(mid, 'Выберите счет, с которого вы даете долг', reply_markup = markup1)
            event[mid] = 1
            users[mid] += '_add'
            bot.register_next_step_handler(sent, addcredit1)

        # Просмотр долгов
        elif text == '**мои долги**':
            bot.send_message(mid, watch_debts(login), reply_markup = MUP[step])

        # Редактирование долгов
        elif text == '**редактировать**':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            debts, kol, osum = get_debts(login)
            for elem in debts:
                markup1.row(elem[0])
            sent = bot.send_message(mid, 'Введите фамилию и имя должника, у которого хотите изменить долг', reply_markup = markup1)
            event[mid] = 1
            users[mid] += '_edit'
            bot.register_next_step_handler(sent, edit1)

        # Предыдущее меню
        elif text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

    # Меню Банк
    elif step == 'main_bank':

        # Предыдущее меню
        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Просмотр баланса счетов
        elif text == '**баланс**':
            watch_bank(message)

        # Меню Доходы
        elif text == '**доходы**':
            catg[login] = 'fin'
            bank_fin(mid)

        # Меню расходы
        elif text == '**расходы**':
            catg[login] = 'spend'
            bank_fin(mid)

        # Меню настройки
        elif text == '**настройки**':
            users[mid] += '_settings'
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Перевод с одного счета на другой
        elif text == '**перевод**':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            vr[mid] = []
            vr1[mid] = []
            vr2[mid] = []
            vr3[mid] = []
            banks, kol, osum = get_banks(login)
            if kol < 2:
                bot.send_message(mid, 'У вас недостаточно счетов', reply_markup = MUP[step])
                return
            for elem in banks:
                vr1[mid].append(elem[0].lower())
                vr3[mid].append(elem[1])
                if elem[1] > 0:		
                    markup1.row(elem[0])
                    vr[mid].append(elem[0].lower())
                    vr2[mid].append(elem[1])
            
            users[mid] += '_tr'
            event[mid] = 1
            sent = bot.send_message(mid, 'Выберите счет, с которого хотите перевести средства (показаны счета с положительным балансом)', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_tr1)

        # Лимиты
        elif text == '**лимиты**':
            if mid not in tester_ids:
                bot.send_message(mid, 'Данная функция находится в разработке')
                return
            bot.send_message(mid, 'Данная функция находится в разработке')
            users[mid] += '_limits'
            step = users[mid]
            bot.send_message(mid, watch_limits(login), reply_markup = MUP[step])

    # Меню Банк - Лимиты
    elif step == 'main_bank_limits':
        
        # Предыдущее меню
        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Просмотр лимитов
        elif text == '**мои лимиты**':
            bot.send_message(mid, watch_limits(login), reply_markup = MUP[step])

        # Добавление лимита
        elif text == '**добавить лимит**':

            logging.info('Getting categs...')
            categs, kol = get_categs(login, 'spend')
            logging.info('Got')

            if kol == 0:
                bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[step])
                return

            vr[mid] = []
            vr[mid].append([])
            logging.info('Creating markup')
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            markup1.row('*все категории*')
            vr[mid][0].append('#all')
            for elem in categs:
                vr[mid][0].append(elem)
                markup1.row(elem)
            logging.info('Created')

            users[mid] += '_add'
            sent = bot.send_message(mid, "Выберите категорию лимита", reply_markup = markup1)
            event[mid] = 1
            bot.register_next_step_handler(sent, bank_limits_add1)
                

        # Удаление лимита
        elif text == '**удалить лимит**':

            logging.info('main_bank_limits [%s]: Getting limits', login)
            limits, kol = get_limits(login)
            logging.info('main_bank_limits [%s]: Got limits', login)

            if kol == 0:
                logging.info('main_bank_limits [%s]: No limits', login)
                bot.send_message(mid, "На данный момент у вас нет установленных лимитов", reply_markup = MUP[step])
                return            

            vr[mid] = []
            logging.info('main_bank_limits [%s]: Creating markup', login)
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            for elem in limits:
                categ = elem[0]
                if categ == '#all':
                    categ = '*все категории*'
                vr[mid].append([elem[0], str(elem[1]), day_end(elem[1], elem[2])])
                markup1.row(categ + ', ' + str(elem[1]) + ' ' + day_end(elem[1], elem[2]))

            logging.info('main_bank_limits [%s]: Created markup', login)

            sent = bot.send_message(mid, 'Выберите лимит, который вы хотите удалить (показана его категория и продолжительность)', reply_markup = markup1)
            event[mid] = 1
            users[mid] += '_del'
            bot.register_next_step_handler(sent, bank_limits_del)

    # Меню Банк - Настройки
    elif step == 'main_bank_settings':
        
        # Предыдущее меню
        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Создание нового счета
        elif text == '**новый счет**':
            new_bank(mid)

        # Удаление счета
        elif text == '**удалить счет**':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            banks, kol, osum = get_banks(login)
            vr[mid] = []
            for elem in banks:
                markup1.row(elem[0])
                vr[mid].append(elem[0].lower())
            if kol == 0:
                keybSET = types.InlineKeyboardMarkup()
                cbtn = types.InlineKeyboardButton(text="Добавить счет", callback_data="bank_add")
                keybSET.add(cbtn)
                sent = bot.send_message(mid, 'Для начала работы вам нужно добавить счет (например, наличка). Вы можете сделать это, нажав кнопку ниже', reply_markup = keybSET)
                inline_mes[mid] = sent.message_id
                return
            
            users[mid] += '_del'
            sent = bot.send_message(mid, 'Выберите счет, который хотите удалить', reply_markup = markup1)
            event[mid] = 1
            bot.register_next_step_handler(sent, bank_del)

        # Меню категории расходов
        elif text == '**категории расходов**':
            users[mid] += '_cat'
            step = users[mid]
            catg[login] = 'spend'
            bot.send_message(mid, watch_cat(login, catg[login]), reply_markup = MUP[step])

        # Меню категории
        elif text == '**категории доходов**':
            users[mid] += '_cat'
            step = users[mid]
            catg[login] = 'fin'
            bot.send_message(mid, watch_cat(login, catg[login]), reply_markup = MUP[step])

        # Настройки уведомлений
        elif text == '**уведомления**':
            users[mid] += '_notif'
            step = users[mid]
            bot.send_message(mid, watch_notif(login), reply_markup = MUP[step])

        # Шаблоны
        elif text == '**шаблоны**':
            users[mid] += '_templates'
            step = users[mid]
            bot.send_message(mid, watch_templates(login), reply_markup = MUP[step])

    # Меню Банк - Настройки - Шаблоны
    elif step == 'main_bank_settings_templates':

        # Предыдущее меню
        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Просмотр шаблонов
        elif text == '**мои шаблоны**':
            bot.send_message(mid, watch_templates(login), reply_markup = MUP[step])

        # Добавление шаблона
        elif text == '**добавить шаблон**':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            markup1.row('**Расход**')
            markup1.row('**Доход**')

            sent = bot.send_message(mid, 'Это шаблон расхода или дохода?', reply_markup = markup1)
            event[mid] = 1
            users[mid] += '_add'
            bot.register_next_step_handler(sent, bank_templates_add1)

        # Удаление шаблона
        elif text == '**удалить шаблон**':
            
            templates, kol = get_templates(login)

            if kol == 0:
                bot.send_message(mid, "На данный момент у вас нет шаблонов", reply_markup = MUP[step])
                return

            vr[mid] = []
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            for elem in templates:
                vr[mid].append(elem[0])
                markup1.row(elem[0])

            sent = bot.send_message(mid, 'Выберите шаблон, который вы хотите удалить', reply_markup = markup1)
            event[mid] = 1
            users[mid] += '_del'
            bot.register_next_step_handler(sent, bank_templates_del)

    # Меню Банк - Настройки - Уведомления
    elif step == 'main_bank_settings_notif':

        # Предыдущее меню
        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Просмотр уведомлений
        elif text == '**мои уведомления**':
            bot.send_message(mid, watch_notif(login), reply_markup = MUP[step])

        # Добавление уведомлений
        elif text == '**добавить уведомление**':
            
            vr[mid] = []
            for i in range(24):
                vr[mid].append(str(i))
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            
            conn = sqlite3.connect(notif_db)
            cur = conn.cursor()
            cur.execute("SELECT time FROM notif WHERE login = '%s'"%(login))
            for row in cur:
                vr[mid].pop(vr[mid].index(str(row[0])))
            cur.close()
            conn.close()
            kol = 0
            for elem in vr[mid]:
                markup1.row(str(elem))
                kol += 1

            if kol == 0:
                bot.send_message(mid, "У вас уже установленно максимальное количество уведомлений", reply_markup = MUP[step])
                return

            sent = bot.send_message(mid, 'Выберите время уведомления', reply_markup = markup1)
            event[mid] = 1
            users[mid] += '_add'
            bot.register_next_step_handler(sent, bank_notif_add)

        # Удаление уведомлений
        elif text == '**убрать уведомление**':
            
            vr[mid] = []
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            
            conn = sqlite3.connect(notif_db)
            cur = conn.cursor()
            cur.execute("SELECT time FROM notif WHERE login = '%s'"%(login))
            for row in cur:
                vr[mid].append(row[0])
                kol += 1
            cur.close()
            conn.close()

            vr[mid].sort()
            for i, elem in enumerate(vr[mid]):
                markup1.row(str(elem))
                vr[mid][i] = str(elem)
            if kol == 0:
                bot.send_message(mid, "У вас нет уведомлений", reply_markup = MUP[step])
                return

            sent = bot.send_message(mid, 'Выберите время уведомления, которое вы хотите убрать', reply_markup = markup1)
            event[mid] = 1
            users[mid] += '_del'
            bot.register_next_step_handler(sent, bank_notif_del)

    # Меню Банк - Расходы или Банк - Доходы
    elif step == 'main_bank_spend' or step == 'main_bank_fin':

        # Предыдущее меню
        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
            
        # Добавление расхода/дохода
        elif text == '**новый расход**' or text == '**новый доход**':
            if spend[mid] == 'все':
                users[mid] += '_add'
                markup1 = types.ReplyKeyboardMarkup()
                markup1.row('**Отмена**')
                vr[mid] = []
                banks, kol, osum = get_banks(login)
                for elem in banks:
                    markup1.row(elem[0])
                    vr[mid].append(elem[0])
                vr1[mid] = 'new'
                sent = bot.send_message(mid, 'Для начала выберите счет для добавления позиции', reply_markup = markup1)
                event[mid] = 1
                bot.register_next_step_handler(sent, bank_fin_change)
                return

            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**отмена**')
            vr[mid] = []
            categs, kol = get_categs(login, catg[login])
            for elem in categs:
                markup1.row(elem)
                vr[mid].append(elem.lower())
            
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[step])
                return
            
            users[mid] += '_add'
            sent = bot.send_message(mid, "Выберите категорию\nТекущий счет: " + spend[mid], reply_markup = markup1)
            event[mid] = 1
            vr1[mid] = 'new_no'
            
            keybCH = types.InlineKeyboardMarkup()
            cbtn = types.InlineKeyboardButton(text="Поменять счет", callback_data="bank_change")
            keybCH.add(cbtn)
            sent_in = bot.send_message(mid, 'Вы можете сменить счет', reply_markup = keybCH)
            inline_mes[mid] = sent_in.message_id

            event[mid] = 1
            bot.register_next_step_handler(sent, bank_fin_add1)

        # Отчет по расходам/доходам
        elif text == '**отчет по расходам**' or text == '**отчет по доходам**':
            users[mid] += '_his'
            categs, kol = get_categs(login, catg[login])
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**все**')
            vr[mid] = []
            for elem in categs:
                markup1.row(elem)
                vr[mid].append(elem.lower())
            sent = bot.send_message(mid, 'Выберите категорию', reply_markup = markup1)

            if spend[mid] != 'все':
                keybCH = types.InlineKeyboardMarkup()
                cbtn = types.InlineKeyboardButton(text="Полный отчет", callback_data="bank_allspend")
                keybCH.add(cbtn)
                sent_in = bot.send_message(mid, 'Текущий счет: ' + spend[mid] + '\nВы можете посмотреть отчет сразу по всем счетам', reply_markup = keybCH)
                inline_mes[mid] = sent_in.message_id

            event[mid] = 1            
            bot.register_next_step_handler(sent, bank_fin_his1)

        # Смена счета
        elif text == '**поменять счет**':
            banks, kol, osum = get_banks(login)
            vr[mid] = []
            users[mid] += '_change'
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**все**')
            for elem in banks:
                markup1.row(elem[0])
                vr[mid].append(elem[0].lower())
            sent = bot.send_message(mid, 'Выберите другой счет', reply_markup = markup1)
            event[mid] = 1
            bot.register_next_step_handler(sent, bank_change)

        # Редактирование расхода/дохода
        elif text == '**редактировать расход**' or text == '**редактировать доход**':
            if spend[mid] == 'все':
                users[mid] += '_edit'
                markup1 = types.ReplyKeyboardMarkup()
                markup1.row('**Отмена**')
                vr[mid] = []
                banks, kol, osum = get_banks(login)
                for elem in banks:
                    markup1.row(elem[0])
                    vr[mid].append(elem[0])
                vr1[mid] = 'edit'
                sent = bot.send_message(mid, 'Для начала выберите счет для редактирования позиции', reply_markup = markup1)
                event[mid] = 1
                bot.register_next_step_handler(sent, bank_fin_change)
                return

            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**отмена**')
            vr[mid] = []
            categs, kol = get_categs(login, catg[login])
            for elem in categs:
                markup1.row(elem)
                vr[mid].append(elem.lower())
            
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[step])
                return
            
            users[mid] += '_edit'
            sent = bot.send_message(mid, "Выберите категорию\nТекущий счет: " + spend[mid], reply_markup = markup1)
            event[mid] = 1
            vr1[mid] = 'edit_no'
            
            keybCH = types.InlineKeyboardMarkup()
            cbtn = types.InlineKeyboardButton(text="Поменять счет", callback_data="bank_change")
            keybCH.add(cbtn)
            sent_in = bot.send_message(mid, 'Вы можете сменить счет', reply_markup = keybCH)
            inline_mes[mid] = sent_in.message_id

            event[mid] = 1
            bot.register_next_step_handler(sent, bank_fin_edit1) 

    # Меню Банк - Настройки - Категории
    elif step == 'main_bank_settings_cat':

        # Предыдущее меню
        if text == '**назад**':
            users[mid] = prev_step(users[mid])
            step = users[mid]
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])

        # Добавление новой категории
        elif text == '**добавить**':
            users[mid] += '_add'
            sent = bot.send_message(mid, 'Введите название новой категории', reply_markup = markupCanc)
            event[mid] = 1
            bot.register_next_step_handler(sent, bank_fin_cat_add)

        # Удаление категории
        elif text == '**удалить**':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            vr[mid] = []
            categs, kol = get_categs(login, catg[login])
            for elem in categs:
                markup1.row(elem)
                vr[mid].append(elem.lower())
            if kol == 0:
                bot.send_message(mid, 'У вас нет категорий', reply_markup = MUP[step])
                return
            users[mid] += '_del'
            sent = bot.send_message(mid, 'Внимание! Пока в истории есть операции с этой категорией, удаление невозможно.\nВыберите категорию, которую хотите удалить', reply_markup = markup1)
            event[mid] = 1
            bot.register_next_step_handler(sent, bank_fin_cat_del)

        # Просмотр категорий
        elif text == '**категории**':
            bot.send_message(mid, watch_cat(login, catg[login]), reply_markup = MUP[step])

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

# Добавление уведомления о записи
# Вход: сообщение (время)
# Выход: -
def bank_notif_add(message):
    text = message.text.lower()
    mid = message.chat.id
    step = users[mid]
    login = kods[mid]

    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Неверный формат', reply_markup = MUP[step])
        return

    text = int(text)

    conn = sqlite3.connect(notif_db)
    cur = conn.cursor()
    cur.execute("INSERT INTO notif (login,time) VALUES ('%s','%d')"%(login, text))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, "Установлено уведомление на " + str(text) + ":00", reply_markup = MUP[step])

# Удаление уведомления о записи
# Вход: сообщение (время)
# Выход: -
def bank_notif_del(message):
    text = message.text.lower()
    mid = message.chat.id
    step = users[mid]
    login = kods[mid]

    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Уведомления в это время нет', reply_markup = MUP[step])
        return

    conn = sqlite3.connect(notif_db)
    cur = conn.cursor()
    cur.execute("DELETE FROM notif WHERE time = '%d'"%(int(text)))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, "Удаление выполнено", reply_markup = MUP[step])
    

# Проверка на короткую команду добавления расхода/дохода
# Вход: id пользователя, текст сообщения
# Выход: True если это нужное сообщение 
def short_add(mid, text):
    login = kods[mid]

    vr1[mid] = []
    
    if spend.get(mid) == None:
        bot.send_message(mid, 'У вас нет счетов')
        return
    if spend.get(mid) == 'все':
        banks, kol, osum = get_banks(login)
        if kol == 0:
            bot.send_message(mid, 'У вас нет счетов')
            return 
        spend[mid] = banks[0][0]
    try:
        text = text.split()
        if len(text) == 1:
            text = text[0]
            templates, kol = get_templates(login)
            for elem in templates:
                if text in elem[0]:
                    categ = elem[1]
                    sm = elem[2]
                    catg[login] = elem[3]
                    if sm != 0:
                        vr1[mid].append([categ, elem[0], sm, elem[3]])
            if vr1[mid] != []:
                catg[login] = vr1[mid][0][3]
                add_fin(mid, vr1[mid][0][1], vr1[mid][0][0], vr1[mid][0][2])
                return
            bot.send_message(mid, 'Не удалось найти такой шаблон')
            return
        try:
            sm = text[len(text) - 2]
            if sm[0] == '+':
                sm = sm[1:]
                catg[login] = 'fin'
            else:
                catg[login] = 'spend'
            sm = float(check_num(sm))
            categ = text.pop()
            text.pop()
            text = ' '.join(text)
            if check_text(text.lower(), 'ruseng1'):
                bot.send_message(mid, 'Используйте в описании только русские или английские символы, пробел или цифры')
                return
            if len(text) > 64:
                bot.send_message(mid, 'Максимальный размер описания - 64 символа')
                return
            vr1[mid] = []
            add_fin(mid, text, categ, sm)
            return
        except Exception:
            try:
                sm = text[len(text) - 1]
                if sm[0] == '+':
                    sm = sm[1:]
                    catg[login] = 'fin'
                else:
                    catg[login] = 'spend'
                sm = float(check_num(sm))
                text.pop()
                text = ' '.join(text)
                templates, kol = get_templates(login)
                for elem in templates:
                    if text in elem[0]:
                        categ = elem[1]
                        catg[login] = elem[3]
                        vr1[mid].append([categ, elem[0], sm, elem[3]])
                if vr1[mid] != []:
                    catg[login] = vr1[mid][0][3]
                    add_fin(mid, vr1[mid][0][1], vr1[mid][0][0], vr1[mid][0][2])
                    return
                bot.send_message(mid, 'Сообщение не распознано')
                return
            except Exception as e:
                #print(str(e))
                bot.send_message(mid, 'Сообщение не распознано')
                return
    except Exception as e:
        #print(str(e))
        bot.send_message(mid, 'Сообщение не распознано')
        return 

# Общая обработка регистрации
# Вход: логин, пароль и id нового пользователя 
# Выход: -
def registration(login, pas, mid):
    step = users[mid]

    logging.info('registration: Connecting to data base')
    conn = sqlite3.connect(db)
    logging.info('Connected')
    cur = conn.cursor()
    logging.info('registration: Inserting values into data base')
    cur.execute("INSERT INTO users (login,password) VALUES ('%s','%s')"%(login,pas))
    cur.execute("INSERT INTO zalog (id,login) VALUES ('%d','%s')"%(mid,login))
    conn.commit()
    cur.close()
    conn.close()
    
    logging.info('Creating directory')
    os.chdir(directory + 'users/')
    os.mkdir(login)
    logging.info('Created')
    logging.info('Connecting to user data base')
    conn = sqlite3.connect(user_db(login))
    logging.info('Connected')
    cur = conn.cursor()
    logging.info('Creating tebles')
    create_tables([login])
    logging.info('Created')
    for elem in categ_sp:
        cur.execute("INSERT INTO cats (login,cat) VALUES ('%s','%s')"%(login,elem))
    for elem in categ_fin:
        cur.execute("INSERT INTO fcats (login,cat) VALUES ('%s','%s')"%(login,elem))
    
    conn.commit()
    cur.close()
    conn.close()

    logging.info('registration: Connecting to notif data base')
    conn = sqlite3.connect(notif_db)
    logging.info('registration: Connected')
    cur = conn.cursor()
    logging.info('registration: Inserting values into notif data base')
    text = 22
    cur.execute("INSERT INTO notif (login,time) VALUES ('%s','%d')"%(login, text))
    logging.info('registration: Inserted')
    conn.commit()
    cur.close()
    conn.close()

    if dialogs.get(mid) != None:
        text = dialogs[mid]
        dialogs.pop(mid)
        logging.info('Starting alice__after_auth')
        bot.send_message(mid, alice_after_auth(text, login))
        logging.info('Finished alice_after_auth')
    
    logins.append(login)
    
    kods[mid] = login
    users[mid] = 'main'
    step = users[mid]
    
    keybSET = types.InlineKeyboardMarkup()
    cbtn = types.InlineKeyboardButton(text="Добавить счет", callback_data="bank_add")
    keybSET.add(cbtn)
    bot.send_message(mid, 'Регистрация успешно пройдена! Рекомендуем вам удалить сообщение с паролем', reply_markup = MUP[step])
    event[mid] = 0
    sent = bot.send_message(mid, 'Для начала работы вам осталось добавить счет (например, наличка). Вы можете сделать это, нажав кнопку ниже', reply_markup = keybSET)
    inline_mes[mid] = sent.message_id

# Обработка регистрации 1/2
# Вход: сообщение
# Выход: -
def reg1(message):
    text = message.text
    mid = message.chat.id
    step = users[mid]
    
    try:
        log, pas = text.split()
    except Exception:
        log = text.lower()
        if check_text(log, 'login'):
            users[mid] = prev_step(users[mid])
            event[mid] = 0
            bot.send_message(mid, 'Некорректный ввод.  Логин должен быть длиной не более 32 символов, а также могут использоваться только символы a...z или цифры')
            return
        if log in logins:
            bot.send_message(mid, 'Пользователь с таким именем уже существует')
            event[mid] = 0
            users[mid] = prev_step(users[mid])
            return
        vr[mid] = log
        sent = bot.send_message(mid, 'Введите пароль')
        users[mid] = 'mainUS_reg'
        event[mid] = 1
        bot.register_next_step_handler(sent, reg2)
        return
    
    log = log.lower()
    if check_text(log, 'login'):
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        bot.send_message(mid, 'Некорректный ввод.  Логин должен быть длиной не более 32 символов, а также могут использоваться только символы a...z или цифры')
        return
    if log in logins:
        bot.send_message(mid, 'Пользователь с таким именем уже существует')
        event[mid] = 0
        users[mid] = prev_step(users[mid])
        return
    if check_text(pas, 'pass'):
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        bot.send_message(mid, 'Некорректный ввод. Используйте только символы a..z, A..Z или цифры для пароля')
        return

    registration(log, pas, mid)

        
# Обработка регистрации 2/2
# Вход: сообщение
# Выход: -
def reg2(message):
    text = message.text
    mid = message.chat.id
    log = vr.pop(mid)
    pas = text

    if check_text(pas, 'pass'):
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        bot.send_message(mid, 'Некорректный ввод. Используйте только символы a..z, A..Z или цифры для пароля')
        return

    registration(log, pas, mid)

# Общая обработка входа
# Вход: логин, пароль и id
# Выход: -
def log_in(log, pas, mid):
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    for row in cur:
        if row[0] == log:
            if row[1] == pas:
                login = log
                kods[mid] = log
                cur.execute("INSERT INTO zalog (id,login) VALUES ('%d','%s')"%(mid,log))
                conn.commit()
                users[mid] = 'main'
                step = users[mid] = 'main'
                if dialogs.get(mid) != None:
                    text = dialogs[mid]
                    dialogs.pop(mid)
                    bot.send_message(mid, alice_after_auth(text, login))
                bot.send_message(mid, 'Авторизация пройдена! Рекомендуем вам удалить сообщение с паролем.', reply_markup = MUP[step])
            else:
                users[mid] = prev_step(users[mid])
                bot.send_message(mid, 'Пара логин/пароль не верна')
            cur.close()
            conn.close()
            event[mid] = 0
            return
    cur.close()
    conn.close()

# Вход в аккаунт 1/2
# Вход: сообщение
# Выход: -
def login1(message):
    text = message.text
    mid = message.chat.id
    step = users[mid]
    
    pas = ''
    try:
        log, pas = text.split()
    except Exception:
        log = text.lower()
        if log not in logins:
            users[mid] = prev_step(users[mid])
            event[mid] = 0
            bot.send_message(mid, 'Такого логина не существует')
            return
        if log in kods.values():
            users[mid] = prev_step(users[mid])
            event[mid] = 0
            bot.send_message(mid, 'Данный участник уже авторизирован')
            return
        vr[mid] = log
        sent = bot.send_message(mid, 'Введите пароль')
        users[mid] = 'mainUS_login'
        event[mid] = 1
        bot.register_next_step_handler(sent, login2)
        return

    log = log.lower()
    if log not in logins:
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        bot.send_message(mid, 'Такого логина не существует')
        return
    if log in kods.values():
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        bot.send_message(mid, 'Данный участник уже авторизирован')
        return

    log_in(log, pas, mid)

# Вход в аккаунт 2/2
# Вход: сообщение
# Выход: -
def login2(message):
    text = message.text
    mid = message.chat.id
    log = vr.pop(mid)
    pas = text
    log_in(log, pas, mid)

# Смена пароля 1/2
# Вход: сообщение
# Выход: -
def chngpass1(message):
    text = message.text
    mid = message.chat.id
    login = kods[mid]
    
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    for row in cur:
        if row[0] == login:
            if row[1] == text:
                sent = bot.send_message(mid, 'Введите новый пароль')
                event[mid] = 1
                bot.register_next_step_handler(sent, chngpass2)
            else:
                event[mid] = 0
                bot.send_message(mid, 'Пароль набран неправильно')
                users[mid] = prev_step(users[mid])
            cur.close()
            conn.close()
            return

# Смена пароля 2/2
# Вход: сообщение
# Выход: -
def chngpass2(message):
    mid = message.chat.id
    pas = message.text
    login = kods[mid]
    event[mid] = 0
    
    if check_text(pas, 'pass'):
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        bot.send_message(mid, 'Некорректный ввод. Используйте только символы a..z, A..Z или цифры для пароля')
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = '%s' WHERE login = '%s'"%(pas,login))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Пароль успешно изменен.\nРекомендуем удалить сообщение с паролем.')
    users[mid] = prev_step(users[mid])

# Добавление долга 1/2
# Вход: сообщение
# Выход: -
def addcredit1(message):
    mid = message.chat.id
    login = kods[mid]
    text = message.text.lower()
    step = users[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Такого счета нет', reply_markup = MUP[users[mid]])
        return
    vr[mid] = text
    sent = bot.send_message(mid, 'Введите фамилию, имя и размер долга через пробел', reply_markup = markupCanc)
    event[mid] = 1
    bot.register_next_step_handler(sent, addcredit2)
    
# Добавление долга 2/2
# Вход: сообщение
# Выход: -
def addcredit2(message):
    mid = message.chat.id
    login = kods[mid]
    text = message.text
    step = users[mid]

    if text.lower() == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    try:
        fam, im, dolg = text.split()
        dolg = round(float(check_num(dolg)),2)
        dolg = str(dolg)
        fam, im = fam + ' ' + im, im + ' ' + fam
    except Exception:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[step])
        return
    if check_text(fam.lower(), 'rus'):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Используйте только русские буквы', reply_markup = MUP[users[mid]])
        return
    if len(fam) > 64:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Слишком длинное имя', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT cred, sz FROM credits")
    for row in cur:
        if (row[0].lower() == fam.lower()) or (row[0].lower() == im.lower()):
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, 'Данный участник уже есть в базе. Пожалуйста, воспользуйтесь командой РЕДАКТИРОВАТЬ для изменения размера долга', reply_markup = MUP[step])
            cur.close()
            conn.close()
            return
    cur.execute("SELECT bal FROM bank WHERE name = '%s'"%(vr[mid]))
    for row in cur:
        if row[0] < round(float(dolg),2):
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, 'У вас нет столько денег', reply_markup = MUP[step])
            cur.close()
            conn.close()
            return
        sz = row[0]
    sz -= round(float(dolg),2)
    cur.execute("UPDATE bank SET bal = '%f' WHERE name = '%s'"%(sz,vr[mid]))
    tme[mid] = stday()
    cur.execute("INSERT INTO credits (login,cred,time,sz) VALUES ('%s','%s','%s','%f' )"%(login,fam,tme[mid],round(float(dolg),2)))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, 'Долг успешно добавлен.\nБаланс счета ' + vr[mid] + ': ' + str(round(sz,2)), reply_markup = MUP[step])

# Редактирование долгов 1/3
# Вход: сообщение
# Выход: - 
def edit1(message):
    text = message.text
    mid = message.chat.id
    login = kods[mid]
    step = users[mid]
    if text.lower() == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    try:
        fam, im = text.split()
    except Exception:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[step])
        return
    vr[mid] = fam + ' ' + im
    vr1[mid] = []
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    banks, kol, osum = get_banks(login)
    for elem in banks:
        markup1.row(elem[0])
        vr1[mid].append(elem[0].lower())
    sent = bot.send_message(mid, 'Выберите счет, на который будут положены деньги', reply_markup = markup1)
    event[mid] = 1
    bot.register_next_step_handler(sent, edit2)
    
# Редактирование долгов 2/3
# Вход: сообщение
# Выход: -
def edit2(message):
    text = message.text.lower()
    mid = message.chat.id
    login = kods[mid]
    step = users[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    if text.lower() not in vr1[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Такого счета нет', reply_markup = MUP[step])
        return
    vr1[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    debts, kol, osum = get_debts(login)
    for elem in debts:
        if elem[0] == vr[mid]:
            markup1.row(str(-elem[1]))
    sent = bot.send_message(mid, 'Введите сумму', reply_markup = markup1)
    event[mid] = 1
    bot.register_next_step_handler(sent, edit3)

# Редактирование долгов 3/3
# Вход: сообщение
# Выход: -
def edit3(message):
    text = message.text.lower()
    mid = message.chat.id
    login = kods[mid]
    step = users[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    fam, im = vr[mid].split()
    fam, im = fam + ' ' + im, im + ' ' + fam
    vr.pop(mid)
    try:
        text = round(float(check_num(text)),2)
    except Exception:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[step])
        return
    debts, kol, osum = get_debts(login)
    kdk = 0
    for elem in debts:
        if elem[0] == fam:
            kdk = 1
            zn = elem[1]
            break
        if elem[0] == im:
            kdk = 2
            zn = elem[1]
            break
    if kdk == 0:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Участник не найден', reply_markup = MUP[step])
        return
    if kdk == 2:
        fam = im
    zn = zn + text
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    if text > 0:
        cur.execute("SELECT bal FROM bank WHERE name = '%s'"%(vr1[mid]))
        for row in cur:
            if row[0] < text:
                users[mid] = prev_step(users[mid])
                step = users[mid]
                event[mid] = 0
                bot.send_message(mid, 'У вас нет столько денег', reply_markup = MUP[step])
                cur.close()
                conn.close()
                return
    if zn == 0:
        cur.execute("DELETE FROM credits WHERE cred = '%s'"%(fam))
    else:
        cur.execute("UPDATE credits SET sz = '%f' WHERE cred = '%s'"%(zn,fam))
    cur.execute("SELECT bal FROM bank WHERE name = '%s'"%(vr1[mid]))
    for row in cur:
        zn = row[0]
    zn -= text
    cur.execute("UPDATE bank SET bal = '%f' WHERE name = '%s'"%(zn,vr1[mid]))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, 'Операция успешно выполнена.\nБаланс счета ' + vr1[mid] + ': ' + str(round(zn,2)), reply_markup = MUP[step])

# Сброс данных
# Вход: сообщение
# Выход: -
def reset(message):
    mid = message.chat.id
    step = users[mid]
    login = kods[mid]
    text = message.text.lower()

    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return

    elif text == '**оставить категории**':
        vr[mid] = False

    elif text == '**удалить категории**':
        vr[mid] = True

    else:
        sent = bot.send_message(mid, 'Используйте клавиатуру для ответа', reply_markup = MUP[step])
        bot.register_next_step_handler(sent, reset)
        return

    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="reset_yes")
    cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="reset_no")
    keybGR.add(cbtn1, cbtn2)
    bot.send_message(mid, 'Сброс данных...', reply_markup = MUP[step])
    sent = bot.send_message(mid, 'Вы уверены, что хотите сбросить все данные? Отмена данной операции невозможна!', reply_markup = keybGR)
    inline_mes[mid] = sent.message_id    

# Просмотр счетов
# Вход: сообщение
# Выход: Сообщение со счетами
def watch_bank(message):
    mid = message.chat.id
    step = users[mid]
    login = kods[mid]
    
    banks, kol, osum = get_banks(login)
    
    sdebt = 0
    stroka = 'Ваши счета:\n'

    for i, elem in enumerate(banks):
        stroka += str(i + 1) + ') ' + elem[0] + '\nБаланс: ' + str(round(elem[1], 2)) + '\n\n'
    stroka += 'Сумма: ' + str(round(osum,2))

    debts, kol1, sdebt = get_debts(login)
    if sdebt != 0:
        stroka += '\nСумма, учитывая долги: ' + str(round(osum+sdebt,2))
    
    if kol == 0:
        users[mid] = prev_step(users[mid])
        keybSET = types.InlineKeyboardMarkup()
        cbtn = types.InlineKeyboardButton(text="Добавить счет", callback_data="bank_add")
        keybSET.add(cbtn)
        sent = bot.send_message(mid, 'Для начала работы вам нужно добавить счет (например, наличка). Вы можете сделать это, нажав кнопку ниже', reply_markup = keybSET)
        inline_mes[mid] = sent.message_id
        return
        
    bot.send_message(mid, stroka, reply_markup = MUP[step])

# Создание нового счета 1/3
# Вход: id пользователя
# Выход: 
def new_bank(mid):
    sent = bot.send_message(mid, 'Введите название счета (до 32 символов)', reply_markup = markupCanc)
    users[mid] += '_add'
    event[mid] = 1
    bot.register_next_step_handler(sent, bank_add1)

# Создание нового счета 2/3
# Вход: сообщение
# Выход: -
def bank_add1(message):
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    if text == 'все':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Пожалуйста, выберите другое имя', reply_markup = MUP[step])
        return
    if len(text) > 32:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Слишком длинное название', reply_markup = MUP[step])
        return
    if check_text(text.lower(), 'rus1'):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Используйте только русские буквы, пробел или цифры', reply_markup = MUP[step])
        return
    banks, kol, osum = get_banks(login)
    for elem in banks:
        if elem[0].lower() == text:
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, 'Данный счет уже есть в базе', reply_markup = MUP[step])
            return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('0')
    sent = bot.send_message(mid, 'Введите начальный баланс счета', reply_markup = markup1)
    event[mid] = 1
    bot.register_next_step_handler(sent, bank_add2)

# Создание нового счета 3/3
# Вход: сообщение
# Выход: -
def bank_add2(message):
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    if text[0] == '-':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        return
    try:
        text = round(float(check_num(text)),2)
    except Exception:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Неверный формат ввода', reply_markup = MUP[step])
        return
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("INSERT INTO bank (login,name,bal) VALUES ('%s','%s',%f)"%(login,vr[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    event[mid] = 0
    users[mid] = prev_step(users[mid])
    step = users[mid]
    bot.send_message(mid, 'Счет добавлен', reply_markup = MUP[step])

# Удаление счета
# Вход: сообщение
# Выход: -
def bank_del(message):
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Данного счета не существует', reply_markup = MUP[step])
        return
    
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT bank FROM spend WHERE bank = '%s'"%(text))
    for row in cur:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Сначала необходимо удалить операции с данным счетом', reply_markup = MUP[step])
        cur.close()
        conn.close()
        return
    cur.execute("SELECT bank FROM inc WHERE bank = '%s'"%(text))
    for row in cur:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, 'Сначала необходимо удалить операции с данным счетом', reply_markup = MUP[step])
        cur.close()
        conn.close()
        return
    cur.close()
    conn.close()    
    if text == spend[mid].lower():
        spend[mid] = 'все'
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    vr[mid] = text
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="bank_del_yes")
    cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="bank_del_no")
    keybGR.add(cbtn1, cbtn2)
    bot.send_message(mid, 'Удаление счета...', reply_markup = MUP[step])
    sent = bot.send_message(mid, 'Вы уверены, что хотите удалить счет? Его баланс будет удален!', reply_markup = keybGR)
    #bot.editMessageReplyMarkup(chat_id = sent.message_id, message_id = mid, reply_markup = keybGR)
    #bot.editMessageText(chat_id = sent.message_id, message_id = mid, text = 'Вы уверены, что хотите удалить счет? Его баланс будет удален!', reply_markup = keybGR)
    inline_mes[mid] = sent.message_id

# Главная расходы/доходы
# Вход: id пользователя
# Выход: -
def bank_fin(mid):
    login = kods[mid]

    logging.info('bank_fin [%s]: Getting banks', login)
    banks, kol, osum = get_banks(login)
    if kol == 0:
        logging.info('bank_fin [%s]:No banks', login)
        keybSET = types.InlineKeyboardMarkup()
        cbtn = types.InlineKeyboardButton(text="Добавить счет", callback_data="bank_add")
        keybSET.add(cbtn)
        sent = bot.send_message(mid, 'Для начала работы вам нужно добавить счет (например, наличка). Вы можете сделать это, нажав кнопку ниже', reply_markup = keybSET)
        inline_mes[mid] = sent.message_id
        return
    logging.info('bank_fin [%s]: Got', login)
    tme = tday()
    logging.info('bank_fin [%s]: Getting history', login)
    data, diag = get_fin_his(tme[0], tme[1], tme[2], tme[0], tme[1], tme[2], 0, 1, login, catg[login], 'все', 'все', 0)
    logging.info('bank_fin [%s]: Got', login)
    users[mid] += '_' + catg[login]
    step = users[mid]
    if spend.get(mid) == None:
        spend[mid] = 'все'
    bot.send_message(mid, "Текущий счет: " + spend[mid], reply_markup = MUP[step])
    if diag != 2:
        bot.send_message(mid, data)

# Смена счета
# Вход: сообщение
# Выход: -
def bank_change(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    if text == '**все**':
        spend[mid] = 'все'
        bot.send_message(mid, "Выбраны все счета", reply_markup = MUP[step])
    elif text not in vr[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[step])
    else:
        spend[mid] = text
        bot.send_message(mid, "Выбран счет: " + spend[mid], reply_markup = MUP[step])
    vr.pop(mid)

# Смена счета для добавления/редактирования расходов/доходов
def bank_fin_change(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    step = users[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text == '**все**':
        spend[mid] = 'все'
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Нельзя выбрать все счета", reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[step])
        return
    spend[mid] = text

    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**отмена**')
    vr[mid] = []
    categs, kol = get_categs(login, catg[login])
    if kol == 0:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[step])
        return
    for elem in categs:
        markup1.row(elem)
        vr[mid].append(elem.lower())

    vr1[mid] += '_no'

    if vr1[mid] == 'new_no':
        sent = bot.send_message(mid, "Выберите категорию\nТекущий счет: " + spend[mid], reply_markup = markup1)
        event[mid] = 1
        bot.register_next_step_handler(sent, bank_fin_add1)

    elif vr1[mid] == 'edit_no':
        sent = bot.send_message(mid, "Выберите категорию, позицию из которой вы хотите редактировать\nТекущий счет: " + spend[mid], reply_markup = markup1)
        event[mid] = 1
        bot.register_next_step_handler(sent, bank_fin_edit1) 

# Создание новой категории
# Вход: сообщение
# Выход: -
def bank_fin_cat_add(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    users[mid] = prev_step(users[mid])
    event[mid] = 0
    step = users[mid]
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text == 'все':
        bot.send_message(mid, "Данное имя выбрать невозможно", reply_markup = MUP[step])
        return
    if check_text(text, 'rus1'):
        bot.send_message(mid, 'Используйте только русские буквы, пробел или цифры', reply_markup = MUP[step])
        return
    if len(text) > 64:
        bot.send_message(mid, 'Название не должно содержать более 64 символов', reply_markup = MUP[step])
        return
    categs, kol = get_categs(login, catg[login])
    for elem in categs:
        if elem == text:
            bot.send_message(mid, "Данная категория уже существует", reply_markup = MUP[step])
            return
    
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    if catg[login] == 'spend':
        cur.execute("INSERT INTO cats (login,cat) VALUES ('%s','%s')"%(login,text))
    elif catg[login] == 'fin':
        cur.execute("INSERT INTO fcats (login,cat) VALUES ('%s','%s')"%(login,text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Категория добавлена", reply_markup = MUP[step])

# Удаление категории
# Вход: сообщение
# Выход: -
def bank_fin_cat_del(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    users[mid] = prev_step(users[mid])
    event[mid] = 0
    step = users[mid]
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[step])
        return
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    if catg[login] == 'spend':
        cur.execute("SELECT cat FROM spend")
    elif catg[login] == 'fin':
        cur.execute("SELECT cat FROM inc")
    for row in cur:
        if row[0].lower() == text:
            bot.send_message(mid, "Данная категория используется, удаление невозможно", reply_markup = MUP[step])
            cur.close()
            conn.close()
            return
    if catg[login] == 'spend':
        cur.execute("DELETE FROM cats WHERE cat = '%s'"%(text))
    elif catg[login] == 'fin':
        cur.execute("DELETE FROM fcats WHERE cat = '%s'"%(text))
    cur.execute("DELETE FROM template WHERE cat = '%s'"%(text))
    cur.execute("DELETE FROM limits WHERE cat = '%s'"%(text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Удаление выполнено", reply_markup = MUP[step])

# История 1/2
# Вход: сообщение
# Выход: -
def bank_fin_his1(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    step = users[mid]
    if text not in vr[mid] and text != '**все**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[step])
        return
    if text == '**все**':
        text = 'все'
    vr[mid] = text
    sent = bot.send_message(mid, 'Выберите период просмотра.\nДопустимые форматы ввода:\n1) гггг (расходы/доходы будут показываться отдельно по всем месяцам года)\n2)мм гггг (расходы/доходы за определенный месяц)\n3)дд мм гггг (расходы/доходы за определенный день)\n4)мм гггг мм гггг (расходы/доходы будут показываться отдельно по месяцам)5)дд мм гггг дд мм гггг (расходы/доходы С и ДО введенных дат)', reply_markup = MUP[step])
    event[mid] = 1
    bot.register_next_step_handler(sent, bank_fin_his2)

# История 2/2
# Вход: сообщение
# Выход: -
def bank_fin_his2(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    step = users[mid]
    show = 1
    tm = tday()
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
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
        tm = day_min(1)
        sday = int(tm[0])
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])
        
    elif text == '**этот месяц**':
        sday = 1
        fday = 31
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
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
            return
        show = 0
        users[mid] = prev_step(users[mid])
        step = users[mid]
        for i in range(k, -1, -1):
            sday, smon, syear, fday, fmon, fyear = tweek(7 * i)
            stroka, diag = get_fin_his(sday, smon, syear, fday, fmon, fyear, kod_mon, show, login, catg[login], spend[mid], vr[mid], 1)
            if diag == 1:
                try:
                    diag = open(user_res(login) + 'diag.png','rb')
                    bot.send_photo(mid, diag)
                except Exception as e:
                    bot.send_message(admin_ids[0], str(e))
            bot.send_message(mid, stroka, reply_markup = MUP[step])
        event[mid] = 0
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
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
            return

    if sday < 1 or sday > 31 or fday < 1 or fday > 31 or smon < 1 or smon > 12 or fmon < 1 or fmon > 12 or syear < 2000 or fyear < syear or (fyear == syear and fmon < smon) or (fyear == syear and fmon == smon and fday < sday):
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        return
    stroka, diag = get_fin_his(sday, smon, syear, fday, fmon, fyear, kod_mon, show, login, catg[login], spend[mid], vr[mid], 1)
    if diag == 1:
        try:
            diag = open(user_res(login) + 'diag.png','rb')
            bot.send_photo(mid, diag)
        except Exception as e:
            bot.send_message(admin_ids[0], str(e))
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, stroka, reply_markup = MUP[step])

# Добавление расхода/дохода короткой строкой
# Вход: описание, категория, сумма
# Выход: -
def add_fin(mid, text, categ, sm):
    f_name = 'add_fin'
    login = kods[mid]

    if len(vr1[mid]) == 0:

        logging.info('%s [%s]: Getting categs', f_name, login)
        
        vr1[mid] = []
        categs, kol = get_categs(login, catg[login])
        if kol == 0:
            logging.info('%s [%s]: No categs', f_name, login)
            bot.send_message(mid, 'У вас нет категорий')
            return

        logging.info('%s [%s]: %s', f_name, login, 'Got')

        logging.info('%s [%s]: Creating list of categs', f_name, login)
        
        for elem in categs:
            if categ in elem or categ == elem:
                vr1[mid].append(elem)

        if vr1[mid] == []:
            logging.info('%s [%s]: No such categs', f_name, login)
            bot.send_message(mid, 'Таких категорий не найдено')
            return

        logging.info('%s [%s]: Created with %d categs', f_name, login, len(vr1[mid]))

        categ = vr1[mid][0]

        vr[mid] = [categ, text, sm]

        logging.info('%s [%s]: Creating markup', f_name, login)

        keybGR = types.InlineKeyboardMarkup()
        for i, elem in enumerate(vr1[mid]):
            if elem != categ:
                cbtn = types.InlineKeyboardButton(text=elem, callback_data="short_add_changecat_" + str(i))
                keybGR.add(cbtn)

    else:
        logging.info('%s [%s]: It is template', f_name, login)
        logging.info('%s [%s]: Creating markup', f_name, login)
        vr[mid] = [categ, text, sm]
        keybGR = types.InlineKeyboardMarkup()
        for i, elem in enumerate(vr1[mid]):
            if elem[:3] != vr[mid]:
                cbtn = types.InlineKeyboardButton(text=elem[1], callback_data="short_add_changetempl_" + str(i))
                keybGR.add(cbtn)

    cbtn = types.InlineKeyboardButton(text="Поменять счет", callback_data="short_add_changebank")
    keybGR.add(cbtn)
    
    cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="short_add_yes")
    cbtn2 = types.InlineKeyboardButton(text="Отмена", callback_data="short_add_no")
    keybGR.add(cbtn1, cbtn2)

    logging.info('%s [%s]: Created', f_name, login)
    
    if catg[login] == 'spend':
        stroka = 'Добавление расхода:\n'
    elif catg[login] == 'fin':
        stroka = 'Добавление дохода:\n'
    stroka += text
    if text != '':
        stroka += ' '
    stroka += str(sm) + 'р\n'
    stroka += 'Категория: ' + categ + '\n'
    stroka += 'Счет: ' + spend[mid] + '\n'
    stroka += 'Добавляем?'
    sent = bot.send_message(mid, stroka, reply_markup = keybGR)
    inline_mes[mid] = sent.message_id
    vr2[mid] = keybGR
    

# Добавление 1/3
# Вход: сообщение (категория)
# Выход: -
def bank_fin_add1(message):
    mid = message.chat.id
    if vr1[mid] != 'new_no':
        return
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[step])
        return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('**Сегодня**')
    markup1.row('**Вчера**')
    sent = bot.send_message(mid, "Введите дату? (Формат: дд мм гггг)", reply_markup = markup1)
    event[mid] = 1
    bot.register_next_step_handler(sent, bank_fin_add2)

# Добавление 2/3
# Вход: сообщение (дата)
# Выход: -
def bank_fin_add2(message): 
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text == '**сегодня**':
        tme[mid] = tday()
    elif text == '**вчера**':
        tme[mid] = day_min(1)
    else:
        text = text.split()
        try:
            for i in range(len(text)):
                text[i] = int(text[i])
            tme[mid] = text
        except Exception:
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])
            return
    if tme[mid][0] < 1 or tme[mid][0] > 31 or tme[mid][1] < 1 or tme[mid][1] > 12:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода даты", reply_markup = MUP[step])
        return
    if catg[login] == 'spend':
        sent = bot.send_message(mid, "Напишите расход в формате: описание (не обязательно, не должно начинаться с числа) + сумма расхода")
    elif catg[login] == 'fin':
        sent = bot.send_message(mid, "Напишите доход в формате: описание (не обязательно, не должно начинаться с числа) + сумма дохода")
    event[mid] = 1
    bot.register_next_step_handler(sent, bank_fin_add3)

# Добавление 3/3
# Вход: сообщение
# Выход: -
def bank_fin_add3(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    text = text.split()
    ras = 0
    if text[len(text)-1][0] == '-':
        if catg[login] == 'spend':
            bot.send_message(mid, "Отрицательный расход? Хаха, нет", reply_markup = MUP[step])
        elif catg[login] == 'fin':
            bot.send_message(mid, "Отрицательный доход? Хаха, нет", reply_markup = MUP[step])
        return
    try:
        ras = round(float(check_num((text[len(text)-1]))),2)
    except Exception:
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])
        return
    text.pop()
    if len(text) == 0:
        text = '%' + str(nums())
    else:
        text = ' '.join(text)
        if check_text(text.lower(), 'ruseng1'):
            bot.send_message(mid, 'Используйте в описании только русские или английские символы, пробел или цифры', reply_markup = MUP[step])
            return
        if len(text) > 64:
            bot.send_message(mid, 'Максимальный размер описания - 64 символа', reply_markup = MUP[step])
            return
        text += '%' + str(nums())
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE name = '%s'"%(spend[mid]))
    for row in cur:
        bal = round(float(row[0]),2)
    if catg[login] == 'spend':
        bal -= ras
    elif catg[login] == 'fin':
        bal += ras
    if bal < 0:
        bot.send_message(mid, "У вас нет столько средств", reply_markup = MUP[step])
        cur.close()
        conn.close()
        return
    tm = tme[mid]
    tme.pop(mid)
    cur.execute("UPDATE bank SET bal = '%f' WHERE name = '%s'"%(bal,spend[mid]))
    if catg[login] == 'spend':
        cur.execute("INSERT INTO spend (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(login,tm[2],tm[1],tm[0],vr[mid],spend[mid],text.lower(),ras))
    elif catg[login] == 'fin':
        cur.execute("INSERT INTO inc (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(login,tm[2],tm[1],tm[0],vr[mid],spend[mid],text.lower(),ras))
    conn.commit()
    cur.close()
    conn.close()
    if catg[login] == 'spend':
        stroka = fin_add_limits(mid, vr[mid], ras, tm)
    vr.pop(mid)
    bot.send_message(mid, "Операция выполнена\nБаланс счета " + spend[mid] + ': ' + str(round(bal,2)) + '\n' + stroka, reply_markup = MUP[step])

# Учитывание расхода в лимитах
# Вход: категория, сумма
# Выход: строка
def fin_add_limits(mid, categ, sm, tm, al = 1):
    login = kods[mid]

    logging.info('fin_add_limits [%s]: Getting limits', login)
    limits, kol = get_limits(login)
    if kol == 0:
        logging.info('fin_add_limits [%s]: No limits', login)
        return ''
    logging.info('fin_add_limits [%s]: Got', login)

    stroka = '\n'

    td_lims = []
    al_lims = []
    categs = []
    counts = []
    durs = []

    for elem in limits:
        elem[3] -= sm
        elem[4] += sm
        r_categ, count, dur, tlim, osum, lim_sum, f_day, f_month, f_year = elem
        if r_categ != '#all' and r_categ != categ:
            logging.info('fin_add_limits [%s]: Wrong categ', login)
            continue
        if al == 0 and r_categ == '#all':
            logging.info('fin_add_limits [%s]: No change #all categ', login)
            continue
        if check_add_limit(count, dur, f_day, f_month, f_year, tm):
            logging.info('fin_add_limits [%s]: Adding limit to list', login)
            if r_categ == '#all':
                k = day_count(tday(), [f_day, f_month, f_year])
                day = day_end(k)
                stroka += 'У вас осталось ' + str(round(lim_sum - osum, 2)) + 'р из ' + str(round(lim_sum, 2)) + 'р на ' + str(k) + ' ' + day + ' (до ' + str(f_day) + ' ' + monthR[f_month] + ' ' + str(f_year) + ' года)\n'
                if elem[2] == 'day' or elem[2] == 'week':
                    if elem[3] > 0:
                        stroka += 'А сегодня можно потратить еще ' + str(round(elem[3], 2)) + 'р\n'
                    elif elem[3] == 0:
                        stroka += 'Вы израсходовали весь лимит на сегодня.\n'
                    else:
                        stroka += 'Вы потратили сегодня больше на ' + str(round(-elem[3], 2)) + 'р, чем можно было. Будьте аккуратнее.\n'
            td_lims.append(tlim)
            al_lims.append(osum)
            categs.append(r_categ)
            counts.append(count)
            durs.append(dur)
            logging.info('fin_add_limits [%s]: Added', login)

    if len(durs) > 0:
        logging.info('fin_add_limits [%s]: Connecting to data base', login)
        conn = sqlite3.connect(user_db(login))
        cur = conn.cursor()
        logging.info('fin_add_limits [%s]: Connected', login)

    for i in range(len(td_lims)):
        logging.info('fin_add_limits [%s]: Updating tlim', login)
        cur.execute("UPDATE limits SET tlim = ? WHERE cat = ? AND count = ? AND dur = ?", [(round(td_lims[i], 2)), (categs[i]), (counts[i]), (durs[i])])
        logging.info('fin_add_limits [%s]: Updating sum', login)
        cur.execute("UPDATE limits SET sum = ? WHERE cat = ? AND count = ? AND dur = ?", [(round(al_lims[i], 2)), (categs[i]), (counts[i]), (durs[i])])
        logging.info('fin_add_limits [%s]: Updated', login)

    if len(durs) > 0:
        logging.info('fin_add_limits [%s]: Closing data base', login)
        conn.commit()
        cur.close()
        conn.close()
        logging.info('fin_add_limits [%s]: Closed', login)
    
    return stroka

# Редактирование 1/5
# Вход: сообщение (категория)
# Выход: -
def bank_fin_edit1(message):
    mid = message.chat.id
    if vr1[mid] != 'edit_no':
        return
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        vr.pop(mid)
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[step])
        vr.pop(mid)
        return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('**Сегодня**')
    markup1.row('**Вчера**')
    event[mid] = 1
    sent = bot.send_message(mid, "Позицию за какое число вы хотите редактировать? (Формат: дд мм гггг)", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_fin_edit2)

# Редактирование 2/5
# Вход: сообщение (дата)
# Выход: -
def bank_fin_edit2(message):
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    
    if text.lower() == '**отмена**':
        logging.info('bank_fin_edit3 [%s]: Cancelled', login)
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        vr.pop(mid)
        return
    logging.info('bank_fin_edit3 [%s]: Getting text', login)
    if text == '**сегодня**':
        tme[mid] = tday()
    elif text == '**вчера**':
        tme[mid] = day_min(1)
    else:
        text = text.split()
        try:
            for i in range(len(text)):
                text[i] = int(text[i])
            tme[mid] = text
        except Exception:
            logging.info('bank_fin_edit3 [%s]: Wrong format', login)
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])
            vr.pop(mid)
            return
    logging.info('bank_fin_edit3 [%s]: Got', login)
    if tme[mid][0] < 1 or tme[mid][0] > 31 or tme[mid][1] < 1 or tme[mid][1] > 12:
        logging.info('bank_fin_edit3 [%s]: Wrong format', login)
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        vr.pop(mid)
        return
    
    logging.info('bank_fin_edit3 [%s]: Connecting to data base', login)
    conn = sqlite3.connect(user_db(login))
    logging.info('bank_fin_edit3 [%s]: Connected', login)
    cur = conn.cursor()
    if catg[login] == 'spend':
        stroka = "Ваши расходы по данным параметрам\n\n"
        cur.execute("SELECT name, sum FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid]))
    elif catg[login] == 'fin':
        stroka = "Ваши доходы по данным параметрам\n\n"
        cur.execute("SELECT name, sum FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid]))
    logging.info('bank_fin_edit2 [%s]: Getting data from data base', login)
    rows = cur.fetchall()
    logging.info('bank_fin_edit2 [%s]: Got', login)
    logging.info('bank_fin_edit2 [%s]: Closing connecton', login)
    cur.close()
    conn.close()
    logging.info('bank_fin_edit2 [%s]: Closed', login)
    kol = 0
    vr1[mid] = {}
    logging.info('bank_fin_edit2 [%s]: Creating markup', login)
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    for row in rows:
        kol += 1
        txt = row[0]
        txt = txt.split('%')
        markup1.row(str(kol))
        stroka += 'Номер ' + str(kol) + '\n' + 'Сумма: ' + str(row[1]) + '\n' + txt[0] + '\n\n'
        vr1[mid][str(kol)] = row[0].lower() #номер и описание
    logging.info('bank_fin_edit2 [%s]: Created', login)
    if kol == 0:
        logging.info('bank_fin_edit2 [%s]: No data', login)
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Позиций по заданным параметрам не найдено", reply_markup = MUP[step])
        return
    stroka += "Выберите номер позиции, которую хотите редактировать"
    sent = bot.send_message(mid, stroka, reply_markup = markup1)
    event[mid] = 1
    bot.register_next_step_handler(sent, bank_fin_edit3)

# Редактирование 3/5
# Вход: сообщение
# Выход: -
def bank_fin_edit3(message):
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    
    if text == '**отмена**':
        logging.info('bank_fin_edit3 [%s]: Cancelled', login)
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        vr1.pop(mid)
        return
    if text not in vr1[mid]:
        logging.info('bank_fin_edit3 [%s]: Wrong format', login)
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат или такой позиции нет", reply_markup = MUP[step])
        vr1.pop(mid)
        return
    txt = vr1[mid][text]
    vr2[mid] = txt
    txt = txt.split('%')

    logging.info('bank_fin_edit3 [%s]: Connecting to data base', login)
    conn = sqlite3.connect(user_db(login))
    logging.info('bank_fin_edit3 [%s]: Connected', login)
    cur = conn.cursor()
    if catg[login] == 'spend':
        cur.execute("SELECT sum FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    elif catg[login] == 'fin':
        cur.execute("SELECT sum FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    logging.info('bank_fin_edit3 [%s]: Getting data from data base', login)
    rows = cur.fetchall()
    logging.info('bank_fin_edit3 [%s]: Got', login)
    logging.info('bank_fin_edit3 [%s]: Closing connecton', login)
    cur.close()
    conn.close()
    logging.info('bank_fin_edit3 [%s]: Closed', login)
    for row in rows:
        vr3[mid] = row[0]
        stroka = 'Дата: ' + str(tme[mid][0]) + '.' + str(tme[mid][1]) + '.' + str(tme[mid][2]) + '\n'
        stroka += 'Счет: ' + spend[mid] + '\nКатегория: ' + vr[mid] + '\nСумма: ' + str(vr3[mid]) + '\n'
        if len(txt[0]) != 0:
            stroka += txt[0]
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    logging.info('bank_fin_edit3 [%s]: Creating markup', login)
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Удалить", callback_data="bank_fin_del_yes")
    cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="bank_fin_del_no")
    keybGR.add(cbtn1, cbtn2)
    cbtn1 = types.InlineKeyboardButton(text="Поменять категорию", callback_data="bank_fin_chngcat")
    keybGR.add(cbtn1)
    cbtn1 = types.InlineKeyboardButton(text="Поменять сумму", callback_data="bank_fin_chngsum")
    keybGR.add(cbtn1)
    logging.info('bank_fin_edit3 [%s]: Created', login)
    bot.send_message(mid, 'Что вы хотите сделать?', reply_markup = MUP[step])
    sent = bot.send_message(mid, stroka, reply_markup = keybGR)
    inline_mes[mid] = sent.message_id
    

# Редактирование 4/5 (смена категории)
# Вход: сообщение
# Выход: -
def bank_fin_edit4(message):
    mid = message.chat.id
    text = message.text.lower()
    step = users[mid]
    login = kods[mid]
    
    if text == '**отмена**':
        logging.info('bank_fin_edit4 [%s]: Cancelled', login)
        event[mid] = 0
        users[mid] = prev_step(users[mid])
        step = users[mid]
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text not in vr1[mid]:
        logging.info('bank_fin_edit4 [%s]: Wrong category', login)
        event[mid] = 0
        users[mid] = prev_step(users[mid])
        step = users[mid]
        bot.send_message(mid, "У вас нет такой категории", reply_markup = MUP[step])
        return
    
    logging.info('bank_fin_edit4 [%s]: Connecting to data base', login)
    conn = sqlite3.connect(user_db(login))
    logging.info('bank_fin_edit4 [%s]: Connected', login)
    cur = conn.cursor()
    if catg[login] == 'spend':
        logging.info('bank_fin_edit4 [%s]: Updating spend', login)
        cur.execute("UPDATE spend SET cat = '%s' WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND name = '%s'"%(text,tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr2[mid]))
        logging.info('bank_fin_edit4 [%s]: Updated', login)
    elif catg[login] == 'fin':
        logging.info('bank_fin_edit4 [%s]: Updating fin', login)
        cur.execute("UPDATE inc SET cat = '%s' WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND name = '%s'"%(text,tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr2[mid]))
        logging.info('bank_fin_edit4 [%s]: Updated', login)
    logging.info('bank_fin_edit4 [%s]: Closing data base connection', login)
    conn.commit()
    cur.close()
    conn.close()
    logging.info('bank_fin_edit4 [%s]: Closed', login)
    if catg[login] == 'spend':
        logging.info('bank_fin_edit4 [%s]: Removing limits in old categs', login)
        stroka = fin_add_limits(mid, vr[mid], -vr3[mid], tme[mid], al = 0)
        logging.info('bank_fin_edit4 [%s]: Removed', login)
        logging.info('bank_fin_edit4 [%s]: Adding limits in new categs', login)
        stroka = fin_add_limits(mid, text, vr3[mid], tme[mid], al = 0)
        logging.info('bank_fin_edit4 [%s]: Added', login)
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, "Категория изменена", reply_markup = MUP[step])

# Редактирование 5/5 (смена суммы)
# Вход: сообщение
# Выход: -
def bank_fin_edit5(message):
    mid = message.chat.id
    text = message.text.lower()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    login = kods[mid]
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        event[mid] = 0
        return
    ras = 0
    if text[0] == '-':
        if catg[login] == 'spend':
            bot.send_message(mid, "Отрицательный расход? Хаха, нет", reply_markup = MUP[step])
        if catg[login] == 'inc':
            bot.send_message(mid, "Отрицательный доход? Хаха, нет", reply_markup = MUP[step])
        event[mid] = 0
        return
    try:
        ras = round(float(check_num((text))),2)
    except Exception:
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])
        event[mid] = 0
        return
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE name = '%s'"%(spend[mid]))
    for row in cur:
        bal = round(float(row[0]),2)
    if catg[login] == 'spend':
        bal += (vr3[mid]-ras)
    elif catg[login] == 'fin':
        bal -= (vr3[mid]-ras)
    if bal < 0:
        event[mid] = 0
        bot.send_message(mid, "Операция невозможна, так как баланс стал отрицательным", reply_markup = MUP[step])
        cur.close()
        conn.close()
        return
    cur.execute("UPDATE bank SET bal = '%f' WHERE name = '%s'"%(bal,spend[mid]))
    if catg[login] == 'spend':
        cur.execute("UPDATE spend SET sum = '%f' WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(ras,tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    elif catg[login] == 'fin':
        cur.execute("UPDATE inc SET sum = '%f' WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(ras,tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    conn.commit()
    cur.close()
    conn.close()
    if catg[login] == 'spend':
        stroka = fin_add_limits(mid, vr[mid], ras-vr3[mid], tme[mid])
    event[mid] = 0
    bot.send_message(mid, "Сумма изменена\nБаланс счета " + spend[mid] + ': ' + str(round(bal,2)), reply_markup = MUP[step])
    
# Добавление шаблона 1/3
# Вход: сообщение (расход/доход)
# Выход: -
def bank_templates_add1(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text == '**расход**':
        catg[login] = 'spend'
    elif text == '**доход**':
        catg[login] = 'fin'
    else:
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Надо было выбрать расход или доход", reply_markup = MUP[step])
        return
    
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**отмена**')
    vr[mid] = []
    categs, kol = get_categs(login, catg[login])
    for elem in categs:
        markup1.row(elem)
        vr[mid].append(elem)
            
    if kol == 0:
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[step])
        return
            
    sent = bot.send_message(mid, "Выберите категорию", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_templates_add2)

# Добавление шаблона 2/3
# Вход: сообщение (категория)
# Выход: -
def bank_templates_add2(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[step])
        return

    vr[mid] = text
    sent = bot.send_message(mid, "Напишите шаблон в формате (сумма необязательна):\n*Название* *сумма*", reply_markup = markupCanc)
    bot.register_next_step_handler(sent, bank_templates_add3)

# Добавление шаблона 3/3
# Вход: сообщение (шаблон)
# Выход: -
def bank_templates_add3(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    text = text.split()
    sm = text.pop()
    if sm[0] == '-':
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Число должно быть положительное", reply_markup = MUP[step])
        return
    try:
        ras = round(float(check_num((sm))),2)
        sm = ras
    except Exception:
        text.append(sm)
        sm = 0
    text = ' '.join(text)
    if check_text(text, 'ruseng1'):
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, 'Используйте в названии только русские или английские символы, пробел или цифры', reply_markup = MUP[step])
        return
    if len(text) > 64:
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, 'Максимальный размер названия - 64 символа', reply_markup = MUP[step])
        return
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT login FROM template WHERE name = '%s'"%(text))
    for row in cur:
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Шаблон с данным именем уже существует", reply_markup = MUP[step])
        cur.close()
        conn.close()
        return
    cur.execute("INSERT INTO template (login, name, cat, sum, sect) VALUES (?, ?, ?, ?, ?)", [(login), (text), (vr[mid]), (sm), (catg[login])])
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    event[mid] = 0
    step = users[mid]
    bot.send_message(mid, "Шаблон добавлен", reply_markup = MUP[step])

# Удаление шаблонов
# Вход: сообщение (название шаблона)
# Выход: -
def bank_templates_del(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    users[mid] = prev_step(users[mid])
    event[mid] = 0
    step = users[mid]
    if text == '**отмена**':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        bot.send_message(mid, "Такого шаблона нет", reply_markup = MUP[step])
        return
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("DELETE FROM template WHERE name = ?", [(text)])
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Удаление выполнено", reply_markup = MUP[step])

# Добавление лимита 1/4
# Вход: сообщение (категория)
# Выход: -
def bank_limits_add1(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text == '*все категории*':
        text = '#all'
    if text not in vr[mid][0]:
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[step])
        return
    vr[mid][0] = text
    sent = bot.send_message(mid, "Напишите сумму лимита", reply_markup = markupCanc)
    bot.register_next_step_handler(sent, bank_limits_add2)

# Добавление лимита 2/4
# Вход: сообщение (сумма)
# Выход: -
def bank_limits_add2(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    try:
        text = round(float(check_num(text)),2)
    except Exception:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])	
        return
    vr[mid].append(text)
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('**Сегодня**')
    markup1.row('**Со следующей недели**')
    markup1.row('**Со следующего месяца**')
    sent = bot.send_message(mid, "Напишите дату начала периода (Формат: дд мм гггг)", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_limits_add3)

# Добавление лимита 3/4
# Вход: сообщение (дата начала)
# Выход: -
def bank_limits_add3(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    if text == '**отмена**':
        logging.info('bank_limits_add3 [%s]: Cancelled', login)
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        vr.pop(mid)
        return
    logging.info('bank_limits_add3 [%s]: Getting start date', login)
    if text == '**сегодня**':
        tme[mid] = tday()
    elif text == '**со следующей недели**':
        tme[mid] = next_week()
    elif text == '**со следующего месяца**':
        tme[mid] = next_month()
    else:
        text = text.split()
        if len(text) == 1:
            text = text[0].split('.')
        try:
            for i in range(len(text)):
                text[i] = int(text[i])
            tme[mid] = text
        except Exception:
            logging.error('bank_limits_add3: Wrong format')
            users[mid] = prev_step(users[mid])
            step = users[mid]
            event[mid] = 0
            bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])
            return
    logging.info('bank_limits_add3: Got')
    if tme[mid][0] < 1 or tme[mid][0] > 31 or tme[mid][1] < 1 or tme[mid][1] > 12:
        logging.error('bank_limits_add3: Wrong format')
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        return
    tm = tday()
    if (tm[2] > tme[mid][2]) or (tm[2] == tme[mid][2] and tm[1] > tme[mid][1]) or (tm[2] == tme[mid][2] and tm[1] == tme[mid][1] and tm[0] > tme[mid][0]):
        logging.error('bank_limits_add3: Wrong format')
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Нельзя вводить даты в прошлом", reply_markup = MUP[step])
        return
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    markup1.row('1 неделя')
    markup1.row('1 месяц')
    sent = bot.send_message(mid, "Напишите период (Формат: *число* *дней/недель/месяцев/лет*)", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_limits_add4)

# Добавление лимита 4/4
# Вход: сообщение (длительность)
# Выход: -
def bank_limits_add4(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    if text == '**отмена**':
        logging.info('bank_limits_add4: Cancelled')
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        vr.pop(mid)
        return
    logging.info('bank_limits_add4: Getting duration')
    text = text.split()
    if len(text) != 2:
        logging.error('bank_limits_add4: Wrong format')
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        return
    if 'дн' in text[1]:
        text[1] = 'day'
    elif 'недел' in text[1]:
        text[1] = 'week'
    elif 'месяц' in text[1]:
        text[1] = 'month'
    elif 'год' in text[1] or 'лет' in text[1]:
        text[1] = 'year'
    else:
        logging.error('bank_limits_add4: Wrong format')
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        return
    try:
        text[0] = int(text[0])
    except Exception:
        logging.error('bank_limits_add4: Wrong format')
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        return
    if text[0] < 1:
        logging.error('bank_limits_add4: Wrong format')
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[step])
        return
    if text[1] == 'week':
        text[0] *= 7
    if text[1] == 'week' or text[1] == 'day':
        tme[mid] = day_plus(text[0], b = tme[mid])
    elif text[1] == 'year':
        tme[mid][2] += text[0]
    elif text[1] == 'month':
        tme[mid][1] += text[0]
        while tme[mid][1] > 12:
            tme[mid][2] += 1
            tme[mid][1] -= 12
    if text[1] == 'week':
        text[0] //= 7
    logging.info('bank_limits_add4 [%s]: Got', login)

    logging.info('bank_limits_add4: Connecting to user data base')
    conn = sqlite3.connect(user_db(login))
    logging.info('bank_limits_add4: Connected')
    cur = conn.cursor()
    cur.execute("SELECT login FROM limits WHERE cat = '%s' AND count = '%d' AND dur = '%s'"%(vr[mid][0], text[0], text[1]))
    for row in cur:
        logging.error('bank_limits_add4: This limit is already exist')
        users[mid] = prev_step(users[mid])
        event[mid] = 0
        step = users[mid]
        bot.send_message(mid, "Лимит с такими параметрами уже существует", reply_markup = MUP[step])
        cur.close()
        conn.close()
        return
    if text[1] == 'day' or text[1] == 'week':
        tlim = vr[mid][1] / text[0]
        if text[1] == 'week':
            tlim /= 7
    else:
        tlim = 0
    logging.info('bank_limits_add4: Inserting data')
    cur.execute("INSERT INTO limits (login, cat, count, dur, tlim, sum, lim_sum, f_year, f_month, f_day) VALUES ('%s', '%s', '%d', '%s', '%f', '%f', '%f', '%d', '%d', '%d')"%(login, vr[mid][0], text[0], text[1], round(tlim, 2), 0, round(vr[mid][1], 2), tme[mid][2], tme[mid][1], tme[mid][0]))
    logging.info('bank_limits_add4: Inserted')
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    event[mid] = 0
    step = users[mid]
    bot.send_message(mid, "Лимит добавлен добавлен", reply_markup = MUP[step])

# Удаление лимита
# Вход: сообщение (категория, продолжительность)
# Выход: -
def bank_limits_del(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    users[mid] = prev_step(users[mid])
    event[mid] = 0
    step = users[mid]
    if text == '**отмена**':
        vr.pop(mid)
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    text.replace('*все категории*', '#all')
    text = text.split(', ')
    text = [text[0]] + text[1].split()
    if text[0] == '*все категории*':
        text[0] = '#all'
    if text not in vr[mid]:
        vr.pop(mid)
        bot.send_message(mid, "Неправильный ввод", reply_markup = MUP[step])
        return
    if 'дн' in text[2]:
        text[2] = 'day'
    elif 'недел' in text[2]:
        text[2] = 'week'
    elif 'месяц' in text[2]:
        text[2] = 'month'
    elif 'год' in text[2] or 'лет' in text[2]:
        text[2] = 'year'
    vr.pop(mid)
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT cat, count, dur from limits")
    cur.execute("DELETE FROM limits WHERE cat = ? AND count = ? AND dur = ?", [(text[0]), (int(text[1])), (text[2])])
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Удаление выполнено", reply_markup = MUP[step])

# Перевод 1/3
# Вход: сообщение
# Выход: -
def bank_tr1(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    step = users[mid]
    
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text not in vr[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Такого счета нет, либо на данном счете нет средств", reply_markup = MUP[step])
        return
    vr2[mid] = vr2[mid][vr[mid].index(text)]
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('**Отмена**')
    for i in vr1[mid]:
        if i != vr[mid]:
            markup1.row(i)            
    event[mid] = 1
    sent = bot.send_message(mid, 'Выберите счет, на который хотите перевести средства', reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_tr2)

# Перевод 2/3
# Вход: сообщение
# Выход: -
def bank_tr2(message):
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    step = users[mid]
    
    if text == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text not in vr1[mid]:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[step])
        return
    vr3[mid] = vr3[mid][vr1[mid].index(text)]
    vr1[mid] = text
    event[mid] = 1
    sent = bot.send_message(mid, 'Напишите сумму перевода', reply_markup = markupCanc)
    bot.register_next_step_handler(sent, bank_tr3)

# Перевод 3/3
# Вход: сообщение
# Выход: -
def bank_tr3(message): #сумма перевода
    mid = message.chat.id
    text = message.text.lower()
    login = kods[mid]
    step = users[mid]
    
    if text.lower() == '**отмена**':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
        return
    if text[0] == '-':
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])	
        return
    try:
        text = round(float(check_num(text)),2)
    except Exception:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[step])	
        return
    vr2[mid] -= text
    vr3[mid] += text
    if vr2[mid] < 0:
        users[mid] = prev_step(users[mid])
        step = users[mid]
        event[mid] = 0
        bot.send_message(mid, "У вас нет столько средств", reply_markup = MUP[step])	
        return
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("UPDATE bank SET bal = '%f' WHERE name = '%s'"%(vr2[mid],vr[mid]))
    cur.execute("UPDATE bank SET bal = '%f' WHERE name = '%s'"%(vr3[mid],vr1[mid]))
    conn.commit()
    cur.close()
    conn.close()
    users[mid] = prev_step(users[mid])
    step = users[mid]
    event[mid] = 0
    bot.send_message(mid, "Перевод выполнен\nБаланс счета " + vr[mid] + ': ' + str(round(vr2[mid],2)) + 'р\nБаланс счета ' + vr1[mid] + ': ' + str(round(vr3[mid],2)) + 'р', reply_markup = MUP[step])

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    # Если сообщение из чата с ботом
    if call.message:
        mid = call.message.chat.id
        login = kods[mid]
        step = users[mid]

        if inline_mes.get(mid) == None:
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Данное сообщение уже устарело")
            return
        inline_mes.pop(mid)

        # Удаление счета
        if call.data == "bank_del_yes":
            conn = sqlite3.connect(user_db(login))
            cur = conn.cursor()
            cur.execute("DELETE FROM bank WHERE name = '%s'"%(vr[mid]))
            conn.commit()
            cur.close()
            conn.close()
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удвление выполнено")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])

        # Удаление счета (отмена)
        if call.data == "bank_del_no":
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])

        # Удаление операции
        if call.data == "bank_fin_del_yes":
            conn = sqlite3.connect(user_db(login))
            cur = conn.cursor()
            cur.execute("SELECT bal FROM bank WHERE name = '%s'"%(spend[mid]))
            for row in cur:
                bal = row[0]
            if catg[login] == 'spend':
                bal += vr3[mid]
                cur.execute("DELETE FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
            elif catg[login] == 'fin':
                bal -= vr3[mid]
                if bal < 0:
                    vr.pop(mid)
                    vr1.pop(mid)
                    vr2.pop(mid)
                    tme.pop(mid)
                    event[mid] = 0
                    bot.send_message(mid, "Удаление невозможно, так как баланс станет отрицательным", reply_markup = MUP[step])
                    cur.close()
                    conn.close()
                    return
                cur.execute("DELETE FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
            cur.execute("UPDATE bank SET bal = '%f' WHERE name = '%s'"%(bal,spend[mid]))
            conn.commit()
            cur.close()
            conn.close()
            if catg[login] == 'spend':
                stroka = fin_add_limits(mid, vr[mid], -vr3[mid], tme[mid])
            vr.pop(mid)
            vr1.pop(mid)
            vr2.pop(mid)
            tme.pop(mid)
            event[mid] = 0
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удаление выполнено, баланс счета " + spend[mid] + ': ' + str(round(bal)))
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])

        # Удаление операции (отмена)
        if call.data == "bank_fin_del_no":
            vr.pop(mid)
            vr1.pop(mid)
            vr2.pop(mid)
            tme.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])

        # Смена категории операции
        if call.data == "bank_fin_chngcat":
            users[mid] += '_edit'
            event[mid] = 1
            vr1[mid] = []
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('**Отмена**')
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Выберите новую категорию")
            categs, kol = get_categs(login, catg[login])
            for elem in categs:
                markup1.row(elem)
                vr1[mid].append(elem)
            sent = bot.send_message(mid, "Список категорий ниже", reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_edit4)

        # Смена суммы операции
        if call.data == "bank_fin_chngsum":
            users[mid] += '_edit'
            event[mid] = 1
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Не забудьте, что у вас изменится и счет")
            sent = bot.send_message(mid, "Напишите новую сумму", reply_markup = markupCanc)
            bot.register_next_step_handler(sent, bank_fin_edit5)

        # Добавление фразы-вопроса и фразы-ответа
        if call.data == "alice_add_yes":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо")
            users[mid] += '_aliceadd'
            sent = bot.send_message(mid, "Напишите фразу-вопрос (без знаков препинания)", reply_markup = markupCanc)
            event[mid] = 1
            bot.register_next_step_handler(sent, alice_add1)

        # Добавление фразы-вопроса и фразы-ответа (отмена)
        if call.data == "alice_add_no":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Ладно. Чтобы добавить фразы напишите еще раз /alice")
            bot.send_message(mid, 'Используйте команду /help для помощи', reply_markup = MUP[step])

        # Аутентификация диалога
        if call.data == "alice_auth_yes":
            conn = sqlite3.connect(user_db(login))
            cur = conn.cursor()
            cur.execute("DELETE FROM alice WHERE id = '%s'"%(vr[mid]))
            conn.commit()
            cur.close()
            conn.close()
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("INSERT INTO zalog_alice (id,login) VALUES ('%s','%s')"%(vr[mid],login))
            conn.commit()
            cur.close()
            conn.close()
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Добавление выполнено выполнено")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
            event[mid] = 0

        # Аутентификация диалога (отмена)
        if call.data == "alice_auth_no":
            conn = sqlite3.connect(user_db(login))
            cur = conn.cursor()
            cur.execute("DELETE FROM alice WHERE id = '%s'"%(vr[mid]))
            conn.commit()
            cur.close()
            conn.close()
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удаление выполнено")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[login])
            event[mid] = 0

        # Деаутентификация диалога 
        if call.data == "alice_deauth_yes":
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("DELETE FROM zalog_alice WHERE login = '%s'"%(login))
            conn.commit()
            cur.close()
            conn.close()
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удаление сессий выполнено")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
            event[mid] = 0

        # Деаутентификация диалога (отмена)
        if call.data == "alice_deauth_no":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, сессии работают")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[step])
            event[mid] = 0

        # Создание нового счета
        if call.data == "bank_add":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Начинаем создание счета...")
            users[mid] = 'main'
            new_bank(mid)

        # Смена счета
        if call.data == "bank_change":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Смена счета...")
            markup1 = types.ReplyKeyboardMarkup()
            vr[mid] = []
            banks, kol, osum = get_banks(login)
            for elem in banks:
                markup1.row(elem[0])
                vr[mid].append(elem[0])
            vr1[mid] = prev_step(vr1[mid])
            sent = bot.send_message(mid, 'Выберите счет', reply_markup = markup1)
            event[mid] = 1
            bot.register_next_step_handler(sent, bank_fin_change)

        # Выбор всех счетов
        if call.data == "bank_allspend":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Выбраны все счета")
            spend[mid] = 'все'

        # Сброс данных
        if call.data == "reset_yes":
            reset_data(login, vr[mid])
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Сброс данных выполнен")

        # Сброс данных (отмена)
        if call.data == "reset_no":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Отмена сброса данных")

        # Удаление аккаунта
        if call.data == "delete_yes":
            keybGR = types.InlineKeyboardMarkup()
            cbtn1 = types.InlineKeyboardButton(text="Удалить", callback_data="delete_yes_ac")
            cbtn2 = types.InlineKeyboardButton(text="Отмена", callback_data="delete_no")
            keybGR.add(cbtn2)
            keybGR.add(cbtn1)
            inline_mes[mid] = call.message.message_id
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = 'Если вы подтверждаете удаление аккаунта, нажмите кнопку "Удалить". Отмена данной операции невозможна', reply_markup = keybGR)

        if call.data == "delete_yes_ac":
            delete_data(login, mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удаление выполнено")
            kods.pop(mid)
            logins.pop(logins.index(login))
            users[mid] = 'mainUS'
            step = users[mid]
            bot.send_message(mid, 'Будем благодарны, если вы оставите отзыв о работе бота здесь: @m3prod', reply_markup = MUP[step])

        # Удаление аккаунта (отмена)
        if call.data == 'delete_no':
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Отмена удаления аккаунта")

        # Короткое добавление расхода/дохода
        if call.data == 'short_add_yes':
            categ, text, sm = vr.pop(mid)
            text += '%' + str(nums())
            conn = sqlite3.connect(user_db(login))
            cur = conn.cursor()
            cur.execute("SELECT bal FROM bank WHERE name = ?", [(spend[mid])])
            for row in cur:
                bal = round(float(row[0]),2)
            if catg[login] == 'spend':
                bal -= sm
            elif catg[login] == 'fin':
                bal += sm
            if bal < 0:
                bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "У вас недостаточно средств для совершения операции")
                cur.close()
                conn.close()
                return
            tm = tday()
            cur.execute("UPDATE bank SET bal = ? WHERE name = ?", [(bal),(spend[mid])])
            stroka = ''
            if catg[login] == 'spend':
                cur.execute("INSERT INTO spend (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(login,tm[2],tm[1],tm[0],categ,spend[mid],text.lower(),sm))
            elif catg[login] == 'fin':
                cur.execute("INSERT INTO inc (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%f')"%(login,tm[2],tm[1],tm[0],categ,spend[mid],text.lower(),sm))
            conn.commit()
            cur.close()
            conn.close()
            if catg[login] == 'spend':
                stroka = fin_add_limits(mid, categ, sm, tm)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Операция выполнена\nБаланс счета " + spend[mid] + ': ' + str(round(bal,2)) + '\n' + stroka)

        # Короткое добавление расхода/дохода (отмена)
        if call.data == 'short_add_no':
            vr.pop(mid)
            vr1.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Отменено")

        # Короткое добавление расхода/дохода, смена счета 1
        if call.data == 'short_add_changebank':
            banks, kol, osum = get_banks(login)
            if kol == 1:
                bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = 'У вас всего 1 счет\n' + call.message.text, reply_markup = vr2[mid])
                inline_mes[mid] = call.message.message_id
                return
            keybGR = types.InlineKeyboardMarkup()
            vr3[mid] = []
            for elem in banks:
                if elem[0] != spend[mid]:
                    vr3[mid].append(elem[0])
                    cbtn = types.InlineKeyboardButton(text=elem[0], callback_data="short_add_changebank_" + str(len(vr3[mid]) - 1))
                    keybGR.add(cbtn)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = 'Выберите счет', reply_markup = keybGR)
            inline_mes[mid] = call.message.message_id

        # Короткое добавление расхода/дохода, смена счета
        if 'short_add_changebank_' in call.data:
            logging.info('INLINE short_add_changebank_: Getting num')
            num = call.data.split('_')
            num = int(num.pop())
            logging.info('INLINE short_add_changebank_: Got')
            spend[mid] = vr3[mid][num]
            sm = vr[mid][2]
            text = vr[mid][1]
            categ = vr[mid][0]
            logging.info('INLINE short_add_changebank_: Creating string')
            if catg[login] == 'spend':
                stroka = 'Добавление расхода:\n'
            elif catg[login] == 'fin':
                stroka = 'Добавление дохода:\n'
            stroka += text
            if text != '':
                stroka += ' '
            stroka += str(sm) + 'р\n'
            stroka += 'Категория: ' + categ + '\n'
            stroka += 'Счет: ' + spend[mid] + '\n'
            stroka += 'Добавляем?'
            logging.info('INLINE short_add_changebank_: Created')
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = stroka, reply_markup = vr2[mid])
            inline_mes[mid] = call.message.message_id

        # Короткое добавление расхода/дохода, смена категории
        if 'short_add_changecat_' in call.data:
            num = call.data.split('_')
            num = int(num.pop())
            categ = vr1[mid][num]
            vr[mid][0] = categ
            sm = vr[mid][2]
            text = vr[mid][1]
            keybGR = types.InlineKeyboardMarkup()
            for i, elem in enumerate(vr1[mid]):
                if elem != categ:
                    cbtn = types.InlineKeyboardButton(text=elem, callback_data="short_add_changecat_" + str(i))
                    keybGR.add(cbtn)
            cbtn = types.InlineKeyboardButton(text="Поменять счет", callback_data="short_add_changebank")
            keybGR.add(cbtn)
            cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="short_add_yes")
            cbtn2 = types.InlineKeyboardButton(text="Отмена", callback_data="short_add_no")
            keybGR.add(cbtn1, cbtn2)
            if catg[login] == 'spend':
                stroka = 'Добавление расхода:\n'
            elif catg[login] == 'fin':
                stroka = 'Добавление дохода:\n'
            stroka += text
            if text != '':
                stroka += ' '
            stroka += str(sm) + 'р\n'
            stroka += 'Категория: ' + categ + '\n'
            stroka += 'Счет: ' + spend[mid] + '\n'
            stroka += 'Добавляем?'
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = stroka, reply_markup = keybGR)
            inline_mes[mid] = call.message.message_id
            vr2[mid] = keybGR

        # Короткое добавление расхода/дохода, смена шаблона
        if 'short_add_changetempl_' in call.data:
            logging.info('INLINE short_add_changetempl_: Getting num')
            num = call.data.split('_')
            num = int(num.pop())
            logging.info('INLINE short_add_changetempl_: Got')
            vr[mid] = vr1[mid][num][:3]
            sm = vr[mid][2]
            text = vr[mid][1]
            categ = vr[mid][0]
            catg[login] =  vr1[mid][num][3]
            keybGR = types.InlineKeyboardMarkup()
            for i, elem in enumerate(vr1[mid]):
                if elem[:3] != vr[mid]:
                    cbtn = types.InlineKeyboardButton(text=elem[1], callback_data="short_add_changetempl_" + str(i))
                    keybGR.add(cbtn)
            cbtn = types.InlineKeyboardButton(text="Поменять счет", callback_data="short_add_changebank")
            keybGR.add(cbtn)
            cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="short_add_yes")
            cbtn2 = types.InlineKeyboardButton(text="Отмена", callback_data="short_add_no")
            keybGR.add(cbtn1, cbtn2)
            if catg[login] == 'spend':
                stroka = 'Добавление расхода:\n'
            elif catg[login] == 'fin':
                stroka = 'Добавление дохода:\n'
            stroka += text
            if text != '':
                stroka += ' '
            stroka += str(sm) + 'р\n'
            stroka += 'Категория: ' + categ + '\n'
            stroka += 'Счет: ' + spend[mid] + '\n'
            stroka += 'Добавляем?'
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = stroka, reply_markup = keybGR)
            inline_mes[mid] = call.message.message_id
            vr2[mid] = keybGR

        # Добавление тестера
        if 'tester_add_' in call.data:
            tid = call.data.split('_')
            tid = int(tid.pop())
            if tid not in tester_ids:
                tester_ids.append(tid)
                bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = 'Тестер добавлен')         
            else:
                bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = 'Данный участник уже есть в списке')

        # Удаление тестера
        if 'tester_delete_' in call.data:
            tid = call.data.split('_')
            tid = int(tid.pop())
            if tid not in tester_ids:
                bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = 'Тестер уже удален')         
            else:
                tester_ids.pop(tester_ids.index(tid))
                bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = 'Удаление выполнено')
            
# WEBHOOK_START

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

# WEBHOOK_FINISH
