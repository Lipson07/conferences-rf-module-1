"""Проверка данных, которые пришли из форм."""
import re
from datetime import date, datetime
 
 
class RegistrationValidator:
    """Проверяет поля формы регистрации. Ошибки собираются в словарь errors."""
 
    LOGIN_RE = re.compile(r"[A-Za-z0-9]{6,}")
    FULL_NAME_RE = re.compile(r"[А-Яа-яЁё ]+")
    PHONE_RE = re.compile(r"8\([0-9]{3}\)[0-9]{3}-[0-9]{2}-[0-9]{2}")
    EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
 
    def __init__(self, form):
        self.form = form
        self.errors = {}
 
    def _value(self, name):
        return self.form.get(name, "").strip()
 
    def validate(self):
        """Вернуть True, если ошибок нет."""
        login = self._value("login")
        if not login:
            self.errors["login"] = "Введите логин"
        elif not self.LOGIN_RE.fullmatch(login):
            self.errors["login"] = "Только латиница и цифры, не менее 6 символов"
        elif len(login) > 50:
            self.errors["login"] = "Логин не длиннее 50 символов"
 
        password = self.form.get("password", "")
        if not password:
            self.errors["password"] = "Введите пароль"
        elif len(password) < 8:
            self.errors["password"] = "Пароль должен быть не короче 8 символов"
 
        full_name = self._value("full_name")
        if not full_name:
            self.errors["full_name"] = "Введите ФИО"
        elif not self.FULL_NAME_RE.fullmatch(full_name):
            self.errors["full_name"] = "Только кириллица и пробелы"
        elif len(full_name) > 150:
            self.errors["full_name"] = "ФИО не длиннее 150 символов"
 
        phone = self._value("phone")
        if not phone:
            self.errors["phone"] = "Введите телефон"
        elif not self.PHONE_RE.fullmatch(phone):
            self.errors["phone"] = "Формат: 8(XXX)XXX-XX-XX"
 
        email = self._value("email")
        if not email:
            self.errors["email"] = "Введите адрес электронной почты"
        elif not self.EMAIL_RE.fullmatch(email):
            self.errors["email"] = "Формат: name@example.ru"
        elif len(email) > 100:
            self.errors["email"] = "Адрес не длиннее 100 символов"
 
        return not self.errors
 
 
def parse_date(text):
    """Превратить строку в дату. Понимает 2027-05-20 и 20.05.2027. Иначе - None."""
    for pattern in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(text.strip(), pattern).date()
        except ValueError:
            continue
    return None
 
 
def is_future_or_today(value):
    return value >= date.today()
