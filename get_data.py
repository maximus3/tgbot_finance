import sqlite3
from config import monthR, monthRim, notif_db, directory
from func import user_db, tday, lday
from diag import make_diag

import logging

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO, filename = directory + 'finbot.log')

# Просмотр уведомлений о записи
# Вход: логин
# Выход: строка с уведомлениями
def watch_notif(login):

    notifs = []
    
    stroka = 'Ваши уведомления о записи расходов и доходов:\n'
    conn = sqlite3.connect(notif_db)
    cur = conn.cursor()
    cur.execute("SELECT time FROM notif WHERE login = '%s'"%(login))
    for row in cur:
        notifs.append(row[0])
    cur.close()
    conn.close()

    notifs.sort()
    for elem in notifs:
        tm = str(elem)
        if len(tm) < 2:
            tm = '0' + tm
        stroka += '- ' + str(tm) + ':00\n'

    if len(notifs) == 0:
        stroka = 'У вас нет уведомлений о записи расходов и доходов'
    return stroka

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

# Шаблоны
# Вход: логин пользователя
# Выход: список шаблонов пользователя [название, категория, сумма], количество
def get_templates(login):
    templates = []

    kol = 0

    logging.info('get_templates: Connecting to data base')
    conn = sqlite3.connect(user_db(login))
    logging.info('get_templates: Connected')
    cur = conn.cursor()
    logging.info('get_templates: Executing')
    cur.execute("SELECT name, cat, sum, sect FROM template")
    for row in cur:
        kol += 1
        templates.append([row[0].lower(), row[1].lower(), row[2], row[3]])
    logging.info('get_templates: Executed')
    logging.info('get_templates: Closing connection')
    cur.close()
    conn.close()
    logging.info('get_templates: Closed')
    return templates, kol

# Категории
# Вход: логин пользователя, spend/fin (расходы или доходы)
# Выход: список категорий пользователя [название], количество
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

# Лимиты
# Вход: логин пользователя
# Выход: список лимитов пользователя [категория, количество, day/week/month/year, остаток на сегодня, сумма расходов, сумма лимита, день окончания, месяц окончания, год окончания], количество
def get_limits(login):
    limits = []

    kol = 0
    
    conn = sqlite3.connect(user_db(login))
    cur = conn.cursor()
    cur.execute('SELECT cat, count, dur, tlim, sum, lim_sum, f_day, f_month, f_year FROM limits')
    for row in cur:
        kol += 1
        limits.append([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]])
        if row[0] == '#all':
            limits = [limits.pop()] + limits
    cur.close()
    conn.close()
    return limits, kol

# Получение истории расходов/доходов
# Вход: ДД, ММ, ГГГГ, ДД, ММ, ГГГГ, флаг отправки данных по месяцам, флаг показа всех позиций, логин, флаг расход/доход, счет, категория, флаг показа диаграммы
# Выход: Строка отчета, флаг составлена ли диаграмма
def get_fin_his(sday, smon, syear, fday, fmon, fyear, kod_mon, show, login, sect, spend, categ, show_diag):
    if sect == 'spend':
        stroka = "Ваши расходы "
        title = "Расходы "
    elif sect == 'fin':
        stroka = "Ваши доходы "
        title = "Доходы "
    if sday == fday and smon == fmon and syear == fyear:
        if [sday, smon, syear] == tday():
            stroka += "за сегодня (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)\n"
            title += "за сегодня (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)"
        elif [sday, smon, syear] == lday():
            stroka += "за вчера (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)\n"
            title += "за вчера (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)"
        else:
            stroka += "за " + str(sday) + " " + monthR[smon] + " " + str(syear) + " года\n"
            title += "за " + str(sday) + " " + monthR[smon] + " " + str(syear) + " года"
    elif smon == fmon and sday == 1 and fday == 31:
        stroka += "за " + monthRim[smon] + " " + str(syear) + " года\n"
        title += "за " + monthRim[smon] + " " + str(syear) + " года"
    else:
        stroka += "с " + str(sday) + " " + monthR[smon] + " " + str(syear) + ' года, по ' + str(fday) + " " + monthR[fmon] + " " + str(fyear) + " года\n"
        title += "с " + str(sday) + " " + monthR[smon] + " " + str(syear) + ' года, по ' + str(fday) + " " + monthR[fmon] + " " + str(fyear) + " года"
    if spend != 'все':
        stroka += "Счет: " + spend + "\n"
        title += "\nСчет: " + spend
    if categ != 'все':
        stroka += "Категория: " + categ + "\n"
    stroka += "\n"
    s_old = stroka
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
        else:
            if sect == 'spend':
                cur.execute("SELECT name, sum FROM spend WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(year,mon,day,spend,categ))
            elif sect == 'fin':
                cur.execute("SELECT name, sum FROM inc WHERE year = '%d' AND month = '%d' AND day = '%d' AND bank = '%s' AND cat = '%s'"%(year,mon,day,spend,categ))
        if sday == fday and smon == fmon and syear == fyear:
            stroka1 = ''
        elif syear == fyear:
            stroka1 = str(day) + " " + monthR[mon] + ':\n'
        else:
            stroka1 = str(day) + " " + monthR[mon] + " " + str(year) + ' года:\n'
        kol = 0
        for row in cur:
            osum += round(row[1],2)
            kol += 1
            kol1 += 1
            if categ == 'все':
                stroka1 += row[2]
                if kod_mon == 1:
                    if mon_s.get(str(year) + ' ' + str(mon)) == None:
                        mon_s[str(year) + ' ' + str(mon)] = dict()
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
                if categ == 'все':
                    stroka1 += ', '
                stroka1 += row[3]
            txt = row[0]
            txt = txt.split('%')
            if len(txt[0]) == 0:
                stroka1 +=  str(round(row[1],2)) + "р\n\n"
            else:
                stroka1 +=  txt[0] + ' ' + str(round(row[1],2)) + "р\n\n"
  
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
            stroka = s_old
            kodK = 1

    cur.close()
    conn.close()
    if kol1 == 0:
        if sect == 'spend':
            stroka = "У вас нет расходов "
        elif sect == 'fin':
            stroka = "У вас нет доходов "
        if sday == fday and smon == fmon and syear == fyear:
            if [sday, smon, syear] == tday():
                stroka += "за сегодня (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)\n"
            elif [sday, smon, syear] == lday():
                stroka += "за вчера (" + str(sday) + " " + monthR[smon] + " " + str(syear) + " года)\n"
            else:
                stroka += "за " + str(sday) + " " + monthR[smon] + " " + str(syear) + " года\n"
        elif smon == fmon and sday == 1 and fday == 31:
            stroka += "за " + monthRim[smon] + " " + str(syear) + " года\n"
        else:
            stroka += "с " + str(sday) + " " + monthR[smon] + " " + str(syear) + ' года, по ' + str(fday) + " " + monthR[fmon] + " " + str(fyear) + " года\n"
        if spend != 'все' or categ != 'все':
            stroka +=  " по данным категориям и счету"
        return stroka, 2
    
    if kod_mon == 1:
        if categ == 'все':
            for i in sorted(mon_s):
                stroka += 'Месяц: ' + i + '\n'
                osum1 = 0
                for j in sorted(mon_s[i]):
                    stroka += str(j) + ': ' + str(round(mon_s[i][j],2)) + '\n'
                    osum1 += mon_s[i][j]
                stroka += 'Итого за месяц: ' + str(round(osum1,2)) + 'р\n'
                stroka += '\n'
        else:
            for i in sorted(mon_s):
                stroka += 'Месяц: ' + i + '\n'
                stroka += 'Сумма: ' + str(round(mon_s[i],2)) + 'р\n'
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
            stroka += elem[1] + ': ' + str(round(elem[0],2)) + 'р\n'
        try:
            if show_diag:
                make_diag(login, title, data_names, data_values)
        except Exception as e:
            diag = -1       
    stroka += 'Итого: ' + str(round(osum,2))
    while len(stroka) >= 4000:
            #bot.send_message(mid, stroka[:4000], reply_markup = MUP[users[mid]])
            stroka = stroka[3000:]
    return stroka, diag
