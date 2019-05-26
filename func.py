import time
import sqlite3
from shutil import rmtree
from config import month, mdays, days, monthR, notif_db, directory
from config import db as data_base

# Создание таблиц в базе данных
# Вход: список логинов
# Выход: -
def create_tables(logins):
    for login in logins:
        conn = sqlite3.connect(user_db(login))
        cur = conn.cursor()
        try:
            cur.execute("CREATE TABLE bank (login TEXT, name TEXT, bal REAL)")
        except sqlite3.OperationalError:
           pass
        try:
            cur.execute("CREATE TABLE cats (login TEXT, cat TEXT)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE credits (login TEXT, cred TEXT, time TEXT, sz REAL)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE fcats (login TEXT, cat TEXT)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE inc (login TEXT, year INTEGER, month INTEGER, day INTEGER, cat TEXT, bank TEXT, name TEXT, sum REAL)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE spend (login TEXT, year INTEGER, month INTEGER, day INTEGER, cat TEXT, bank TEXT, name TEXT, sum REAL)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE alice (id TEXT, phrase TEXT, login TEXT)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE template (login TEXT, sect TEXT, name TEXT, cat TEXT, sum REAL)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE limits (login TEXT, cat TEXT, count INTEGER, dur TEXT, tlim REAL, sum REAL, lim_sum REAL, f_year INTEGER, f_month INTEGER, f_day INTEGER)")
        except sqlite3.OperationalError:
            pass
        try:
            cur.execute("CREATE TABLE last_mes (login TEXT, time TEXT, username TEXT, text TEXT)")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        cur.close()
        conn.close()

# Окончание слова "день" в зависимости от числа
# Вход: число
# Выход: дней/дня/день
def day_end(k, a = 'day'):
    k %= 100
    if k > 10 and k < 15:
        if a == 'day':
            return 'дней'
        if a == 'week':
            return 'недель'
        if a == 'month':
            return 'месяцев'
        if a == 'year':
            return 'лет'
        if a == 'day_d':
            return 'дней'
        if a == 'week_d':
            return 'недель'
        if a == 'month_d':
            return 'месяцев'
        if a == 'year_d':
            return 'лет'
    k %= 10
    if k > 4 or k == 0:
        if a == 'day':
            return 'дней'
        if a == 'week':
            return 'недель'
        if a == 'month':
            return 'месяцев'
        if a == 'year':
            return 'лет'
        if a == 'day_d':
            return 'дней'
        if a == 'week_d':
            return 'недель'
        if a == 'month_d':
            return 'месяцев'
        if a == 'year_d':
            return 'лет'
    elif k < 2:
        if a == 'day':
            return 'день'
        if a == 'week':
            return 'неделя'
        if a == 'month':
            return 'месяц'
        if a == 'year':
            return 'год'
        if a == 'day_d':
            return 'день'
        if a == 'week_d':
            return 'неделю'
        if a == 'month_d':
            return 'месяц'
        if a == 'year_d':
            return 'год'
    else:
        if a == 'day':
            return 'дня'
        if a == 'week':
            return 'недели'
        if a == 'month':
            return 'месяца'
        if a == 'year':
            return 'года'
        if a == 'day_d':
            return 'дня'
        if a == 'week_d':
            return 'недели'
        if a == 'month_d':
            return 'месяца'
        if a == 'year_d':
            return 'года'

# Удаление аккаунта
# Вход: логин, id
# Выход: -
def delete_data(login, mid):
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    cur.execute("DELETE FROM zalog WHERE login = ?", [(login)])
    cur.execute("DELETE FROM zalog_alice WHERE login = ?", [(login)])
    cur.execute("DELETE FROM alice WHERE login = ?", [(login)])
    cur.execute("DELETE FROM users WHERE login = ?", [(login)])
    conn.commit()
    cur.close()
    conn.close()
    conn = sqlite3.connect(notif_db)
    cur = conn.cursor()
    cur.execute("DELETE FROM notif WHERE login = ?", [(login)])
    conn.commit()
    cur.close()
    conn.close()
    rmtree(directory + 'users/' + login + '/')

# Сброс данных пользователя
# Вход: логин, True если надо удалить категории
# Выход: -
def reset_data(login, del_cat):
    # conn = sqlite3.connect(data_base)
    # cur = conn.cursor()
    # cur.execute("DELETE FROM alice WHERE login = ?", [(login)])
    # conn.commit()
    # cur.close()
    # conn.close()
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("DELETE FROM bank WHERE login = ?", [(login)])
    cur.execute("DELETE FROM inc WHERE login = ?", [(login)])
    cur.execute("DELETE FROM spend WHERE login = ?", [(login)])
    cur.execute("DELETE FROM alice WHERE login = ?", [(login)])
    cur.execute("DELETE FROM credits WHERE login = ?", [(login)])
    cur.execute("DELETE FROM limits WHERE login = ?", [(login)])
    cur.execute("DELETE FROM template WHERE login = ?", [(login)])
    if del_cat:
        cur.execute("DELETE FROM cats WHERE login = ?", [(login)])
        cur.execute("DELETE FROM fcats WHERE login = ?", [(login)])
    conn.commit()
    cur.close()
    conn.close()

# Быстрая авторизация в Яндекс.Диалогах
# Вход: токен, логин
# Выход: Строка состояния
def alice_after_auth(text, login):
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM alice WHERE id = '%s'"%(text))
        conn.commit()
    except Exception:
        pass
    cur.close()
    conn.close()
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    cur.execute("SELECT login FROM zalog_alice WHERE id = '%s'"%(text))
    kod = 1
    for row in cur:
        kod = 0
    if kod:
        cur.execute("INSERT INTO zalog_alice (id,login) VALUES ('%s','%s')"%(text,login))
        conn.commit()
        text = "Авторизация Яндекс.Диалога успешно пройдена"
    else:
        text = "Данное устройство в Яндекс.Диалогах уже подключено"
    cur.close()
    conn.close()
    return text

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
def loadkods(kod = 'all'):
    conn = sqlite3.connect(data_base)
    cur = conn.cursor()
    kods = dict()
    users = dict()
    cur.execute('SELECT * FROM zalog')
    for row in cur:
        if kod == 'all':
            kods[row[0]] = row[1]
            users[row[0]] = 'main'
        else:
            kods[row[1]] = row[0]
    cur.close()
    conn.close()
    if kod == 'all':
        return kods, users
    else:
        return kods

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
# Вход: (не обязательно) + минут
# Выход: Список с элементами - ДД, ММ, ГГГГ (сегодня)
def tday(k = 0):
    a = time.asctime()
    a = a.split()
    b = [int(a[2]),month[a[1]],int(a[4])]
    tm = time.asctime().split()[3].split(':')
    tm = int(tm[0]) + (int(tm[1]) + k) // 60
    if tm == 24:
        return day_plus(1)
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
    b[0] -= 1
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

# Количество дней между датами
# Вход: Число k; (не обязательно) список вида time.asctime.split()
# Выход: список вида ДД, ММ, ГГГГ (+k дней от даты a)
def day_count(b, a):
    k = 0
    v = 0
    if b[2]%4 == 0:
        v = 1
    while a != b:
        if (a[2] == b[2] and a[1] == b[1]):
            k += a[0] - b[0]
            return k
        k += 1
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
    return k

# Увеличение периода
# Вход: период (количество, day/week/month/year), дата окончания (день, месяц, год)
# Выход: дата окончания нового периода (день, месяц, год)
def per_plus(count, dur, day, mon, year):
    if dur == 'week':
        count *= 7
        dur = 'day'
    if dur == 'day':
        day, mon, year = day_plus(count)
    elif dur == 'year':
        year += count
    elif dur == 'month':
        while count > 0:
            mon += 1
            count -= 1
            if mon == 13:
                mon = 11
                year += 1

    return day, mon, year

# Начало периода лимита
# Вход: период (количество, day/week/month/year), дата окончания (день, месяц, год)
# Выход: дата начала периода (день, месяц, год)
def limit_start_date(count, dur, day, mon, year):
    if dur == 'week':
        count *= 7
        dur = 'day'
    if dur == 'day':
        return day_min(count, b = [day, mon, year])
    elif dur == 'year':
        year -= count
    elif dur == 'month':
        while count > 0:
            mon -= 1
            count -= 1
            if mon == 0:
                mon = 12
                year -= 1
    return [day, mon, year]

# Проверка нужно ли добавлять расход в данный лимит
# Вход: период (количество, day/week/month/year), дата окончания (день, месяц, год), дата расхода ([день, месяц, год])
# Выход: True если нужно, False иначе
def check_add_limit(count, dur, day, mon, year, tm):
    tm_start = limit_start_date(count, dur, day, mon, year)
    tm1 = [tm[2], tm[1], tm[0]]
    tm_start.reverse()
    return tm1 >= tm_start

# Прибавить k дней
# Вход: Число k; (не обязательно) список вида time.asctime.split(); (не обязательно) список ДД, ММ, ГГГГ
# Выход: список вида ДД, ММ, ГГГГ (+k дней от даты a)
def day_plus(k, a = time.asctime().split(), b = []):
    if b == []:
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
# Вход: Число k; (не обязательно) список вида time.asctime.split(); (не обязательно) список ДД, ММ, ГГГГ
# Выход: список вида ДД, ММ, ГГГГ (-k дней от даты a)
def day_min(k, a = time.asctime().split(), b = []):
    if b == []:
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

# Следующая неделя в формате ДД ММ ГГГГ 
# Вход: -
# Выход: список вида ДД, ММ, ГГГГ (дата начала следующей недели)
def next_week():
    a = days[time.asctime().split()[0]]
    return day_plus(8 - a)

# Следующий месяцs в формате ДД ММ ГГГГ
# Вход: -
# Выход: список вида ДД, ММ, ГГГГ (дата начала следующего месяца)
def next_month():
    a = time.asctime().split()
    a = [int(a[2]), month[a[1]], int(a[4])]
    a[0] = 1
    a[1] += 1
    if a[1] == 13:
        a[1] = 1
        a[2] += 1
    return a

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
    return directory + 'users/' + login + '/data.db'

# Папка ресурсов определенного пользователя
# Вход: логин пользователя
# Выход: адрес адрес папки ресурсов данного пользователя
def user_res(login):
    return directory + 'users/' + login + '/'

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

