# -*- coding: utf-8 -*-
import telebot
import sqlite3
from telebot import types
import time

"""
инлайн кнопка отмена
общий назад
Долги из счетов
"""

__version__ = '0.4.0.7 Beta'
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

3.0.0:
Теперь этот бот будет и вашей бухгалтерией. Для начала немного перенесем раздел долги
3.0.1:
Исправлено:
Удаление групп
Добавлено:
Возможность создавать счета
3.0.2:
Возможность удалять счета

4.0.1:
Появились расходы:
смена счета, с которым работаешь
добавлены категории
добалена возможность просмотра истории операций
4.0.2:
Оптимизирована работа со временем в истории расходов
4.0.3:
Добавлена возможность добавлять расходы
4.0.4:
Теперь возможно добавлять расходы за любую дату
4.0.5:
Теперь можно удалять расходы и доходы из истории
4.0.6:
В долгах добавлены даты
Добавлена общая сумма расходов/доходов за период
Добавлены переводы
4.0.7:
Теперь расходы связанны со счетами
"""

__desc__ = """
Данный бот был создан для того, чтобы вы могли вести учет своих расходов и доходов
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
vr1 = dict() #^2
vr2 = dict()
vr3 = dict()
vr4 = dict()
spend = dict() #счет в расходах
tme = dict() #время для записи расходов
month = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
mdays = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}

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
markup.row('Мой кошелек','Мои долги')
markup.row('Регистрация')
markup.row('Смена пароля', 'О боте')

markupDebt = types.ReplyKeyboardMarkup()
markupDebt.row('Мои долги','Мои группы')
markupDebt.row('Добавить долг')
markupDebt.row('Редактировать')
markupDebt.row('Назад')

markupBank = types.ReplyKeyboardMarkup()
markupBank.row('Мои счета','Перевод')
markupBank.row('Расходы','Доходы')
markupBank.row('Новый счет','Удалить счет')
markupBank.row('Назад')

markupSpend = types.ReplyKeyboardMarkup()
markupSpend.row('Расходы за период')
markupSpend.row('Новый расход','Удалить расход')
markupSpend.row('Поменять счет','Категории')
markupSpend.row('Назад')

markupFin = types.ReplyKeyboardMarkup()
markupFin.row('Доходы за период')
markupFin.row('Новый доход','Удалить доход')
markupFin.row('Поменять счет','Категории')
markupFin.row('Назад')

markupCat = types.ReplyKeyboardMarkup()
markupCat.row('Добавить','Удалить')
markupCat.row('Категории')
markupCat.row('Назад')

markupSZ = types.ReplyKeyboardMarkup()
markupSZ.row('ОТМЕНА')
markupSZ.row('Сегодня')
markupSZ.row('Вчера')
markupSZ.row('Этот месяц')
markupSZ.row('Прошлый месяц')

markupCanc = types.ReplyKeyboardMarkup()
markupCanc.row('ОТМЕНА')

markupG = types.ReplyKeyboardMarkup()
markupG.row('Меню')
markupG.row('Удалить группу')
markupG.row('Добавить долг')

MUP = {'main':markup,'main_debt':markupDebt,'main_bank':markupBank,'main_bank_fin_cat':markupCat,'main_bank_spend_cat':markupCat,'main_bank_spend':markupSpend,'main_debt_group':markupG,'main_bank_fin_his':markupSZ,'main_bank_spend_his':markupSZ,'main_bank_fin':markupFin}

@bot.message_handler(commands=['errors'])
def errors1(message):
    mid = message.chat.id
    users[mid] = 'main_errors'
    sent = bot.send_message(mid, 'Введите кодовое слово:')
    bot.register_next_step_handler(sent, errors2)

def errors2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
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
        sent = bot.send_message(mid, 'ERROR: ' + str(ERROR) + '\n\nLOGS:\n' + LOGS + '\n\nЗапустить бота?', reply_markup = markup1)
        users[mid] = 'main_errors'
        bot.register_next_step_handler(sent, errors3)
    elif text == code and ERROR == 0:
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('ДА')
        markup1.row('НЕТ')
        sent = bot.send_message(mid, 'Остановить бота?', reply_markup = markup1)
        users[mid] = 'main_errors'
        bot.register_next_step_handler(sent, errors4)
    else:
        bot.send_message(mid, 'Кодовое слово не верно')

def errors3(message):
    global ERROR
    mid = message.chat.id
    text = message.text
    text = text.upper()
    users[mid] = prev_step(users[mid])
    if text == 'ДА':
        ERROR = 0
        bot.send_message(mid, 'Бот запущен', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Бот не запущен', reply_markup = MUP[users[mid]])

def errors4(message):
    global ERROR
    mid = message.chat.id
    text = message.text
    text = text.upper()
    users[mid] = prev_step(users[mid])
    if text == 'ДА':
        ERROR = 1
        bot.send_message(mid, 'Бот остановлен', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Бот работает', reply_markup = MUP[users[mid]])

@bot.message_handler(commands=['start'])
def start(message):
    mid = message.chat.id
    if (users.get(mid) == None) or (users.get(mid) == 'main'):
        users[mid] = 'main'
        bot.send_message(mid , __desc__ + '\nВерсия бота: ' + str(__version__) + '\n\nСписок изменений:' + __chng__, reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid , __desc__ + '\nВерсия бота: ' + str(__version__) + '\n\nСписок изменений:' + __chng__)

@bot.message_handler(content_types=['text'])
def main(message):
    mid = message.chat.id
    text = message.text
    text = text.upper()
    if ERROR != 0:
        bot.send_message(mid, 'Проводятся технические работы')
        return
    if((users.get(mid) == None) or (users[mid] == 'main')):
        users[mid] = 'main'
        if text == 'РЕГИСТРАЦИЯ':
            if kods.get(mid) == None:
                sent = bot.send_message(mid, 'Пожалуйста, введите новый логин и пароль через пробел или в два разных сообщения:')
                users[mid] = 'main_reg'
                bot.register_next_step_handler(sent, reg1)
            else:
                bot.send_message(mid, 'Вы уже авторизированны')
                
        elif text == 'ВХОД':
            if kods.get(mid) == None:
                sent = bot.send_message(mid, 'Пожалуйста, введите свой логин и пароль через пробел или в два разных сообщения:')
                users[mid] = 'main_login'
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
                
        elif text == 'О БОТЕ':
            start(message)

        elif text == 'СМЕНА ПАРОЛЯ':
            if kods.get(mid) == None:
                bot.send_message(mid, 'Сначала вам нужно авторизоваться')
            else:
                sent = bot.send_message(mid, 'Введите старый пароль')
                users[mid] = 'main_changepass' 
                bot.register_next_step_handler(sent, chngpass1)

        elif text == 'МОИ ДОЛГИ':
            if kods.get(mid) == None:
                bot.send_message(mid, 'Сначала вам нужно авторизоваться')
            else:
                users[mid] = 'main_debt'
                watch_debts(message)

        elif text == 'МОЙ КОШЕЛЕК' or text == 'МОЙ КОШЕЛЁК':
            if kods.get(mid) == None:
                bot.send_message(mid, 'Сначала вам нужно авторизоваться')
            else:
                users[mid] = 'main_bank'
                watch_bank(message)

    elif users[mid] == 'main_debt':

        if text == 'ДОБАВИТЬ ДОЛГ':
            vr[mid] = []
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите счет, с которого вы даете долг', reply_markup = markup1)
            users[mid] = 'main_debt_add'
            bot.register_next_step_handler(sent, addcredit1)

        elif text == 'МОИ ДОЛГИ':
            watch_debts(message)

        elif text == 'РЕДАКТИРОВАТЬ':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cred FROM credits WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Введите фамилию и имя должника, у которого хотите изменить долг или ОТМЕНА', reply_markup = markup1)
            users[mid] = 'main_debt_edit'
            bot.register_next_step_handler(sent, edit1)

        elif text == 'МОИ ГРУППЫ':
            stroka = ""
            stroka += 'Ваши группы:\n'
            markupGR = types.ReplyKeyboardMarkup()
            markupGR.row('Добавить группу')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            i = 1
            cur.execute("SELECT name, kol FROM groups WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                stroka += str(i) + ') ' + row[0] + '\nКоличество людей: ' + str(row[1]) + '\n\n'
                markupGR.row(row[0])
                i = i + 1
            markupGR.row('Назад')
            cur.close()
            conn.close()
            if i == 1:
                stroka = 'У вас нет групп'
            sent = bot.send_message(mid, stroka, reply_markup = markupGR)
            users[mid] = 'main_debt_group'
            bot.register_next_step_handler(sent, group1)

        elif text == 'НАЗАД':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

    elif users[mid] == 'main_bank':

        if text == 'НАЗАД':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == 'МОИ СЧЕТА':
            watch_bank(message)

        elif text == 'ДОХОДЫ':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            conn = sqlite3.connect(db)
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
            bank_fin(mid)
            
        elif text == 'РАСХОДЫ':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            conn = sqlite3.connect(db)
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
            bank_spend(mid)

        elif text == 'НОВЫЙ СЧЕТ':
            new_bank(mid)

        elif text == 'УДАЛИТЬ СЧЕТ':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            conn = sqlite3.connect(db)
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
            sent = bot.send_message(mid, 'Выберите счет, который хотите удалить или ОТМЕНА', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_del)

        elif text == 'ПЕРЕВОД':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            vr[mid] = []
            vr1[mid] = []
            vr2[mid] = []
            vr3[mid] = []
            vr4[mid] = []
            cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                vr1[mid].append(row[0].upper())
                vr4[mid].append(row[0])
                vr3[mid].append(row[1])
                if row[1] > 0:		
                    markup1.row(row[0])
                    vr[mid].append(row[0].upper())
                    vr2[mid].append(row[1])
            cur.close()
            conn.close()
            if kol < 2:
                bot.send_message(mid, 'У вас недостаточно счетов', reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_tr'
            sent = bot.send_message(mid, 'Выберите счет, с которого хотите перевести средства (показаны счета с положительным балансом)', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_tr1)

    elif users[mid] == 'main_bank_spend':

        if text == 'НАЗАД':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == 'НОВЫЙ РАСХОД':
            if spend[mid] == 'ВСЕ':
                bot.send_message(mid, "Сначала поменяйте счет", reply_markup = MUP[users[mid]])
                return
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий, чтобы добавить расход", reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_spend_add'
            sent = bot.send_message(mid, "Выберите категорию расхода\nТекущий счет: " + spend[mid], reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_spend_add1)
            
        elif text == 'РАСХОДЫ ЗА ПЕРИОД':
            users[mid] = 'main_bank_spend_his'
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ВСЕ')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите категорию', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_spend_his1)
                        
        elif text == 'ПОМЕНЯТЬ СЧЕТ':
            users[mid] = 'main_bank_spend_change'
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ВСЕ')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
            vr[mid] = []
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите другой счет', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_change)

        elif text == 'КАТЕГОРИИ':
            users[mid] = 'main_bank_spend_cat'
            watch_cat(mid)

        elif text == 'УДАЛИТЬ РАСХОД':
            if spend[mid] == 'ВСЕ':
                bot.send_message(mid, "Сначала поменяйте счет", reply_markup = MUP[users[mid]])
                return
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_spend_del'
            sent = bot.send_message(mid, "Выберите категорию расхода, который хотите удалить\nТекущий счет: " + spend[mid], reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_spend_del1)

    elif users[mid] == 'main_bank_spend_cat':

        if text == 'НАЗАД':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == 'ДОБАВИТЬ':
            users[mid] = 'main_bank_spend_cat_add'
            sent = bot.send_message(mid, 'Введите название новой категории', reply_markup = markupCanc)
            bot.register_next_step_handler(sent, bank_spend_cat_add)

        elif text == 'УДАЛИТЬ':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
                kol += 1
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, 'У вас нет категорий', reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_spend_cat_del'
            sent = bot.send_message(mid, 'Внимание! Пока в истории есть операции с этой категорией, удаление невозможно.\nВыберите категорию, которую хотите удалить', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_spend_cat_del)

        elif text == 'КАТЕГОРИИ':
            watch_cat(mid)

    elif users[mid] == 'main_bank_fin':

        if text == 'НАЗАД':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == 'НОВЫЙ ДОХОД':
            if spend[mid] == 'ВСЕ':
                bot.send_message(mid, "Сначала поменяйте счет", reply_markup = MUP[users[mid]])
                return
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий, чтобы добавить доход", reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_fin_add'
            sent = bot.send_message(mid, "Выберите категорию расхода\nТекущий счет: " + spend[mid], reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_add1)
            
        elif text == 'ДОХОДЫ ЗА ПЕРИОД':
            users[mid] = 'main_bank_fin_his'
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ВСЕ')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите категорию', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_his1)
                        
        elif text == 'ПОМЕНЯТЬ СЧЕТ':
            users[mid] = 'main_bank_fin_change'
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ВСЕ')
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
            vr[mid] = []
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            sent = bot.send_message(mid, 'Выберите другой счет', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_change)

        elif text == 'КАТЕГОРИИ':
            users[mid] = 'main_bank_fin_cat'
            watch_fcat(mid)

        elif text == 'УДАЛИТЬ ДОХОД':
            if spend[mid] == 'ВСЕ':
                bot.send_message(mid, "Сначала поменяйте счет", reply_markup = MUP[users[mid]])
                return
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                kol += 1
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, "У вас нет категорий", reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_fin_del'
            sent = bot.send_message(mid, "Выберите категорию дохода, который хотите удалить\nТекущий счет: " + spend[mid], reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_del1)

    elif users[mid] == 'main_bank_fin_cat':

        if text == 'НАЗАД':
            users[mid] = prev_step(users[mid])
            bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])

        elif text == 'ДОБАВИТЬ':
            users[mid] = 'main_bank_fin_cat_add'
            sent = bot.send_message(mid, 'Введите название новой категории', reply_markup = markupCanc)
            bot.register_next_step_handler(sent, bank_fin_cat_add)

        elif text == 'УДАЛИТЬ':
            kol = 0
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            vr[mid] = []
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                markup1.row(row[0])
                vr[mid].append(row[0].upper())
                kol += 1
            cur.close()
            conn.close()
            if kol == 0:
                bot.send_message(mid, 'У вас нет категорий', reply_markup = MUP[users[mid]])
                return
            users[mid] = 'main_bank_fin_cat_del'
            sent = bot.send_message(mid, 'Внимание! Пока в истории есть операции с этой категорией, удаление невозможно.\nВыберите категорию, которую хотите удалить', reply_markup = markup1)
            bot.register_next_step_handler(sent, bank_fin_cat_del)

        elif text == 'КАТЕГОРИИ':
            watch_fcat(mid)

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
    users[mid] = prev_step(users[mid])
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
                users[mid] = 'main_reg'
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
    logins.append(log)
    bot.send_message(mid, 'Регистрация успешно пройдена!')

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
                users[mid] = 'main_login'
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
                    bot.send_message(mid, 'Авторизация пройдена!', reply_markup = MUP[users[mid]])
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
                bot.send_message(mid, 'Авторизация пройдена!', reply_markup = MUP[users[mid]])
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

def chngpass2(message):
    text = message.text
    users[mid] = prev_step(users[mid])
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE users SET password = '%s' WHERE login = '%s'"%(text,kods[mid]))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Пароль успешно изменен на ' + text)

def addcredit1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, 'Такого счета нет', reply_markup = MUP[users[mid]])
        return
    vr[mid] = text
    sent = bot.send_message(mid, 'Введите фамилию, имя и размер долга через пробел', reply_markup = markupCanc)
    users[mid] = 'main_debt_add'
    bot.register_next_step_handler(sent, addcredit2)
    
    

def addcredit2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text != 'ОТМЕНА':
        try:
            fam, im, dolg = text.split()
            dolg = int(dolg)
            dolg = str(dolg)
            fam, im = fam + ' ' + im, im + ' ' + fam
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
            return
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT cred, sz FROM credits WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            if (row[0] == fam) or (row[0] == im):
                bot.send_message(mid, 'Данный участник уже есть в базе. Пожалуйста, воспользуйтесь командой РЕДАКТИРОВАТЬ для изменения размера долга', reply_markup = MUP[users[mid]])
                cur.close()
                conn.close()
                return
        cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],vr[mid]))
        for row in cur:
            if row[0] < int(dolg):
                bot.send_message(mid, 'У вас нет столько денег', reply_markup = MUP[users[mid]])
                cur.close()
                conn.close()
                return
            sz = row[0]
        sz -= int(dolg)
        cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(sz,kods[mid],vr[mid]))
        tme[mid] = stday()
        cur.execute("INSERT INTO credits (login,cred,time,sz) VALUES ('%s','%s','%s','%d' )"%(kods[mid],fam,tme[mid],int(dolg)))
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(mid, 'Долг успешно добавлен', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

def edit1(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
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
    markup1.row('ОТМЕНА')
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        markup1.row(row[0])
        vr1[mid].append(row[0].upper())
    cur.close()
    conn.close()
    sent = bot.send_message(mid, 'Выберите счет, на который будут положены деньги', reply_markup = markup1)
    users[mid] = 'main_debt_edit'
    bot.register_next_step_handler(sent, edit2)
    

def edit2(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    if text.upper() not in vr1[mid]:
        bot.send_message(mid, 'Такого счета нет', reply_markup = MUP[users[mid]])
        return
    vr1[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT sz FROM credits WHERE cred = '%s' AND login = '%s'"%(vr[mid],kods[mid]))
    for row in cur:
        markup1.row(str(-row[0]))
    cur.close()
    conn.close()
    sent = bot.send_message(mid, 'Введите сумму', reply_markup = markup1)
    users[mid] = 'main_debt_edit'
    bot.register_next_step_handler(sent, edit3)

def edit3(message):
    text = message.text
    mid = message.chat.id
    users[mid] = prev_step(users[mid])
    if text != 'ОТМЕНА':
        fam, im = vr[mid].split()
        fam, im = fam + ' ' + im, im + ' ' + fam
        vr.pop(mid)
        try:
            text = int(text)
        except Exception:
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
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
            bot.send_message(mid, 'Участник не найден', reply_markup = MUP[users[mid]])
            return
        else:
            if kdk == 2:
                fam = im
            zn = zn + text
            conn = sqlite3.connect(db)
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
                cur.execute("UPDATE credits SET sz = '%d' WHERE login = '%s' AND cred = '%s'"%(zn,kods[mid],fam))
            cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],vr1[mid]))
            for row in cur:
                zn = row[0]
            zn -= text
            cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(zn,kods[mid],vr1[mid]))
            conn.commit()
            cur.close()
            conn.close()
            bot.send_message(mid, 'Операция успешно выполнена', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

def group1(message):
    text = message.text
    mid = message.chat.id
    text = text.upper()
    users[mid] = prev_step(users[mid])
    if text != 'НАЗАД':
        if text == 'ДОБАВИТЬ ГРУППУ':
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            sent =bot.send_message(mid, 'Введите название группы', reply_markup = markup1)
            users[mid] = 'main_debt_group_add'
            bot.register_next_step_handler(sent, group2)
        else:
            stroka = 'Такой группы нет'
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("SELECT name,kol,pep FROM groups WHERE login = '%s'"%(kods[mid]))
            for row in cur:
                if text.upper() == row[0].upper():
                    stroka = row[0] + '\nКоличество людей: ' + str(row[1]) + '\n' + row[2] + '\n\nВыберите действие'
                    users[mid] = 'main_debt_group'
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

def group2(message):
    text = message.text
    mid = message.chat.id
    text1 = text.upper()
    users[mid] = 'main_debt'
    if text != 'ОТМЕНА':
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM groups WHERE login = '%s'"%(kods[mid]))
        for row in cur:
            if text1 == row[0].upper():
                bot.send_message(mid, 'Данная группа уже есть', reply_markup = MUP[users[mid]])
                cur.close()
                conn.close()
                return
        cur.close()
        conn.close()
        vr[mid] = text
        markup1 = types.ReplyKeyboardMarkup()
        markup1.row('ОТМЕНА')
        sent = bot.send_message(mid, 'Введите участников группы (имя и фамилия через пробел) в разных строчках', reply_markup = markup1)
        users[mid] = 'main_debt_group_add'
        bot.register_next_step_handler(sent, group3)
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

def group3(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 'main_debt'
    if text != 'ОТМЕНА':
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
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("INSERT INTO groups (login,name,kol,pep) VALUES ('%s','%s','%d','%s')"%(kods[mid],vr[mid],i,text))
        conn.commit()
        cur.close()
        conn.close()
        vr.pop(mid)
        bot.send_message(mid, 'Группа создана', reply_markup = MUP[users[mid]])
    else:
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

def group4(message):
    text = message.text
    mid = message.chat.id
    users[mid] = 'main_debt'
    if text.upper() == 'МЕНЮ':
        bot.send_message(mid, 'Вот меню:', reply_markup = MUP[users[mid]])
    elif text.upper() == 'УДАЛИТЬ ГРУППУ':
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="gr_del_yes")
        cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="gr_del_no")
        keybGR.add(cbtn1, cbtn2)
        users[mid] = 'main_debt_group_del'
        bot.send_message(mid, 'Удалить группу "' + vr[mid] + '"?', reply_markup = keybGR)
    elif text.upper() == 'ДОБАВИТЬ ДОЛГ':
        keybGR = types.InlineKeyboardMarkup()
        cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="gr_yes")
        cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="gr_no")
        keybGR.add(cbtn1, cbtn2)
        users[mid] = 'main_debt_group_newdebt'
        bot.send_message(mid, 'Вы хотите добавить существующим учасиникам долг или оставить их долг таким же?', reply_markup = keybGR)  
    else:
        bot.send_message(mid, 'Я вас не понимаю. Вот меню:', reply_markup = MUP[users[mid]])

def group5(message):
    text = message.text
    mid = message.chat.id
    if text != 'ОТМЕНА':
        try:
            text = int(text)
        except Exception:
            users[mid] = 'main_debt'
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
            vr.pop(mid)
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
        users[mid] = 'main_debt'
        bot.send_message(mid, 'Операция выполнена', reply_markup = MUP[users[mid]])
    else:
        users[mid] = 'main_debt'
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

def group6(message):
    text = message.text
    mid = message.chat.id
    if text != 'ОТМЕНА':
        try:
            text = int(text)
        except Exception:
            users[mid] = 'main_debt'
            bot.send_message(mid, 'Некорректный ввод', reply_markup = MUP[users[mid]])
            vr.pop(mid)
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
        users[mid] = 'main_debt'
        bot.send_message(mid, 'Операция выполнена', reply_markup = MUP[users[mid]])
    else:
        users[mid] = 'main_debt'
        bot.send_message(mid, 'Отмена выполнена', reply_markup = MUP[users[mid]])

def watch_debts(message):
    mid = message.chat.id
    kol = 0
    osum = 0
    stroka = ""
    stroka += 'Ваши должники:\n'
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT cred, sz, time FROM credits WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        stroka += row[0] + ' ' + str(row[1]) + ' от ' + row[2] + '\n'
        kol = kol + 1
        osum += row[1]
    stroka += 'Всего человек: ' + str(kol) + '\nСумма: ' + str(osum)
    if kol == 0:
        stroka = 'У вас нет должников'
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])
    cur.close()
    conn.close()

def watch_bank(message):
    mid = message.chat.id
    kol = 0
    osum = 0
    stroka = ""
    stroka += 'Ваши счета:\n'
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT name, bal FROM bank WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        kol += 1
        stroka += str(kol) + ') ' + row[0] + '\nБаланс: ' + str(row[1]) + '\n\n'
        osum += row[1]
    cur.close()
    conn.close()
    stroka += 'Сумма: ' + str(osum)
    if kol == 0:
        stroka = 'У вас нет счетов'
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])

def new_bank(mid):
    sent = bot.send_message(mid, 'Введите название счета (до 32 символов)', reply_markup = markupCanc)
    users[mid] = 'main_bank_add'
    bot.register_next_step_handler(sent, bank_add)

def bank_add(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    if text.upper() == 'ВСЕ':
        bot.send_message(mid, 'Пожалуйста, выберите другое имя', reply_markup = MUP[users[mid]])
        return
    if len(text) > 32:
        bot.send_message(mid, 'Слишком длинное название', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT name FROM bank WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].upper() == text.upper():
            bot.send_message(mid, 'Данный счет уже есть в базе', reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    cur.close()
    conn.close()
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("INSERT INTO bank (login,name,bal) VALUES ('%s','%s',%d)"%(kods[mid],text,0))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, 'Счет добавлен', reply_markup = MUP[users[mid]])

def bank_del(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, 'Выберите действие', reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE name = '%s' AND login = '%s'"%(text,kods[mid]))
    kod = 1
    for row in cur:
        kod = 0
    cur.close()
    conn.close()
    if kod == 1:
        bot.send_message(mid, 'Данного счета не существует', reply_markup = MUP[users[mid]])
        return
    vr[mid] = text
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Да", callback_data="bank_del_yes")
    cbtn2 = types.InlineKeyboardButton(text="Нет", callback_data="bank_del_no")
    keybGR.add(cbtn1, cbtn2)
    bot.send_message(mid, 'Вы уверены, что хотите удалить счет? Его баланс будет удален!', reply_markup = keybGR)
    users[mid] = 'main_bank_del'

def bank_spend(mid):
    users[mid] = 'main_bank_spend'
    if spend.get(mid) == None:
        spend[mid] = 'ВСЕ'
    bot.send_message(mid, "Выберите действие. Текущий счет: " + spend[mid], reply_markup = MUP[users[mid]])

def bank_change(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ВСЕ':
        spend[mid] = 'ВСЕ'
        bot.send_message(mid, "Выбраны все счета", reply_markup = MUP[users[mid]])
    elif text.upper() not in vr[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[users[mid]])
    else:
        spend[mid] = text
        bot.send_message(mid, "Выбран счет: " + spend[mid], reply_markup = MUP[users[mid]])
    vr.pop(mid)

def watch_cat(mid):
    kol = 0
    stroka = ""
    stroka += 'Ваши категории:\n'
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        kol += 1
        stroka += str(kol) + ') ' + row[0] + '\n\n'
    cur.close()
    conn.close()
    if kol == 0:
        stroka = 'У вас нет категорий'
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])


def bank_spend_cat_add(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.upper() == 'ВСЕ':
        bot.send_message(mid, "Данное имя выбрать невозможно", reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT cat FROM cats WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].upper() == text.upper():
            bot.send_message(mid, "Данная категория уже существует", reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    cur.execute("INSERT INTO cats (login,cat) VALUES ('%s','%s')"%(kods[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Категория добавлена", reply_markup = MUP[users[mid]])

def bank_spend_cat_del(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT cat FROM spend WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].upper() == text.upper():
            bot.send_message(mid, "Данная категория используется, удаление невозможно", reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    cur.execute("DELETE FROM cats WHERE login = '%s' AND cat = '%s'"%(kods[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Удаление выполнено", reply_markup = MUP[users[mid]])

def bank_spend_his1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() not in vr[mid] and text.upper() != 'ВСЕ':
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    vr[mid] = text
    users[mid] = 'main_bank_spend_his'
    sent = bot.send_message(mid, 'Выберите период, расходы за который хотите посмотреть.\nДопустимый формат ввода: гггг; гггг мм; гггг мм дд; гггг мм гггг мм; гггг мм дд гггг мм дд (последние два подразумевают ввод момента С и момента ДО)', reply_markup = MUP[users[mid]])
    bot.register_next_step_handler(sent, bank_spend_his2)

def bank_spend_his2(message):
    mid = message.chat.id
    text = message.text
    text = text.upper()
    tm = tday()
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text == 'СЕГОДНЯ':
        sday = int(tm[0])
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])
        
    elif text == 'ВЧЕРА':
        tm = lday()
        sday = int(tm[0])
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])
        
    elif text == 'ЭТОТ МЕСЯЦ':
        sday = 1
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])

    elif text == 'ПРОШЛЫЙ МЕСЯЦ':
        tm = lmon()
        sday = 1
        fday = 31
        smon = int(tm[0])
        fmon = int(tm[0])
        syear = int(tm[1])
        fyear = int(tm[1])

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
            elif len(text) == 2:
                sday = 1
                fday = 31
                smon = int(text[1])
                fmon = int(text[1])
                syear = int(text[0])
                fyear = int(text[0])
            elif len(text) == 3:
                sday = int(text[2])
                fday = int(text[2])
                smon = int(text[1])
                fmon = int(text[1])
                syear = int(text[0])
                fyear = int(text[0])
            elif len(text) == 4:
                sday = 1
                fday = 31
                smon = int(text[1])
                fmon = int(text[3])
                syear = int(text[0])
                fyear = int(text[2])
            elif len(text) == 6:
                sday = int(text[2])
                fday = int(text[5])
                smon = int(text[1])
                fmon = int(text[4])
                syear = int(text[0])
                fyear = int(text[3])
        except Exception:
            bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return

    if sday < 1 or sday > 31 or fday < 1 or fday > 31 or smon < 1 or smon > 12 or fmon < 1 or fmon > 12 or syear < 2000 or fyear < syear or (fyear == syear and fmon < smon) or (fyear == syear and fmon == smon and fday < sday):
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    stroka = "Ваши расходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear) + "\n"
    if spend[mid] != 'ВСЕ':
        stroka += "Счет: " + spend[mid] + "\n"
    if vr[mid] != 'ВСЕ':
        stroka += "Категория: " + vr[mid] + "\n"
    stroka += "\n"
    year = syear
    mon = smon
    day = sday
    osum = 0
    kod = 0
    kol1 = 0
    while kod == 0:
        if spend[mid] == 'ВСЕ' and vr[mid] == 'ВСЕ':
            cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d'"%(kods[mid],year,mon,day))
        elif spend[mid] != 'ВСЕ' and vr[mid] == 'ВСЕ':
            cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(kods[mid],year,mon,day,spend[mid]))
        elif spend[mid] == 'ВСЕ' and vr[mid] != 'ВСЕ':
            cur.execute("SELECT name, sum, cat, bank FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(kods[mid],year,mon,day,vr[mid]))
        elif spend[mid] != 'ВСЕ' and vr[mid] != 'ВСЕ':
            cur.execute("SELECT name, sum FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],year,mon,day,spend[mid],vr[mid]))
        stroka1 = str(day) + "." + str(mon) + "." + str(year) + ":\n"
        kol = 0
        for row in cur:
            if vr[mid] == 'ВСЕ':
                stroka1 += "Категория: " + row[2] + "\n"
            if spend[mid] == 'ВСЕ':
                stroka1 += "Счет: " + row[3] + "\n"
            txt = row[0]
            txt = txt.split('%')
            if len(txt[0]) == 0:
                stroka1 +=  "Сумма: " + str(row[1]) + "\n\n"
            else:
                stroka1 +=  "Сумма: " + str(row[1]) + "\n" + txt[0] + "\n\n"
            osum += row[1]
            kol += 1
            kol1 += 1
        if kol > 0:
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
            stroka = "Слишком много элементов"
            kod = 1
    cur.close()
    conn.close()
    vr.pop(mid)
    stroka += 'Итого: ' + str(osum)
    if kol1 == 0:
        stroka = "Расходов за выбранный период по данным категориям и счету нет"
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])

def nums():
    a = time.asctime()
    a = a.split()
    a = a[3]
    a = a.split(':')
    a = int(a[0])*60*60 + int(a[1])*60 + int(a[2])
    return a

def tday():
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    return b

def stday():
    a = str(tday())
    a = a.replace('[','')
    a = a.replace(']','')
    a = a.replace(', ','.')
    return a

def lday():
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    v = 0
    if b[2]%4 == 0:
        v = 1
    b [0] -= 1
    if b[0] < 1:
        b[1] -= 1
        if b[1] < 1:
            b[2] -= 1
            b[1] = 12
        if b[1] != 2:
            v = 0
        b[0] = mdays[b[1]] + v
    return b

def lmon():
    a = time.asctime()
    a = a.split()
    b = [month[a[1]],int(a[4])]
    b [0] -= 1
    if b[0] < 1:
        b[1] -= 1
        b[0] = 12
    return b

def bank_spend_add1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    markup1.row('Сегодня')
    markup1.row('Вчера')
    users[mid] = 'main_bank_spend_add'
    sent = bot.send_message(mid, "За какое число расход? (Формат: дд мм гггг", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_spend_add2)

def bank_spend_add2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() == 'СЕГОДНЯ':
        tme[mid] = tday()
    elif text.upper() == 'ВЧЕРА':
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
    users[mid] = 'main_bank_spend_add'
    sent = bot.send_message(mid, "Напишите расход в формате: описание (не обязателно, не должно начинаться с числа) + сумма расхода")
    bot.register_next_step_handler(sent, bank_spend_add3)

def bank_spend_add3(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text[0] == '-':
        bot.send_message(mid, "Отрицательный расход? Хаха, нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    text = text.split()
    ras = 0
    try:
        ras = int(text[len(text)-1])
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
        text += '%' + str(nums())
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
    for row in cur:
        bal = int(row[0])
    bal -= ras
    if bal < 0:
        bot.send_message(mid, "У вас столько нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        cur.close()
        conn.close()
        return
    tm = tme[mid]
    tme.pop(mid)
    cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(bal,kods[mid],spend[mid]))
    cur.execute("INSERT INTO spend (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%d')"%(kods[mid],tm[2],tm[1],tm[0],vr[mid],spend[mid],text,ras))
    conn.commit()
    cur.close()
    conn.close()
    vr.pop(mid)
    bot.send_message(mid, "Операция выполнена", reply_markup = MUP[users[mid]])

def bank_spend_del1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    markup1.row('Сегодня')
    markup1.row('Вчера')
    users[mid] = 'main_bank_spend_del'
    sent = bot.send_message(mid, "За какое число расход вы хотите удалить? (Формат: дд мм гггг", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_spend_del2)

def bank_spend_del2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() == 'СЕГОДНЯ':
        tme[mid] = tday()
    elif text.upper() == 'ВЧЕРА':
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
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    stroka = "Ваши расходы по данным параметрам\n\n"
    kol = 0
    vr1[mid] = []
    vr2[mid] = []
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    cur.execute("SELECT name, sum FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid]))
    for row in cur:
        kol += 1
        txt = row[0]
        txt = txt.split('%')
        markup1.row('%' + txt[1])
        stroka += 'Сумма: ' + str(row[1]) + '\n' + txt[0] + ' %' + txt[1] + '\n\n'
        vr1[mid].append(txt[1])
        vr2[mid].append(row[0])
    cur.close()
    conn.close()
    if kol == 0:
        bot.send_message(mid, "Нет таких расходов", reply_markup = MUP[users[mid]])
        return
    users[mid] = 'main_bank_spend_del'
    stroka += "Выберите номер расхода, который хотите удалить"
    sent = bot.send_message(mid, stroka, reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_spend_del3)

def bank_spend_del3(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    text = text.split('%')
    if text[1] not in vr1[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    vr2[mid] = vr2[mid][vr1[mid].index(text[1])]
    vr1[mid] = text[1]
    txt = vr2[mid]
    txt = txt.split('%')
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT sum FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    for row in cur:
        vr3[mid] = row[0]
        stroka = 'Вы уверены, что хотите удалить этот расход?\nДата:' + str(tme[mid][0]) + '.' + str(tme[mid][1]) + '.' + str(tme[mid][2]) + '\n'
        stroka += 'Счет: ' + spend[mid] + '\nКатегория: ' + vr[mid] + '\nСумма: ' + str(vr3[mid]) + '\n'
        if len(txt[0]) != 0:
            stroka += txt[0]
    cur.close()
    conn.close()
    users[mid] = 'main_bank_spend_del'
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Удалить", callback_data="bank_spend_del_yes")
    cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="bank_spend_del_no")
    keybGR.add(cbtn1, cbtn2)
    bot.send_message(mid, stroka, reply_markup = keybGR)

def bank_fin(mid):
    users[mid] = 'main_bank_fin'
    if spend.get(mid) == None:
        spend[mid] = 'ВСЕ'
    bot.send_message(mid, "Выберите действие. Текущий счет: " + spend[mid], reply_markup = MUP[users[mid]])

def prev_step(text):
    text = text.split('_')
    text.pop()
    text = '_'.join(text)
    return text

def watch_fcat(mid):
    kol = 0
    stroka = ""
    stroka += 'Ваши категории:\n'
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        kol += 1
        stroka += str(kol) + ') ' + row[0] + '\n\n'
    cur.close()
    conn.close()
    if kol == 0:
        stroka = 'У вас нет категорий'
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])

def bank_fin_cat_add(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.upper() == 'ВСЕ':
        bot.send_message(mid, "Данное имя выбрать невозможно", reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT cat FROM fcats WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].upper() == text.upper():
            bot.send_message(mid, "Данная категория уже существует", reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    cur.execute("INSERT INTO fcats (login,cat) VALUES ('%s','%s')"%(kods[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Категория добавлена", reply_markup = MUP[users[mid]])

def bank_fin_cat_del(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT cat FROM inc WHERE login = '%s'"%(kods[mid]))
    for row in cur:
        if row[0].upper() == text.upper():
            bot.send_message(mid, "Данная категория используется, удаление невозможно", reply_markup = MUP[users[mid]])
            cur.close()
            conn.close()
            return
    cur.execute("DELETE FROM fcats WHERE login = '%s' AND cat = '%s'"%(kods[mid],text))
    conn.commit()
    cur.close()
    conn.close()
    bot.send_message(mid, "Удаление выполнено", reply_markup = MUP[users[mid]])

def bank_fin_add1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    markup1.row('Сегодня')
    markup1.row('Вчера')
    users[mid] = 'main_bank_fin_add'
    sent = bot.send_message(mid, "За какое число доход? (Формат: дд мм гггг", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_fin_add2)

def bank_fin_add2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() == 'СЕГОДНЯ':
        tme[mid] = tday()
    elif text.upper() == 'ВЧЕРА':
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
    users[mid] = 'main_bank_fin_add'
    sent = bot.send_message(mid, "Напишите расход в формате: описание (не обязателно, не должно начинаться с числа) + сумма расхода")
    bot.register_next_step_handler(sent, bank_fin_add3)

def bank_fin_add3(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text[0] == '-':
        bot.send_message(mid, "Отрицательный доход? Хаха, нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    text = text.split()
    ras = 0
    try:
        ras = int(text[len(text)-1])
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
        text += '%' + str(nums())
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
    for row in cur:
        bal = int(row[0])
    bal += ras
    tm = tme[mid]
    tme.pop(mid)
    cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(bal,kods[mid],spend[mid]))
    cur.execute("INSERT INTO inc (login,year,month,day,cat,bank,name,sum) VALUES ('%s','%d','%d','%d','%s','%s','%s','%d')"%(kods[mid],tm[2],tm[1],tm[0],vr[mid],spend[mid],text,ras))
    conn.commit()
    cur.close()
    conn.close()
    vr.pop(mid)
    bot.send_message(mid, "Операция выполнена", reply_markup = MUP[users[mid]])

def bank_fin_his1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() not in vr[mid] and text.upper() != 'ВСЕ':
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    vr[mid] = text
    users[mid] = 'main_bank_fin_his'
    sent = bot.send_message(mid, 'Выберите период, доходы за который хотите посмотреть.\nДопустимый формат ввода: гггг; гггг мм; гггг мм дд; гггг мм гггг мм; гггг мм дд гггг мм дд (последние два подразумевают ввод момента С и момента ДО)', reply_markup = MUP[users[mid]])
    bot.register_next_step_handler(sent, bank_fin_his2)

def bank_fin_his2(message):
    mid = message.chat.id
    text = message.text
    text = text.upper()
    tm = tday()
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text == 'СЕГОДНЯ':
        sday = int(tm[0])
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])
        
    elif text == 'ВЧЕРА':
        tm = lday()
        sday = int(tm[0])
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])
        
    elif text == 'ЭТОТ МЕСЯЦ':
        sday = 1
        fday = int(tm[0])
        smon = int(tm[1])
        fmon = int(tm[1])
        syear = int(tm[2])
        fyear = int(tm[2])

    elif text == 'ПРОШЛЫЙ МЕСЯЦ':
        tm = lmon()
        sday = 1
        fday = 31
        smon = int(tm[0])
        fmon = int(tm[0])
        syear = int(tm[1])
        fyear = int(tm[1])

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
            elif len(text) == 2:
                sday = 1
                fday = 31
                smon = int(text[1])
                fmon = int(text[1])
                syear = int(text[0])
                fyear = int(text[0])
            elif len(text) == 3:
                sday = int(text[2])
                fday = int(text[2])
                smon = int(text[1])
                fmon = int(text[1])
                syear = int(text[0])
                fyear = int(text[0])
            elif len(text) == 4:
                sday = 1
                fday = 31
                smon = int(text[1])
                fmon = int(text[3])
                syear = int(text[0])
                fyear = int(text[2])
            elif len(text) == 6:
                sday = int(text[2])
                fday = int(text[5])
                smon = int(text[1])
                fmon = int(text[4])
                syear = int(text[0])
                fyear = int(text[3])
        except Exception:
            bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
            vr.pop(mid)
            return

    if sday < 1 or sday > 31 or fday < 1 or fday > 31 or smon < 1 or smon > 12 or fmon < 1 or fmon > 12 or syear < 2000 or fyear < syear or (fyear == syear and fmon < smon) or (fyear == syear and fmon == smon and fday < sday):
        bot.send_message(mid, "Неверный формат ввода", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return

    conn = sqlite3.connect(db)
    cur = conn.cursor()
    stroka = "Ваши доходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear) + "\n"
    if spend[mid] != 'ВСЕ':
        stroka += "Счет: " + spend[mid] + "\n"
    if vr[mid] != 'ВСЕ':
        stroka += "Категория: " + vr[mid] + "\n"
    stroka += "\n"
    year = syear
    mon = smon
    day = sday
    osum = 0
    kod = 0
    kol1 = 0
    while kod == 0:
        if spend[mid] == 'ВСЕ' and vr[mid] == 'ВСЕ':
            cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d'"%(kods[mid],year,mon,day))
        elif spend[mid] != 'ВСЕ' and vr[mid] == 'ВСЕ':
            cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(kods[mid],year,mon,day,spend[mid]))
        elif spend[mid] == 'ВСЕ' and vr[mid] != 'ВСЕ':
            cur.execute("SELECT name, sum, cat, bank FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(kods[mid],year,mon,day,vr[mid]))
        elif spend[mid] != 'ВСЕ' and vr[mid] != 'ВСЕ':
            cur.execute("SELECT name, sum FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],year,mon,day,spend[mid],vr[mid]))
        stroka1 = str(day) + "." + str(mon) + "." + str(year) + ":\n"
        kol = 0
        for row in cur:
            if vr[mid] == 'ВСЕ':
                stroka1 += "Категория: " + row[2] + "\n"
            if spend[mid] == 'ВСЕ':
                stroka1 += "Счет: " + row[3] + "\n"  
            txt = row[0]
            txt = txt.split('%')
            if len(txt[0]) == 0:
                stroka1 +=  "Сумма: " + str(row[1]) + "\n\n"
            else:
                stroka1 +=  "Сумма: " + str(row[1]) + "\n" + txt[0] + "\n\n"
            osum += row[1]
            kol += 1
            kol1 += 1
        if kol > 0:
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
            stroka = "Слишком много элементов"
            kod = 1
    cur.close()
    conn.close()
    vr.pop(mid)
    stroka += 'Итого: ' + str(osum)
    if kol1 == 0:
        stroka = "Доходов за выбранный период по данным категориям и счету нет"
    bot.send_message(mid, stroka, reply_markup = MUP[users[mid]])

def bank_fin_del1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    markup1.row('Сегодня')
    markup1.row('Вчера')
    users[mid] = 'main_bank_fin_del'
    sent = bot.send_message(mid, "За какое число доход вы хотите удалить? (Формат: дд мм гггг", reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_fin_del2)

def bank_fin_del2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    if text.upper() == 'СЕГОДНЯ':
        tme[mid] = tday()
    elif text.upper() == 'ВЧЕРА':
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
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    stroka = "Ваши доходы по данным параметрам\n\n"
    kol = 0
    vr1[mid] = []
    vr2[mid] = []
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    cur.execute("SELECT name, sum FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid]))
    for row in cur:
        kol += 1
        txt = row[0]
        txt = txt.split('%')
        markup1.row('%' + txt[1])
        stroka += 'Сумма: ' + str(row[1]) + '\n' + txt[0] + ' %' + txt[1] + '\n\n'
        vr1[mid].append(txt[1])
        vr2[mid].append(row[0])
    cur.close()
    conn.close()
    if kol == 0:
        bot.send_message(mid, "Нет таких доходов", reply_markup = MUP[users[mid]])
        return
    users[mid] = 'main_bank_fin_del'
    stroka += "Выберите номер дохода, который хотите удалить"
    sent = bot.send_message(mid, stroka, reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_fin_del3)

def bank_fin_del3(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text.upper() == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        vr.pop(mid)
        return
    text = text.split('%')
    if text[1] not in vr1[mid]:
        bot.send_message(mid, "Такой категории нет", reply_markup = MUP[users[mid]])
        return
    vr2[mid] = vr2[mid][vr1[mid].index(text[1])]
    vr1[mid] = text[1]
    txt = vr2[mid]
    txt = txt.split('%')
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT sum FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
    for row in cur:
        vr3[mid] = row[0]
        stroka = 'Вы уверены, что хотите удалить этот доход?\nДата:' + str(tme[mid][0]) + '.' + str(tme[mid][1]) + '.' + str(tme[mid][2]) + '\n'
        stroka += 'Счет: ' + spend[mid] + '\nКатегория: ' + vr[mid] + '\nСумма: ' + str(vr3[mid]) + '\n'
        if len(txt[0]) != 0:
            stroka += txt[0]
    cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
    for row in cur:
        bal = row[0]
    cur.close()
    conn.close()
    bal -= vr3[mid]
    if bal < 0:
        bot.send_message(mid, "Невозможно, так как денежных средств останется меньше 0", reply_markup = MUP[users[mid]])
        return
    users[mid] = 'main_bank_fin_del'
    keybGR = types.InlineKeyboardMarkup()
    cbtn1 = types.InlineKeyboardButton(text="Удалить", callback_data="bank_fin_del_yes")
    cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="bank_fin_del_no")
    keybGR.add(cbtn1, cbtn2)
    bot.send_message(mid, stroka, reply_markup = keybGR)

def bank_tr1(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.upper() not in vr[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[users[mid]])
        return
    vr2[mid] = vr2[mid][vr[mid].index(text.upper())]
    vr[mid] = text
    markup1 = types.ReplyKeyboardMarkup()
    markup1.row('ОТМЕНА')
    for i in vr4[mid]:
        if i != vr[mid]:
            markup1.row(i)            
    users[mid] = 'main_bank_tr'
    sent = bot.send_message(mid, 'Выберите счет, на который хотите перевести средства', reply_markup = markup1)
    bot.register_next_step_handler(sent, bank_tr2)
	
def bank_tr2(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text.upper() not in vr1[mid]:
        bot.send_message(mid, "Такого счета нет", reply_markup = MUP[users[mid]])
        return
    vr3[mid] = vr3[mid][vr1[mid].index(text.upper())]
    vr1[mid] = text
    users[mid] = 'main_bank_tr'
    sent = bot.send_message(mid, 'Напишите сумму перевода', reply_markup = markupCanc)
    bot.register_next_step_handler(sent, bank_tr3)
	
def bank_tr3(message):
    mid = message.chat.id
    text = message.text
    users[mid] = prev_step(users[mid])
    if text == 'ОТМЕНА':
        bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        return
    if text[0] == '-':
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])	
        return
    try:
        text = int(text)	
    except Exception:
        bot.send_message(mid, "Неверный формат", reply_markup = MUP[users[mid]])	
        return
    vr2[mid] -= text
    vr3[mid] += text
    if vr2[mid] < 0:
        bot.send_message(mid, "У вас нет столько", reply_markup = MUP[users[mid]])	
        return
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(vr2[mid],kods[mid],vr[mid]))
    cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(vr3[mid],kods[mid],vr1[mid]))
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
            users[mid] = 'main_debt'
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("DELETE FROM groups WHERE name = '%s' AND login = '%s'"%(vr[mid],kods[mid]))
            conn.commit()
            cur.close()
            conn.close()
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удвление выполнено")
            bot.send_message(mid, "Вот меню:", reply_markup = MUP[users[mid]])
            
        if call.data == "gr_del_no":
            users[mid] = 'main_debt'
            vr.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Вот меню:", reply_markup = MUP[users[mid]])
            
        if call.data == "gr_yes":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Будем добавлять еще долг уже существующим")
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            sent = bot.send_message(mid, 'Введите размер долга', reply_markup = markup1)
            bot.register_next_step_handler(sent, group5)
            
        if call.data == "gr_no":
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Оставим у существующих все как есть")
            markup1 = types.ReplyKeyboardMarkup()
            markup1.row('ОТМЕНА')
            sent = bot.send_message(mid, 'Введите размер долга', reply_markup = markup1)
            bot.register_next_step_handler(sent, group6)
            
        if call.data == "bank_del_yes":
            users[mid] = prev_step(users[mid])
            conn = sqlite3.connect(db)
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

        if call.data == "bank_spend_del_yes":
            users[mid] = prev_step(users[mid])
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("DELETE FROM spend WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
            cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
            for row in cur:
                bal = row[0]
                bal += vr3[mid]
            cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(bal,kods[mid],spend[mid]))
            conn.commit()
            cur.close()
            conn.close()
            vr.pop(mid)
            vr1.pop(mid)
            vr2.pop(mid)
            tme.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Удвление выполнено, состояние счета изменено")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])
        
        if call.data == "bank_spend_del_no":
            users[mid] = prev_step(users[mid])
            vr.pop(mid)
            vr1.pop(mid)
            vr2.pop(mid)
            tme.pop(mid)
            bot.edit_message_text(chat_id = mid, message_id = call.message.message_id, text = "Хорошо, не будем удалять")
            bot.send_message(mid, "Выберите действие", reply_markup = MUP[users[mid]])

        if call.data == "bank_fin_del_yes":
            users[mid] = prev_step(users[mid])
            conn = sqlite3.connect(db)
            cur = conn.cursor()
            cur.execute("DELETE FROM inc WHERE login = '%s' AND year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s' AND name = '%s'"%(kods[mid],tme[mid][2],tme[mid][1],tme[mid][0],spend[mid],vr[mid],vr2[mid]))
            cur.execute("SELECT bal FROM bank WHERE login = '%s' AND name = '%s'"%(kods[mid],spend[mid]))
            for row in cur:
                bal = row[0]
                bal -= vr3[mid]
            cur.execute("UPDATE bank SET bal = '%d' WHERE login = '%s' AND name = '%s'"%(bal,kods[mid],spend[mid]))
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
            
bot.polling(none_stop=True)
