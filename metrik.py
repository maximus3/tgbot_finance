# Модуль для работы с метрикой
from chatbase import Message

# Токен метрики
metrik_key = 'METRIK_TOKEN_HERE'

# Отправка метрики
# Вход: платформа, id пользователя, сообщение, шаг, сообщение не распознано (True/False)
# Выход: -
def send_metrik(pfm, user_id, msg, step, handl):
    msg = Message(api_key=metrik_key,
                  platform=pfm,
                  user_id=user_id,
                  message=msg,
                  intent=pfm + "_" + step,
                  not_handled=handl)
    resp = msg.send()
