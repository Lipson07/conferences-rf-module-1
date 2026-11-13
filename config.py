"""Настройки приложения «Конференции.РФ»."""
import os
import secrets
 
# Параметры подключения к PostgreSQL
DB_SETTINGS = {
    "host": os.getenv("PGHOST", "localhost"),
    "port": int(os.getenv("PGPORT", "5432")),
    "dbname": os.getenv("PGDATABASE", "conferences"),
    "user": os.getenv("PGUSER", "conf_user"),
    "password": os.getenv("PGPASSWORD", "conf_pass"),
}
 
# Секретный ключ нужен Flask для работы сессий (входа в систему)
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
