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




"""
keybGR = types.InlineKeyboardMarkup()
cbtn1 = types.InlineKeyboardButton(text="Добавить", callback_data="gr_yes")
cbtn2 = types.InlineKeyboardButton(text="Оставить", callback_data="gr_no")
keybGR.add(cbtn1, cbtn2)
bot.send_message(mid, 'Вы хотите добавить существующим учасиникам долг или оставить их долг таким же?', reply_markup = keybGR)  
"""


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
