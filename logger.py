from configurator import configurator
import pymysql
import traceback
import random
import string
import datetime
import inspect
import time
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
class logger(object):
    # *****************************************************************************************************************************************************************
    def __init__(self,send_method = None,session_id = None):
        self.__send_method__ = send_method
        self.__available_sending_methods__ = ['rabbit','clickhouse','rabbit+clickhouse']
        self.session_id = self.__generate_session_id__() if session_id == None else session_id
        self.logs_collection = []
        self.logs_index = 0
    # *****************************************************************************************************************************************************************
    # Генерация ID текущей сессии логов: запускается 1 раз в момент инициализации класса
    def __generate_session_id__(self):
        try:
            # Генерируем session_id состоящий из 8 латинских символов в верхнем регистре и 4 цифр, всего 3 блока символов по 4шт, разделенных через "-"
            # Пример сгенерированного id: NUIV-DUXW-3825
            session_id = '-'.join([''.join([random.choice(string.ascii_uppercase) for y in range(4)]) for y in range(2)])+'-'+str(random.random())[2:6]
            return(session_id)
        except Exception as error:
            print(f'session id generation error: {error}')
    # *****************************************************************************************************************************************************************
    # Создание словоря с сообщением лога
    def __create_log_message__(self,msg_text,msg_type,lib_name,fnc_name):
        dt = datetime.datetime
        tz = datetime.timezone
        td = datetime.timedelta
        dt_now = dt.now(tz=tz(td(hours=3),name='Europe/Moscow'))
        dt_now_ydm = dt_now.strftime('%Y-%m-%d %H:%M:%S')
        dt_now_dmy = dt_now.strftime('%d.%m.%Y %H:%M:%S')
        uts = round(dt_now.timestamp() * 10**3)
        log_message = {
            'is_sent': 0,
            'uts': uts,
            'session_id': self.session_id,
            'date_now': dt_now,
            'date_ymd': dt_now_ydm,
            'date_dmy': dt_now_dmy,
            'msg_text': msg_text,
            'msg_type': msg_type,
            'lib_name': lib_name,
            'fnc_name': fnc_name}
        return(log_message)
    # *****************************************************************************************************************************************************************
    # Принтует переданное сообщение в консоль
    def __print_log__(self,log_message):
        date_dmy = log_message['date_dmy']
        msg_type = log_message['msg_type']
        msg_text = log_message['msg_text']
        lib_name = log_message['lib_name']
        fnc_name = log_message['fnc_name']
        print(f'[{date_dmy}] [{self.session_id}] [{msg_type}] {msg_text} [fnc="{fnc_name}"][lib="{lib_name}"]')
    # *****************************************************************************************************************************************************************
    # Добавляет переданное сообщение в коллекцию логов
    def __add_log_to_collection__(self,log_message):
        self.logs_index += 1
        logs_index = self.logs_index
        log_message['index'] = logs_index
        self.logs_collection.append(log_message)
        time.sleep(0.000001)
    # *****************************************************************************************************************************************************************
    # Создание нового лога (создаёт сообщение лога + добавляет его в коллекцию + принтует в консоль)
    def addlog(self,msg_text='',msg_type='info',print_msg=True,fnc_name=None,lib_name=None):
        code_obj = inspect.currentframe().f_back.f_code
        if fnc_name == None: fnc_name = code_obj.co_name  
        if lib_name == None: lib_name = code_obj.co_filename.split('\\')[len(code_obj.co_filename.split('\\'))-1].split('/')[-1]
        msg_text = str(msg_text)
        log_message = self.__create_log_message__(
            msg_text=msg_text,
            msg_type=msg_type,
            lib_name=lib_name,
            fnc_name=fnc_name)
        self.__add_log_to_collection__(log_message)
        if print_msg == True:
            self.__print_log__(log_message)
    # *****************************************************************************************************************************************************************
    # Добавляет в логи сообщения о текущих ошибках (если они есть), использовать в секции Except...
    def adderrorlog(self,result={}):
        str_traceback = str(traceback.format_exc())
        if str_traceback == '' or str_traceback == None: return
        list_traceback = str_traceback.split('\n')
        code_obj = inspect.currentframe().f_back.f_code
        fnc_name = code_obj.co_name  
        lib_name = code_obj.co_filename.split('\\')[len(code_obj.co_filename.split('\\'))-1].split('/')[-1]
        list_traceback.remove('')
        str_error = list_traceback[-1]
        log_message = self.__create_log_message__(
            msg_text=str_error,
            msg_type='error',
            lib_name=lib_name,
            fnc_name=fnc_name)
        self.__add_log_to_collection__(log_message)
        self.__print_log__(log_message)
        for line_traceback in list_traceback:
            log_message = self.__create_log_message__(
                msg_text=line_traceback,
                msg_type='traceback',
                lib_name=lib_name,
                fnc_name=fnc_name)
            self.__add_log_to_collection__(log_message)
            self.__print_log__(log_message)
        if 'result' in result: result['result']='error'
        if 'errors' in result: 
            result['errors'].append(str_error)
            for line_traceback in list_traceback:
                result['errors'].append(line_traceback)
        if result != {}: return(result)
    # *****************************************************************************************************************************************************************
    # Возвращает текущую (последнюю) ошибку
    def geterrortext(self):
        str_traceback = str(traceback.format_exc())
        if str_traceback == '' or str_traceback == None: return
        list_traceback = str_traceback.split('\n')
        if list_traceback == [] or list_traceback == None: return
        list_traceback.remove('')
        last_err = ''
        for last_err in reversed(list_traceback):
            if last_err != '': return(last_err)
    # *****************************************************************************************************************************************************************
    def getlogs(self,log_index):
        result_list = []
        if int(log_index) <= 0: return([])
        for message in self.logs_collection:
            if message['index'] > int(log_index):
                result_list.append(message)
        return(result_list)
    # Декоратор для функций: логирует начало и окончание работы функции, аргументы функции (если они переданы), а так же время работы функции
    def log_function(self,log_args=False,log_result=False):
        def decorator(function):
            def wrapper(**kwargs):
                # Получаем инфу о том, откуда (какой либы и функции) вызван декоратор
                code_obj = inspect.currentframe().f_back.f_code
                fnc_name = function.__name__
                lib_name = code_obj.co_filename.split('\\')[len(code_obj.co_filename.split('\\'))-1].split('/')[-1]
                # Создаём лог о том, что функция стартует + засекаем время старта
                log_text = f'function "{fnc_name}" started'
                if kwargs == {} and log_args == True: log_text += ' with no args'
                if kwargs != {} and log_args == True: log_text += ' with args'
                log_message = self.__create_log_message__(msg_text=log_text,msg_type='info',lib_name=lib_name,fnc_name=fnc_name)
                self.__add_log_to_collection__(log_message)
                self.__print_log__(log_message)
                # Если требуется логировать в т.ч. аргументы функции (и они есть) сделаем это
                if log_args == True:
                    for arg_name in kwargs:
                        arg_type = str(type(kwargs[arg_name])).replace("<class '",'"')[0:-2]+'"'
                        arg_value_str = str(kwargs[arg_name])
                        log_text = f'arg "{arg_name}" (type={arg_type}) == "{arg_value_str}"'
                        log_message = self.__create_log_message__(msg_text=log_text,msg_type='info',lib_name=lib_name,fnc_name=fnc_name)
                        self.__add_log_to_collection__(log_message)
                        self.__print_log__(log_message)
                # Начинаем отсчет времени работы функции
                d1 = datetime.datetime.now()
                # Запускаем декорируемую (логируемую) функцию
                function_result = function(**kwargs)
                # Завершаем отсчет времени работы функции
                d2 = datetime.datetime.now()
                # Получаем разницу (время работы функции)
                dd = d2-d1
                # Если там есть микросекунды (6 знаков после ",") - округляем их до милисекунд (3 знака после ",")
                ddstr = str(dd)[0:len(str(dd))-3] if '.' in str(dd) else str(dd)
                # Логируем завершение работы функции + время на выполнение функции
                log_text = f'function "{fnc_name}" done for {ddstr}'
                log_message = self.__create_log_message__(msg_text=log_text,msg_type='info',lib_name=lib_name,fnc_name=fnc_name)
                self.__add_log_to_collection__(log_message)
                self.__print_log__(log_message)
                # Логируем результат выполнения функции:
                if log_result == True:
                    result_type_str = str(type(function_result)).replace("<class '",'')[0:-2]
                    result_text_str = str(function_result)
                    log_text = f'function "{fnc_name}" result (type="{result_type_str}") == "{result_text_str}"'
                    log_message = self.__create_log_message__(msg_text=log_text,msg_type='info',lib_name=lib_name,fnc_name=fnc_name)
                    self.__add_log_to_collection__(log_message)
                    self.__print_log__(log_message)
                # Возвращаем результат работы функции
                return(function_result)
            return(wrapper)
        return(decorator)
    # *****************************************************************************************************************************************************************
    # Декоратор для "главной" функции модуля: логирует начало и окончание работы модуля, а так же общее время работы модуля
    def log_module(self):
        def decorator(function):
            def wrapper(**kwargs):
                code_obj = inspect.currentframe().f_back.f_code
                fnc_name = function.__name__
                lib_name = code_obj.co_filename.split('\\')[len(code_obj.co_filename.split('\\'))-1].split('/')[-1]
                log_text = f'module "{lib_name}" started'
                log_message = self.__create_log_message__(msg_text=log_text,msg_type='info',lib_name=lib_name,fnc_name=fnc_name)
                self.__add_log_to_collection__(log_message)
                self.__print_log__(log_message)
                # Начинаем отсчет времени работы модуля
                d1 = datetime.datetime.now()
                # Запускаем декорируемую функцию
                function_result = function(**kwargs)
                # Завершаем отсчет времени работы функции
                d2 = datetime.datetime.now()
                # Получаем разницу (время работы модуля)
                dd = d2-d1
                # Если там есть микросекунды (6 знаков после ",") - округляем их до милисекунд (3 знака после ",")
                ddstr = str(dd)[0:len(str(dd))-3] if '.' in str(dd) else str(dd)
                # Логируем завершение работы функции + время на выполнение функции
                log_text = f'module "{lib_name}" done for {ddstr}'
                log_message = self.__create_log_message__(msg_text=log_text,msg_type='info',lib_name=lib_name,fnc_name=fnc_name)
                self.__add_log_to_collection__(log_message)
                self.__print_log__(log_message)
                return(function_result)
            return(wrapper)
        return(decorator)
    # *****************************************************************************************************************************************************************
    # Отправка логов в хранилище
    def export(self):
        """Экспорт локальных логов на сервер логирования"""
        result = {'result':[],'errors':[]}
        code_obj = inspect.currentframe().f_back.f_code
        fnc_name = code_obj.co_name  
        lib_name = code_obj.co_filename.split('\\')[len(code_obj.co_filename.split('\\'))-1].split('/')[-1]
        try:
            if len(self.logs_collection)>0:
                rows_to_delete = []
                values = ''
                for row in self.logs_collection:
                    rows_to_delete.append(row)
                    msg_text = row['msg_text']
                    msg_text = msg_text.replace("'","\\'")
                    values += "('"+row['session_id']+"','"+str(row['date_ymd'])+"','"+row['msg_type']+"','"+row['lib_name']+"','"+row['fnc_name']+"','"+msg_text+"'),"
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
        # =============================================================================================================================================================
        # Обработка ошибок
        except Exception as error:
            result['result']='error'
            result['errors'].append(str(error))
            self.addlog(msg_text=str(error),msg_type='error',fnc_name=fnc_name,lib_name=lib_name)
            for traceback_line in str(traceback.format_exc()).split('\n'):
                if traceback_line != '': self.addlog(msg_text=traceback_line,msg_type='traceback',fnc_name=fnc_name,lib_name=lib_name)
            return(result)
# *********************************************************************************************************************************************************************

if __name__ == "__main__":
    pass