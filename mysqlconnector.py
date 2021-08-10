import pymysql
# ==================================================================================================================================================================
# Класс для работы бота с его базой данных mySQL
# Для инициализации класса нужно передать IP хоста, логин, пароль и наименование базы данных, а так же объект LLC для логирования событий на случай ошибок
# > connect : подключение к БД - перед работой с БД к ней нужно подключиться
# > disconnect : отключение от БД - после работы от БД необходимо отключиться
# > isConnected : проверяет наличие подключения к БД, возвращает True если подключение есть и False если его нет
# > execute : выполняет sql-запрос и возвращает его результат
# ==================================================================================================================================================================
class mySQLConnector(object):
    """Класс для работы с БД mySQL"""
    # **************************************************************************************************************************************************************
    # Инициализация класса
    def __init__(self,host,user,pwrd,base,LocalLogCollector):
        self.host = host
        self.user = user
        self.pwrd = pwrd
        self.base = base
        self.LLC  = LocalLogCollector
    # **************************************************************************************************************************************************************
    # Подключение к базе
    def connect(self):
        try:    
            self.sqlCon = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.pwrd,
                db=self.base,
                cursorclass=pymysql.cursors.DictCursor
                )
        except Exception as e:
            self.LLC.addlog('error due connection to SQL-server','error')
            self.LLC.addlog(str(e),'error')
    # **************************************************************************************************************************************************************
    # Проверка состояния подключения - вернет True если всё хорошо, вернет False если есть проблемы с выполнением запросов
    def isConnected(self):
        try:
            sqlCur = self.sqlCon.cursor()
            sqlCur.execute('SELECT 1')
            return(True)
        except Exception as e:
            self.LLC.addlog('MariaDB.isConnect = False','error')
            self.LLC.addlog(str(e),'error')
            return(False)
    # **************************************************************************************************************************************************************
    # Отключение от сервера БД (закрытие сессии)
    def disconnect(self):
        try:
            self.sqlCon.close()
        except Exception as e:
            self.LLC.addlog('error due closing SQL-connection','error')
            self.LLC.addlog(str(e),'error')
    # **************************************************************************************************************************************************************
    # Выполнение sql-запроса
    def execute(self,request=''):
        try:
            sqlCur = self.sqlCon.cursor()
            sqlCur.execute(request)
            self.sqlCon.commit()
            return(sqlCur.fetchall())
        except Exception as e:
            self.LLC.addlog('error due executing SQL-request: ' + request,'error')
            self.LLC.addlog(str(e),'error')
# ==================================================================================================================================================================
