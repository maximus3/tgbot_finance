import sqlite3
#from config import *
from func import user_db
from diag import make_diag

# Должники
# Вход: логин пользователя
# Выход: список должников пользователя [имя, сумма, дата], количество, общая сумма
def get_debts(login):
    debts = []
    
    kol = 0
    osum = 0

    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT cred, sz, time FROM credits")
    for row in cur:
        debts.append([row[0], row[1], row[2]])
        kol += 1
        osum += row[1]
    cur.close()
    conn.close()
    return debts, kol, osum

# Счета
# Вход: логин пользователя
# Выход: список счетов пользователя [название, сумма], количество, общая сумма
def get_banks(login):
    banks = []

    kol = 0
    osum = 0

    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute("SELECT name, bal FROM bank")
    for row in cur:
        kol += 1
        banks.append([row[0].lower(), row[1]])
        osum += row[1]
    cur.close()
    conn.close()
    return banks, kol, osum

# Категории
# Вход: логин пользователя
# Выход: список счетов пользователя [название], количество
def get_categs(login, sect):
    categs = []

    kol = 0

    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    if sect == 'spend':
        cur.execute("SELECT cat FROM cats")
    elif sect == 'fin':
        cur.execute("SELECT cat FROM fcats")
    for row in cur:
        kol += 1
        categs.append(row[0].lower())
    cur.close()
    conn.close()
    return categs, kol

# Получение истории расходов/доходов
# Вход: ДД, ММ, ГГГГ, ДД, ММ, ГГГГ, id пользователя, флаг отправки данных по месяцам, флаг показа всех позиций, логин, флаг расход/доход, счет, категория
# Выход: Строка отчета, флаг составлена ли диаграмма
def get_fin_his(sday, smon, syear, fday, fmon, fyear, mid, kod_mon, show, login, sect, spend, categ):
    if sect == 'spend':
        stroka = "Ваши расходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear) + "\n"
        title = "Расходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear)
    elif sect == 'fin':
        stroka = "Ваши доходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear) + "\n"
        title = "Доходы с " + str(sday) + "." + str(smon) + "." + str(syear) + ' по ' + str(fday) + "." + str(fmon) + "." + str(fyear)
    if spend != 'все':
        stroka += "Счет: " + spend + "\n"
        title += "\nСчет: " + spend
    if categ != 'все':
        stroka += "Категория: " + categ + "\n"
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
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    while kod == 0:
        if spend == 'все' and categ == 'все':
            if sect == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d'"%(year,mon,day))
            elif sect == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d'"%(year,mon,day))
        elif spend != 'все' and categ == 'все':
            if sect == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(year,mon,day,spend))
            elif sect == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s'"%(year,mon,day,spend))
        elif spend == 'все' and categ != 'все':
            if sect == 'spend':
                cur.execute("SELECT name, sum, cat, bank FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(year,mon,day,categ))
            elif sect == 'fin':
                cur.execute("SELECT name, sum, cat, bank FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND cat = '%s'"%(year,mon,day,categ))
        elif spend != 'все' and categ != 'все':
            if sect == 'spend':
                cur.execute("SELECT name, sum FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(year,mon,day,spend,categ))
            elif sect == 'fin':
                cur.execute("SELECT name, sum FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(year,mon,day,spend,categ))
        stroka1 = str(day) + "." + str(mon) + "." + str(year) + ":\n"
        kol = 0
        for row in cur:
            osum += round(row[1],2)
            kol += 1
            kol1 += 1
            if categ == 'все':
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
            if spend == 'все':
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
        if categ == 'все':
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
    if categ == 'все':
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
            make_diag(login, title, data_names, data_values)
        except Exception as e:
            diag = -1       
    stroka += 'Итого: ' + str(round(osum,2))
    while len(stroka) >= 4000:
            #bot.send_message(mid, stroka[:4000], reply_markup = MUP[users[mid]])
            stroka = stroka[3000:]
    return stroka, diag
