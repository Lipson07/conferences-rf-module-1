"""Создание администратора портала (логин Conf2027, пароль Demo77).
 
Запуск один раз после создания таблиц:  python create_admin.py
"""
import config
from db import Database
from repositories import UserRepository
 
users = UserRepository(Database(config.DB_SETTINGS))
 
if users.login_exists("Conf2027"):
    print("Администратор уже существует")
else:
    users.create(
        login="Conf2027",
        password="Demo77",
        full_name="Администратор портала",
        phone="8(000)000-00-00",
        email="admin@conf.ru",
        role="admin",
    )
    print("Администратор создан: Conf2027 / Demo77")
