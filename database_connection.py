import sqlite3
import sys


class DBConnection:
    sql_init_query = '''
        CREATE TABLE IF NOT EXISTS gmail_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT NOT NULL,
            token TEXT NOT NULL
    )
    '''

    sql_add_account = 'INSERT INTO gmail_accounts(account_name, token) VALUES (%s, %s)'

    def __init__(self, creds_and_params, logger):
        self.__creds_and_params = creds_and_params
        self.__logger = logger
        try:
            self.get_sqlite_cursor().execute(DBConnection.sql_init_query)
        except sqlite3.Error as e:
            self.__logger.exception(f"Error occurs during init of db file: {e}")
            sys.exit()

    def get_sqlite_cursor(self):
        try:
            with sqlite3.connect(self.__creds_and_params['sqlite_db_name']) as conn:
                cur = conn.cursor()
                return cur
        except sqlite3.Error as e:
            self.__logger.exception(f'Error occurs during establishing connection and getting cursor {e}')

    def add_account(self, account_name, token):
        try:
            self.get_sqlite_cursor().execute(DBConnection.sql_add_account, (account_name, token))
            return True
        except sqlite3.Error as e:
            self.__logger.exception(e)
            return False
