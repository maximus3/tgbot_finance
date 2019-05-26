import telebot
import sqlite3
import time
import logging

from config import TOKEN, monthR, admin_ids, directory, admin_ids

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)3d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO, filename = directory + 'limit.log')

from config import db as data_base
from func import loadkods, loadlogins, tday, user_db, day_count, day_end, check_add_limit, limit_start_date, per_plus
from get_data import get_limits

logging.info( 'Start' )

logging.info( u'Loading logins' )
users_all = loadlogins()
users_in = loadkods('login')
users_str = dict()
logging.info( u'Loaded' )

tm = tday(10)

for login in users_all:
    done = False
    kol = 0
    while not done:
        try:
            logging.debug('[%s] Trying to get limits of user ', login)
            limits, kol = get_limits(login)
            if kol == 0:
                logging.debug('[%s] No limits', login)
                done = True
                break
            logging.debug('[%s] Getting succesful', login)
            if login in users_in:
                logging.debug('[%s] Adding info...', login)
                users_str[login] = ''
                stroka = 'Отчет по лимитам:\n'
                kol_fin = 0
                for elem in limits:
                    if not check_add_limit(elem[1], elem[2], elem[6], elem[7], elem[8], tm):
                        continue
                    if [elem[6], elem[7], elem[8]] == tm:
                        kol_fin += 1
                        continue
                    if elem[0] == '#all':
                        stroka += '\nОбщий лимит:' + '\n'
                    else:
                        stroka += '\nКатегория: ' + elem[0] + '\n'
                    k = day_count(tday(), [elem[6], elem[7], elem[8]])
                    day = day_end(k)
                    stroka += 'У вас осталось ' + str(round(elem[5] - elem[4], 2)) + 'р из ' + str(round(elem[5], 2)) + 'р на ' + str(k) + ' ' + day + ' (до ' + str(elem[6]) + ' ' + monthR[elem[7]] + ' ' + str(elem[8]) + ' года)\n'
                    if elem[2] == 'day' or elem[2] == 'week':
                        count = elem[1]
                        if elem[2] == 'week':
                            count *= 7
                        sm = elem[3] + elem[5] / count
                        if sm <= 0:
                            stroka += 'За предыдущие дни вы израсходовали весь лимит на сегодня (осталось ' + str(round(sm, 2)) +'р на сегодня :), так что будьте аккуратнее\n'
                        else:
                            stroka += 'Сегодня можно будет потратить еще ' + str(round(sm, 2)) + 'р\n'
                if kol_fin != 0:
                    stroka += 'Отчет по законченым лимитам'
                for elem in limits:
                    if [elem[6], elem[7], elem[8]] != tm:
                        continue
                    day = day_end(elem[1], elem[2])
                    stroka += 'За ' + str(elem[1]) + ' ' + day + ' вы потратили ' + str(round(elem[4], 2)) + 'р'
                    if elem[0] != '#all':
                        stroka += ' в категории ' + elem[0]
                    stroka += '.\n'
                    sm = elem[5] - elem[4]
                    if sm > 0:
                        stroka += 'Это на ' + str(round(sm, 2)) + 'р меньше установленного лимита (' + str(round(elem[5], 2)) + 'р).\nПродолжайте в том же духе!\n'
                    elif sm == 0:
                        stroka += 'Вы полностью уложились в лимит.\nПродолжайте в том же духе!\n'
                    else:
                        sm = -sm
                        stroka += 'Это на ' + str(round(sm, 2)) + 'р больше установленного лимита (' + str(round(elem[5], 2)) + 'р).\nПостарайтесь уложиться в установленный лимит в следующий раз.\n'
                    if elem[2] == 'day' or elem[2] == 'week':
                        count = elem[1]
                        if elem[2] == 'week':
                            count *= 7
                        sm = elem[5] / count
                        stroka += 'Сегодня можно будет потратить ' + str(round(sm, 2)) + 'р\n'
                    stroka += '\n'
                users_str[login] = stroka
                logging.debug('[%s] Added', login)
            done = False
            kol = 0
            while not done:
                logging.debug( u'[%s] Updating limits', login)
                try:
                    logging.debug( u'Trying to connect to DB' )
                    conn = sqlite3.connect(user_db(login))
                    logging.debug( u'Connected' )
                    cur = conn.cursor()
                    logging.debug( u'Trying to update' )
                    for elem in limits:
                        dur = 'day'
                        count = elem[1]
                        if elem[2] == 'week':
                            count *= 7
                        if [elem[6], elem[7], elem[8]] != tm:
                            if dur == 'day':
                                cur.execute("UPDATE limits SET tlim = '%f' WHERE cat = '%s' AND count = '%d' AND dur = '%s'"%(round(elem[3] + elem[5] / count, 2), elem[0], elem[1], elem[2]))
                        else:
                            cur.execute("UPDATE limits SET tlim = '%f' WHERE cat = '%s' AND count = '%d' AND dur = '%s'"%(round(elem[5] / count, 2), elem[0], elem[1], elem[2]))
                            cur.execute("UPDATE limits SET sum = '%f' WHERE cat = '%s' AND count = '%d' AND dur = '%s'"%(round(elem[5], 2), elem[0], elem[1], elem[2]))
                            day, mon, year = per_plus(elem[1], elem[2], elem[6], elem[7], elem[8])
                            cur.execute("UPDATE limits SET f_day = '%d' WHERE cat = '%s' AND count = '%d' AND dur = '%s'"%(day, elem[0], elem[1], elem[2]))
                            cur.execute("UPDATE limits SET f_month = '%d' WHERE cat = '%s' AND count = '%d' AND dur = '%s'"%(mon, elem[0], elem[1], elem[2]))
                            cur.execute("UPDATE limits SET f_year = '%d' WHERE cat = '%s' AND count = '%d' AND dur = '%s'"%(year, elem[0], elem[1], elem[2]))            
                    logging.debug( u'Updated' )
                    cur.close()
                    conn.close()
                    done = True
                except Exception as e:
                    logging.error( u'[%s] Update error\n%s', login, str(e) )
                    kol += 1
                    if kol == 10:
                        done = True
                        logging.error( u'[%s] Over 10 errors\n%s', login, str(e) )
                    print(login, e)
                    time.sleep(5)
        except Exception as e:
            logging.error( u'[%s] Getting error\n%s', login, str(e) )
            kol += 1
            if kol == 10:
                done = True
                logging.error( u'[%s] Over 10 errors\n%s', login, str(e) )
            print(login, e)
            time.sleep(5)

try:
    cur.close()
    conn.close()
except Exception:
    pass

bot = telebot.TeleBot(TOKEN)

logging.info( u'Sending...' )

for login in users_str:
    mid = users_in[login]
    if mid not in admin_ids:
        continue
    try:
        logging.info( u'[%s] Sending', str(login) )
        bot.send_message(mid, users_str[login])
        logging.info( u'[%s] Sent', str(login) )
    except Exception as e:
        logging.error( u'Error: ' + str(e))
        pass
