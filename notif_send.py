import telebot
import sqlite3
import time
import logging

from config import TOKEN, notif_db, directory
from config import db as data_base

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.DEBUG, filename = directory + 'notif.log')

logging.info( u'Start...' )

done = False

logins_ch = []
notif = dict()

tm = time.asctime().split()[3].split(':')
tm = int(tm[0]) + (int(tm[1]) + 10) // 60

kol = 0

while not done:
    try:
        logging.info( u'Trying to connect to DB' )
        conn = sqlite3.connect(notif_db)
        logging.info( u'Connected' )
        cur = conn.cursor()
        logging.info( u'Trying to execute' )
        cur.execute("SELECT login FROM notif WHERE time = '%d'"%(tm))
        logging.info( u'Executed' )
        for row in cur:
            logins_ch.append(row[0])
        cur.close()
        conn.close()
        done = True
        logging.info( u'Logins_ch done' )
    except Exception as e:
        logging.error( u'Connect error\n' + str(e) )
        kol += 1
        if kol == 10:
            done = True
            logging.error( u'Over 10 errors\n' + str(e) )
        print(e)
        time.sleep(5)

try:
    cur.close()
    conn.close()
except Exception:
    pass

done = False

kol = 0

while not done:
    try:
        logging.info( u'Trying to connect to DB' )
        conn = sqlite3.connect(data_base)
        logging.info( u'Connected' )
        cur = conn.cursor()
        logging.info( u'Trying to execute' )
        cur.execute('SELECT * FROM zalog')
        logging.info( u'Executed' )
        for row in cur:
            if row[1] in logins_ch:
                notif[row[0]] = row[1]
        cur.close()
        conn.close()
        done = True
        logging.info( u'Notif done' )
    except Exception as e:
        logging.error( u'Connect error\n' + str(e) )
        kol += 1
        if kol == 10:
            done = True
            logging.error( u'Over 10 errors\n' + str(e) )
        print(e)
        time.sleep(5)

try:
    cur.close()
    conn.close()
except Exception:
    pass

bot = telebot.TeleBot(TOKEN)

logging.info( u'Sending...' )

for mid in notif:
    try:
        logging.info( u'Sending to ' + str(notif[mid]) )
        bot.send_message(mid, "Привет! Самое время записать свои расходы и доходы!")
    except Exception as e:
        logging.error( u'Error: ' + str(e))
        pass
