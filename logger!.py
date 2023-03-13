from datetime import datetime
from configurator import configurator
import pymysql
import inspect
import random
import os
# ==================================================================================================================================================================
# Класс "LocalLogCollector" (сокращенно LLC)
# При создании генерирует рандомный ID сиссии, далее собирает локальную коллекцию логов. Каждый элемент коллекции содержит:
# 1) Время события
# 2) Рандомный ID сессии в виде ХХХХ-ХХХХ-ХХХХ-ХХХХ (где Х рандомная цифра 0-9), генерируется при запуске бота и действует всё время до перезапуска
# 3) Тип события. По умолчанию 'info', может быть 'error', 'warning' и т.д.
# 4) Тест сообщения/лога
# 5) Название функции-отправителя лога
# 6) Название модуля-отправителя лога
# После сбора коллекции её необходимо отправить на сервер. Если этого не сделать - логи будут потеряны
# Автоматически отправляет логи на сервер в том случае, если в коллекции собирается 100+ событий ИЛИ если type == 'error'
# ==================================================================================================================================================================
class LocalLogCollector(object):
    # **************************************************************************************************************************************************************
    """Класс для локальной агрегации логов работы скрипта и последующем экспорте логов на сервер"""
    def __init__(self):
        """Инициализация класса"""
        self.logs_collection = []
        self.SessionID = str(random.random())[2:6]+'-'+str(random.random())[2:6]+'-'+str(random.random())[2:6]
    # **************************************************************************************************************************************************************
    def addlog(self, msg_text='', msg_type='info'):
        """Добавление лога в коллекцию"""
        try:
            current_frame = inspect.currentframe()
            caller_frame = current_frame.f_back
            code_obj = caller_frame.f_code
            function_name = code_obj.co_name  
            lib_name = code_obj.co_filename.split('\\')[-1]
            msg_id = self.SessionID
            self.logs_collection.append(
                {
                'id': msg_id,
                'message': msg_text,
                'type': msg_type,
                'date': str(datetime.now())[0:19],
                'lib_name': lib_name,
                'function_name': function_name
                })
            val = '[' + msg_type + '] ' + msg_text
            if type(val) != str: val = str(val)
            if self.SessionID != 0: val = '[ID:' + str(self.SessionID) + '] ' + val
            print('[' + str(datetime.now())[0:19].replace('-','.') + '] ' + val + ' (function_name="' + function_name + '",lib_name="' + lib_name + '")')
            if msg_type == 'error' or len(self.logs_collection)>100:
                self.export()
        except Exception as ex:
            print(str(ex))
    # **************************************************************************************************************************************************************
    def export(self):
        """Экспорт локальных логов на сервер логирования"""
        try:
            if len(self.logs_collection)>0:
                rows_to_delete = []
                values = ''
                for row in self.logs_collection:
                    rows_to_delete.append(row)
                    msg_text = row['message']
                    msg_text = msg_text.replace("'","\\'")
                    values += "('"+row['id']+"','"+str(row['date'])+"','"+row['type']+"','"+row['lib_name']+"','"+row['function_name']+"','"+msg_text+"'),"
                values = values[0:-1]
                config = configurator(os.path.dirname(os.path.realpath(__file__))+"/config/config.ini")
                sqlCon = pymysql.connect(
                    host = config.get(section='mySQL',setting='host'),
                    user = config.get(section='mySQL',setting='user'),
                    password = config.get(section='mySQL',setting='pass'),
                    db = config.get(section='mySQL',setting='base'),
                    cursorclass = pymysql.cursors.DictCursor
                    )
                sqlCur = sqlCon.cursor()
                query = 'INSERT INTO bot_logs(session_id,date,type,library,function,message) VALUES ' + values
                sqlCur.execute(query)
                sqlCon.commit()
                sqlCon.close()
                for row in rows_to_delete:
                    self.logs_collection.remove(row)
        except Exception as ex:
            print(str(ex))
# ==================================================================================================================================================================
