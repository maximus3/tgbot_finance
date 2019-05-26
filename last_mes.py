import sqlite3

logins = []
month = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12, 1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}

conn = sqlite3.connect("my.db")
cur = conn.cursor()
cur.execute("SELECT login FROM users")
rows = cur.fetchall()
cur.close()
conn.close()

for row in rows:
    logins.append(row[0])

stroka = 'Всего пользователей: ' + str(len(logins)) + '\n'
last = []

for login in logins:
    try:
        conn = sqlite3.connect("users/" + login + "/data.db")
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
        if str(e) != 'no such column: username':
            print(str(e))
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
