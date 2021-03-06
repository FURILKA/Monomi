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
    # Выполнение sql-запроса
    def execute(self,request='',NO_BACKSLASH_ESCAPES=False):
        try:
            sqlCon = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.pwrd,
                db=self.base,
                cursorclass=pymysql.cursors.DictCursor
                )
            sqlCur = sqlCon.cursor()
            if NO_BACKSLASH_ESCAPES == True: sqlCur.execute("SET SESSION sql_mode = 'NO_BACKSLASH_ESCAPES'")
            sqlCur.execute(request)
            result = sqlCur.fetchall()
            sqlCon.commit()
            sqlCur.close()
            sqlCon.close()
        except Exception as error:
            sqlerror = str(error)
            self.LLC.addlog('error due executing SQL-request:\n' + request,'error')
            self.LLC.addlog(sqlerror,'error')
            raise pymysql.InternalError('Ошибка при обработке SQL-запроса')
        return(result)
# ==================================================================================================================================================================
