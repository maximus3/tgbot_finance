from telebot import types

TOKEN = 'TGBOT_TOKEN_HERE'

version = '0.4.4.1 Beta'

"""
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

4.1.0:
WebHook!!!
(Теперь бот не должен постоянно падать)
4.1.1:
Мелкие орфографические исправления

4.2.0:
Теперь расходы могут быть и не целыми!!!
4.2.1:
Теперь отображается ваша потенциальная сумма денег (с учетом долгов)
4.2.2:
Добавлены расходы и доходы по категориям при показе общих расходов

4.3.0:
При добавлении нового счета можно указать стартовый баланс
Добавлена возможность редактирования расходов и доходов, а также возможность перенести перенести расходы и доходы из одной категории в другую
Мелкие исправления

4.4.0:
Достаточно крупное обновление (с програмной стороны)
Усовершенствована система хранения и обрботки данных (скоро появится резервное копирование данных для большей безопасности)
Увеличение скорости доступа к файлам

4.4.1:
Немного доработан интерфейс
Убраны ненужные кнопки
"""

chng = """
4.4.1:
Немного доработан интерфейс
"""

desc = """
Данный бот был создан для того, чтобы вы могли вести учет своих расходов и доходов
"""


WEBHOOK_HOST = 'HOST_HERE'
WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

WEBHOOK_SSL_CERT = '/root/debt/webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = '/root/debt/webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)


db = '/root/debt/my.db'
aid = 0 # ADMIN_TGID_HERE
code = 'пассажиры'
ERRORS_DESC = """
0 - все в порядке
1 - остановлено пользователем
"""

month = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
mdays = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}


markupSG = types.ReplyKeyboardMarkup()
markupSG.row('Мой кошелек','Мои долги')
markupSG.row('Смена пароля', 'О боте')    
markupSG.row('Выход')

markupUS = types.ReplyKeyboardMarkup()
markupUS.row('Вход','Регистрация')
markupUS.row('О боте')

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
markupSpend.row('Новый расход','Редактировать расход')
markupSpend.row('Поменять счет','Категории')
markupSpend.row('Назад')

markupFin = types.ReplyKeyboardMarkup()
markupFin.row('Доходы за период')
markupFin.row('Новый доход','Редактировать доход')
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

MUP = {'mainUS':markupUS,'main':markupSG,'main_debt':markupDebt,'main_bank':markupBank,'main_bank_fin_cat':markupCat,'main_bank_spend_cat':markupCat,'main_bank_spend':markupSpend,'main_debt_group':markupG,'main_bank_fin_his':markupSZ,'main_bank_spend_his':markupSZ,'main_bank_fin':markupFin}

