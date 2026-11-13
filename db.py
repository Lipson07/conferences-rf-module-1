"""Работа с базой данных PostgreSQL."""
import psycopg2
from psycopg2.extras import RealDictCursor
 
 
class Database:
    """Отвечает только за выполнение SQL-запросов."""
 
    def __init__(self, settings):
        self.settings = settings
 
    def _run(self, sql, params, fetch):
        """Открыть соединение, выполнить запрос, сохранить изменения, закрыть соединение."""
        connection = psycopg2.connect(**self.settings)
        try:
            with connection:  # при успехе - COMMIT, при ошибке - ROLLBACK
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql, params)
                    if fetch == "one":
                        return cursor.fetchone()
                    if fetch == "all":
                        return cursor.fetchall()
                    return None
        finally:
            connection.close()
 
    def fetch_all(self, sql, params=None):
        """SELECT, который возвращает список строк (каждая строка - словарь)."""
        return self._run(sql, params, "all")
 
    def fetch_one(self, sql, params=None):
        """SELECT, который возвращает одну строку или None."""
        return self._run(sql, params, "one")
 
    def execute(self, sql, params=None):
        """INSERT, UPDATE или DELETE."""
        self._run(sql, params, None)
