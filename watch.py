from get_data import get_debts, get_limits, get_templates, get_categs
from func import day_count, day_end, tday, limit_start_date, check_add_limit
from config import notif_db, monthR, directory

import logging

logging.basicConfig(format = u'%(filename)s[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s', level = logging.INFO, filename = directory + 'finbot.log')

# Просмотр Лимитов
# Вход: логин
# Выход: строка с лимитами
def watch_limits(login):

    limits, kol = get_limits(login)

    tm = tday()

    if kol == 0:
        return "На данный момент у вас нет установленных лимитов"

    stroka = ''
    stroka1 = '\n'
    for elem in limits:
        if check_add_limit(elem[1], elem[2], elem[6], elem[7], elem[8], tm):
            if elem[0] == '#all':
                stroka += '\n- Все категории:' + '\n'
            else:
                stroka += '\n- Категория: ' + elem[0] + '\n'
            k = day_count(tday(), [elem[6], elem[7], elem[8]])
            day = day_end(k)
            stroka += 'У вас осталось ' + str(round(elem[5] - elem[4], 2)) + 'р из ' + str(round(elem[5], 2)) + 'р на ' + str(k) + ' ' + day + ' (до ' + str(elem[6]) + ' ' + monthR[elem[7]] + ' ' + str(elem[8]) + ' года)\n'
            if elem[2] == 'day' or elem[2] == 'week':
                if elem[3] > 0:
                    stroka += 'А сегодня можно потратить еще ' + str(round(elem[3], 2)) + 'р\n'
                elif elem[3] == 0:
                    stroka += 'Вы израсходовали весь лимит на сегодня.\n'
                else:
                    stroka += 'Вы потратили сегодня на ' + str(round(-elem[3], 2)) + 'р больше, чем можно было. Будьте аккуратнее.\n'
        else:
            tm_start = limit_start_date(elem[1], elem[2], elem[6], elem[7], elem[8])
            if elem[0] == '#all':
                stroka1 += '- У вас запланирован лимит на все категории в '
            else:
                stroka1 += '- У вас запланирован лимит на категорию ' + elem[0] + ' в '
            stroka1 += str(round(elem[5], 2)) + 'р на ' + str(elem[1]) + ' ' + day_end(elem[1], a = elem[2] + '_d') + ' с ' + str(tm_start[0]) + ' ' + monthR[tm_start[1]] + ' ' + str(tm_start[2]) + ' года\n'
    return stroka + stroka1

# Просмотр Шаблонов
# Вход: логин
# Выход: строка с шаблонами
def watch_templates(login):

    logging.info('watch_templates: Getting templates')
    templates, kol = get_templates(login)
    logging.info('watch_templates: Got')

    if kol == 0:
        return "На данный момент у вас нет шаблонов"

    stroka1 = 'Шаблоны расходов:\n'
    stroka2 = '\nШаблоны доходов:\n'
    for elem in templates:
        if elem[3] == 'spend':
            stroka1 += '- ' + elem[0] + ' (' + elem[1] + ', ' + str(elem[2]) + 'р)\n'
        else:
            stroka2 += '- ' + elem[0] + ' (' + elem[1] + ', ' + str(elem[2]) + 'р)\n'
    return stroka1 + stroka2

# Просмотр должников
# Вход: логин
# Выход: строка с долгами
def watch_debts(login):
    
    debts, kol, osum = get_debts(login)
    
    sm = 0
    stroka = 'Я должен:\n'
    for elem in debts:
        if elem[1] < 0:
            sm -= -elem[1]
            stroka += '- ' + elem[0] + ' ' + str(round(-elem[1],2)) + 'р от ' + elem[2] + '\n\n'
    stroka += 'Всего ' + str(round(sm,2)) + 'р\n\n'
    sm = 0
    stroka += 'Мне должны:\n'
    for elem in debts:
        if elem[1] > 0:
            sm += elem[1]
            stroka += '- ' + elem[0] + ' ' + str(round(elem[1],2)) + 'р от ' + elem[2] + '\n\n'
    stroka += 'Всего ' + str(round(sm,2)) + 'р\n\n'
    stroka += 'Всего человек: ' + str(kol) + '\nСумма: ' + str(round(osum,2))
    
    if kol == 0:
        stroka = 'У вас нет должников'

    return stroka

# Просмотр категорий
# Вход: логин, spend/fin (расходы или доходы)
# Выход: строка с категориями
def watch_cat(login, sect):

    categs, kol = get_categs(login, sect)
    
    stroka = 'Ваши категории:\n\n'
    
    for i, elem in enumerate(categs):
        stroka += str(i + 1) + ') ' + elem + '\n'
    if kol == 0:
        stroka = 'У вас нет категорий'

    return stroka
