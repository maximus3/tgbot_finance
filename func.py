import time
import sqlite3
from config import month, mdays, days
from config import db as data_base

# Загрузка логинов всех пользователей
# Вход: -
# Выход: Список логинов, существующих в базе
def loadlogins():
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    logins = []
    cur.execute('SELECT * FROM users')
    for row in cur:
        logins.append(row[0])
    cur.close()
    conn.close()
    return logins

# Загрузка логинов уже залогинившихся пользователей
# Вход: -
# Выход: Два словаря
def loadkods():
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    kods = dict()
    users = dict()
    cur.execute('SELECT * FROM zalog')
    for row in cur:
        kods[row[0]] = row[1]
        users[row[0]] = 'main'
    cur.close()
    conn.close()
    return kods, users

# Удаление пользователя из списка залогинившихся
# Вход: -
# Выход: 
def del_kod(kod):
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    cur.execute("DELETE FROM zalog WHERE id = '%d'"%(kod))
    conn.commit()
    cur.close()
    conn.close()

# Проверка вещественного числа (два знака после запятой)
# Вход: Строка
# Выход: 'NO' если это не число с двумя знаками после запятой, иначе само число
def check_num(a):
    a = a.replace(',','.')
    try:
        a = float(a)
        a = str(a)
    except Exception:
        return 'NO'
    k = a
    a = a.split('.')
    if len(a[1])>2:
        return 'NO'
    return k

# Рандомное число
# Вход: -
# Выход: Рандомное число
def nums():
    a = time.asctime()
    a = a.split()
    a = a[3]
    a = a.split(':')
    a = int(a[0])*60*60 + int(a[1])*60 + int(a[2])
    return a

# Дата сегодня в виде массива день-месяц-год
# Вход: -
# Выход: Список с элементами - ДД, ММ, ГГГГ (сегодня)
def tday():
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    return b

# Дата сегодня в виде строки
# Вход: -
# Выход: Строка вида 'ДД.ММ.ГГГГ' (сегодня)
def stday():
    a = str(tday())
    a = a.replace('[','')
    a = a.replace(']','')
    a = a.replace(', ','.')
    return a

# Дата вчера в виде массива ДД ММ ГГГГ
# Вход: (не обязательно) список вида time.asctime.split()
# Выход: список вида ДД, ММ, ГГГГ (вчера)
def lday(a = time.asctime().split()):
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
            if b[2]%4 == 0:
                v = 1
            else:
                v = 0
        b[0] = mdays[b[1]]
        if b[1] == 2:
            b[0] += v
    return b

# Прошлый месяц
# Вход: -
# Выход: Список вида ММ, ГГГГ (предыдущий месяц)
def lmon():
    a = time.asctime()
    a = a.split()
    b = [month[a[1]],int(a[4])]
    b [0] -= 1
    if b[0] < 1:
        b[1] -= 1
        b[0] = 12
    return b

# Прибавить k дней
# Вход: Число k; (не обязательно) список вида time.asctime.split()
# Выход: список вида ДД, ММ, ГГГГ (+k дней от даты a)
def day_plus(k, a = time.asctime().split()):
    b = [int(a[2]),month[a[1]],int(a[4])]
    v = 0
    if b[2]%4 == 0:
        v = 1
    for i in range(k):
        b [0] += 1
        if b[0] > mdays[b[1]]:
            if b[1] == 2 and v == 1:
                continue
            b[1] += 1
            if b[1] > 12:
                b[2] += 1
                b[1] = 1
                if b[2]%4 == 0:
                    v = 1
                else:
                    v = 0
            b[0] = 1
    return b

# Отнять k дней
# Вход: Число k; (не обязательно) список вида time.asctime.split()
# Выход: список вида ДД, ММ, ГГГГ (-k дней от даты a)
def day_min(k, a = time.asctime().split()):
    b = [int(a[2]),month[a[1]],int(a[4])]
    v = 0
    if b[2]%4 == 0:
        v = 1
    for i in range(k):
        b [0] -= 1
        if b[0] < 1:
            b[1] -= 1
            if b[1] < 1:
                b[2] -= 1
                b[1] = 12
                if b[2]%4 == 0:
                    v = 1
                else:
                    v = 0
            b[0] = mdays[b[1]]
            if b[1] == 2:
                b[0] += v
    return b

# Неделя от текущий даты - k в формате ДД ММ ГГГГ ДД ММ ГГГГ
# Вход: (не обязательно) число, на которое надо уменьшить текущую дату
# Выход: список вида ДД, ММ, ГГГГ, ДД, ММ, ГГГГ (неделя от и до)
def tweek(k = 0):
    a = time.asctime()
    a = a.split()
    a[0] = days[a[0]]
    b = day_min(k, a)
    a[1] = month[b[1]]
    a[2] = b[0]
    a[4] = b[2]
    while k > 0:
        a[0] -= 1
        k -= 1
        if a[0] == 0:
            a[0] = 7
    return day_min(a[0] - 1, a) + day_plus(7 - a[0], a)

# Предыдущий шаг
# Вход: текущий шаг (main_..._X_Y)
# Выход: предыдущий шаг (main_..._X)
def prev_step(text):
    text = text.split('_')
    text.pop()
    text = '_'.join(text)
    return text

# База данных для определенного пользователя
# Вход: логин пользователя
# Выход: адрес базы данных данного пользователя
def user_db(login):
    return '/root/debt/users/' + login + '/data.db'

# Папка ресурсов определенного пользователя
# Вход: логин пользователя
# Выход: адрес адрес папки ресурсов данного пользователя
def user_res(login):
    return '/root/debt/users/' + login + '/'

# Проверка текста, True если есть ошибка
# Вход: строка; ключ для проверки
# Выход: True если есть строка не соответствует нужному формату, False иначе
def check_text(text, tp):
    if tp == 'rus':
        for i in text:
            if (not (i >= 'а' and i <= 'я')) and i != ' ' and i != 'ё':
                return True
        return False
    elif tp == 'rus1':
        for i in text:
            if (not (i >= 'а' and i <= 'я')) and i != ' ' and (not (i >= '0' and i <= '9')) and i != 'ё':
                return True
        return False
    elif tp == 'eng1':
        for i in text:
            if (not (i >= 'A' and i <= 'Z')) and i != ' ' and (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')):
                return True
        return False
    elif tp == 'login':
        if len(text) > 32:
            return True
        for i in text:
            if (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')):
                return True
        return False
    elif tp == 'pass':
        if len(text) > 32:
            return True
        for i in text:
            if (not (i >= 'A' and i <= 'Z')) and (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')):
                return True
        return False
    elif tp == 'ruseng1':
        for i in text:
            if (not (i >= 'A' and i <= 'Z')) and i != 'ё' and i != ' ' and (not (i >= '0' and i <= '9')) and (not (i >= 'a' and i <= 'z')) and (not (i >= 'а' and i <= 'я')) and (not (i >= 'А' and i <= 'Я')):
                return True
        return False

# Проверка фразы на существование в базе
# Вход: строка (искомая фраза)
# Выход: True если данная фраза есть в базе, False иначе
def phrase_in(text):
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    cur.execute("SELECT phrase FROM alice")
    for row in cur:
        if row[0] == text:
            cur.close()
            conn.close()
            return True
    cur.close()
    conn.close()
    return False

