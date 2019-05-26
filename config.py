from telebot import types

# Токен для телеграм-бота
TOKEN = 'TGBOT_TOKEN_HERE'

# Версия телеграм-бота
version = '0.5.2.0 Beta'

"""
0.2.0.0:
Команды теперь не через слеш и на русском!
Усовершенствованы системы хранения и обраотки данных
0.2.0.1:
Вместо CANCEL теперь ОТМЕНА (полный перевод)
Команды можно писать и большими и маленькими буквами
0.2.0.2:
Ввод логина и пароля при регистрации и авторизации теперь возможен и через два разных сообщения!
0.2.0.3:
Пароль должен состоять только из символов A..Z, a..z или цифр

0.2.1.0:
Бот будет работать без перебоев (я надеюсь)
0.2.1.1:
Теперь нельзя заходить по одному логину с разных аккаунтов одновременно
0.2.1.2:
Оптимизация кода

0.2.2.0:
Добавлены группы. Теперь вы можете создать свою группу должников и каждый раз не писать их отдельно, а добавлять долг сразу всем.

0.3.0.0:
Теперь этот бот будет и вашей бухгалтерией. Для начала немного перенесем раздел долги
0.3.0.1:
Исправлено:
Удаление групп
Добавлено:
Возможность создавать счета
0.3.0.2:
Возможность удалять счета

0.4.0.1:
Появились расходы:
смена счета, с которым работаешь
добавлены категории
добалена возможность просмотра истории операций
0.4.0.2:
Оптимизирована работа со временем в истории расходов
0.4.0.3:
Добавлена возможность добавлять расходы
0.4.0.4:
Теперь возможно добавлять расходы за любую дату
0.4.0.5:
Теперь можно удалять расходы и доходы из истории
0.4.0.6:
В долгах добавлены даты
Добавлена общая сумма расходов/доходов за период
Добавлены переводы
0.4.0.7:
Теперь расходы связанны со счетами

0.4.1.0:
WebHook!!!
(Теперь бот не должен постоянно падать)
0.4.1.1:
Мелкие орфографические исправления

0.4.2.0:
Теперь расходы могут быть и не целыми!!!
0.4.2.1:
Теперь отображается ваша потенциальная сумма денег (с учетом долгов)
0.4.2.2:
Добавлены расходы и доходы по категориям при показе общих расходов

0.4.3.0:
При добавлении нового счета можно указать стартовый баланс
Добавлена возможность редактирования расходов и доходов, а также возможность перенести перенести расходы и доходы из одной категории в другую
Мелкие исправления

0.4.4.0:
Достаточно крупное обновление (с програмной стороны)
Усовершенствована система хранения и обрботки данных (скоро появится резервное копирование данных для большей безопасности)
Увеличение скорости доступа к файлам
0.4.4.1:
Немного доработан интерфейс
Убраны ненужные кнопки

0.4.5.0:
Интерфейс еще немного переработан (вкладка аккаунт)
Оптимизация кода
Нельзя поменять сумму дохода так, чтобы баланс стал отрицательным

0.5.0.0:
Начальная интеграция с Яндекс.Алисой!
0.5.0.1:
Исправление багов
0.5.0.2:
Небольшие фиксы
0.5.0.3:
Небольшие фиксы
0.5.0.4:
Вернулись комментарии на английском
0.5.0.5:
Статистика + редактрирование описания + буква ё + /help

0.5.1.0:
Кнопки теперь имеют другой вид для большей безопасности
При добавлении или редактировании расходов/доходов, если у вас не выбран счет, вам предлагают его выбрать
Добавлен просмотр расходов/доходов по месяцам (при посмотре за год)
Исправлены мелкие баги
0.5.1.1:
Расходы и доходы по неделям
0.5.1.2:
Диаграммы!
0.5.1.3:
После регистрации вы сразу входите в аккаунт
Изменено взаимодействие с inline-кнопками
Немного изменен интерфейс
Исправление багов
Оптимизация программы
0.5.1.4:
Добавлена поддержка быстрой авторизации Яндекс.Диалогов!!!
Небольшая оптимизация кода

0.5.2.0:
# Запись даты последнего сообщения пользователя
# Новые функции админ-панели

0.5.2.1:
"Сумма, учитывая долги" показывается не всем
"""

chng = """
Очень крупное обновление - добавлено множество новых функций
- Добавлена функция "Удаление аккаунта"
- Добавлена возможность сброса данных
- Изменен вид показа долгов
- Изменен вид показа расходов/доходов
- Показ расходов/доходов за сегодня в соответствующем меню
- Добавлена возможность добавлять расходы и доходы одной командой (подробнее /help)
- Новая функция - уведомления (пока может только напоминать вам записывать расходы каждый день)
- Новая функция - Шаблоны (используются при добавлении одной командой)
- Новая функция - лимиты (подробнее /help)

P.S. Возможны баги, поэтому если вы их вдруг обнаружите, то обязательно напишите об этом в @m3prod
"""

# Описание телеграм-бота
desc = """
Данный бот поможет вам вести учет своих расходов и доходов.
"""

# Адрес папки
directory = '/root/debt/'

# Адрес общей базы данных
db = directory + 'my.db'

# Адрес базы данных для уведомлений
notif_db = directory +'notif.db'

# ID админа телеграм
admin_id = 0 #ADMIN_TGID_HERE
admin_ids = [] #ADMINs_TGID_HERE
tester_ids = []
# Секретный код
code = 'пассажиры'
testers_code = 'яхочутестить11112018'
# Описание ошибок
ERRORS_DESC = """
0 - все в порядке
1 - остановлено админом
2 - бот не запущен после перезагрузки
3 - может работать только админ
"""

# Словарь, преобразующий строки вида Mmm в число или наоборот (месяц)
month = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12, 1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
# Словарь, преобразующий строки с названиями месяцев в число или наоборот (именительный падеж)
monthRim = {'январь':1,'февраль':2,'март':3,'апрель':4,'май':5,'июнь':6,'июль':7,'август':8,'сентябрь':9,'октябрь':10,'ноябрь':11,'декабрь':12,1:'январь',2:'февраль',3:'март',4:'апрель',5:'май',6:'июнь',7:'июль',8:'август',9:'сентябрь',10:'октябрь',11:'ноябрь',12:'декабрь'}
# Словарь, преобразующий строки с названиями месяцев в число или наоборот (родительный падеж)
monthR = {'января':1,'февраля':2,'марта':3,'апреля':4,'мая':5,'июня':6,'июля':7,'августа':8,'сентября':9,'октября':10,'ноября':11,'декабря':12,1:'января',2:'февраля',3:'марта',4:'апреля',5:'мая',6:'июня',7:'июля',8:'августа',9:'сентября',10:'октября',11:'ноября',12:'декабря'}
# Словарь, возвращающий количесвто дней в определенном месяце
mdays = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}
# Словарь, возвращающий номер дня недели
days = {'Mon':1, 'Tue':2, 'Wed':3, 'Thu':4, 'Fri':5, 'Sat':6, 'Sun':7}
# Список стандартных категорий расходов
categ_sp = ['транспорт', 'продукты', 'кафе и рестораны', 'отдых и развлечения', 'подарки', 'красота и здоровье', 'квартира', 'образование']
# Список стандартных категорий доходов
categ_fin = ['зарплата', 'подарки']


markupSG = types.ReplyKeyboardMarkup()
markupSG.row('**Мой кошелек**','**Мои долги**')
markupSG.row('**Аккаунт**', '**О боте**')

markupAC = types.ReplyKeyboardMarkup()
markupAC.row('**Алиса**')
markupAC.row('**Смена пароля**')
markupAC.row('**Выход**')
markupAC.row('**Удалить аккаунт**','**Сброс данных**')
markupAC.row('**Назад**')

markupUS = types.ReplyKeyboardMarkup()
markupUS.row('**Вход**','**Регистрация**')
markupUS.row('**О боте**')

markupDebt = types.ReplyKeyboardMarkup()
markupDebt.row('**Мои долги**')
markupDebt.row('**Добавить долг**')
markupDebt.row('**Редактировать**')
markupDebt.row('**Назад**')

markupBank = types.ReplyKeyboardMarkup()
markupBank.row('**Баланс**','**Перевод**')
markupBank.row('**Расходы**','**Доходы**')
markupBank.row('**Настройки**','**Лимиты**')
markupBank.row('**Назад**')

markupSettings = types.ReplyKeyboardMarkup()
markupSettings.row('**Новый счет**','**Удалить счет**')
markupSettings.row('**Категории расходов**','**Категории доходов**')
markupSettings.row('**Уведомления**','**Шаблоны**')
markupSettings.row('**Назад**')

markupSpend = types.ReplyKeyboardMarkup()
markupSpend.row('**Отчет по расходам**')
markupSpend.row('**Новый расход**','**Редактировать расход**')
markupSpend.row('**Поменять счет**')
markupSpend.row('**Назад**')

markupFin = types.ReplyKeyboardMarkup()
markupFin.row('**Отчет по доходам**')
markupFin.row('**Новый доход**','**Редактировать доход**')
markupFin.row('**Поменять счет**')
markupFin.row('**Назад**')

markupCat = types.ReplyKeyboardMarkup()
markupCat.row('**Добавить**','**Удалить**')
markupCat.row('**Категории**')
markupCat.row('**Назад**')

markupSZ = types.ReplyKeyboardMarkup()
markupSZ.row('**Отмена**')
markupSZ.row('**Сегодня**')
markupSZ.row('**Вчера**')
markupSZ.row('**Эта неделя**')
markupSZ.row('**Этот месяц**')
markupSZ.row('**Прошлая неделя**')
markupSZ.row('**Прошлый месяц**')
markupSZ.row('**Позапрошлая неделя**')

markupCanc = types.ReplyKeyboardMarkup()
markupCanc.row('**Отмена**')

markupAlice = types.ReplyKeyboardMarkup()
markupAlice.row('**Поменять вопрос**','**Поменять ответ**')
markupAlice.row('**Авторизация диалога**')
markupAlice.row('**Активные сессии**')
markupAlice.row('**Помощь**')
markupAlice.row('**Назад**')

markupRes = types.ReplyKeyboardMarkup()
markupRes.row('**Отмена**')
markupRes.row('**Оставить категории**')
markupRes.row('**Удалить категории**')

markupLim = types.ReplyKeyboardMarkup()
markupLim.row('**Мои лимиты**')
markupLim.row('**Добавить лимит**')
markupLim.row('**Удалить лимит**')
markupLim.row('**Назад**')

markupNotif = types.ReplyKeyboardMarkup()
markupNotif.row('**Мои уведомления**')
markupNotif.row('**Добавить уведомление**')
markupNotif.row('**Убрать уведомление**')
markupNotif.row('**Назад**')

markupTempl = types.ReplyKeyboardMarkup()
markupTempl.row('**Мои шаблоны**')
markupTempl.row('**Добавить шаблон**')
markupTempl.row('**Удалить шаблон**')
markupTempl.row('**Назад**')

MUP = {'main_bank_settings_templates':markupTempl,'main_bank_settings_notif':markupNotif,'main_bank_limits':markupLim,'main_account_reset':markupRes,'main_account_alice':markupAlice,'main_account':markupAC,'mainUS':markupUS,'main':markupSG,'main_debt':markupDebt,'main_bank':markupBank,'main_bank_settings_cat':markupCat,'main_bank_spend':markupSpend,'main_bank_fin_his':markupSZ,'main_bank_spend_his':markupSZ,'main_bank_fin':markupFin,'main_bank_settings':markupSettings}

