"""Классы-репозитории: каждый отвечает за свою таблицу."""
from werkzeug.security import check_password_hash, generate_password_hash
 
 
class UserRepository:
    """Пользователи: регистрация и вход."""
 
    def __init__(self, db):
        self.db = db
 
    def login_exists(self, login):
        row = self.db.fetch_one("SELECT id FROM users WHERE login = %s", (login,))
        return row is not None
 
    def create(self, login, password, full_name, phone, email, role="user"):
        # Пароль никогда не храним в открытом виде - только его хеш
        self.db.execute(
            "INSERT INTO users (login, password_hash, full_name, phone, email, role) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (login, generate_password_hash(password), full_name, phone, email, role),
        )
 
    def authenticate(self, login, password):
        """Вернуть пользователя, если логин и пароль верные, иначе None."""
        user = self.db.fetch_one("SELECT * FROM users WHERE login = %s", (login,))
        if user and check_password_hash(user["password_hash"], password):
            return user
        return None
 
 
class RoomRepository:
    """Помещения для конференций."""
 
    def __init__(self, db):
        self.db = db
 
    def all(self):
        return self.db.fetch_all("SELECT * FROM rooms ORDER BY room_type, name")
 
    def get(self, room_id):
        return self.db.fetch_one("SELECT * FROM rooms WHERE id = %s", (room_id,))
 
    def find_by_name(self, name):
        # casefold understands Cyrillic even when PostgreSQL uses locale C.
        expected = name.strip().casefold()
        return next((room for room in self.all() if room["name"].casefold() == expected), None)
 
 
class BookingRepository:
    """Заявки на бронирование: создание, чтение, изменение, удаление (CRUD)."""
 
    STATUSES = ("Новая", "Мероприятие назначено", "Завершено")
    PAYMENT_METHODS = ("При очном посещении", "Перевод по СБП")
 
    def __init__(self, db):
        self.db = db
 
    def create(self, user_id, room_id, start_date, payment_method, participants=10):
        self.db.execute(
            "INSERT INTO bookings (user_id, room_id, start_date, payment_method, participants) "
            "VALUES (%s, %s, %s, %s, %s)",
            (user_id, room_id, start_date, payment_method, participants),
        )
 
    def get(self, booking_id):
        return self.db.fetch_one("SELECT * FROM bookings WHERE id = %s", (booking_id,))
 
    def for_user(self, user_id):
        """Заявки одного пользователя вместе с названием помещения и отзывом."""
        return self.db.fetch_all(
            "SELECT b.*, TO_CHAR(b.start_date, 'DD.MM.YYYY') AS start_date_text, "
            "r.name AS room_name, rv.text AS review_text "
            "FROM bookings b "
            "JOIN rooms r ON r.id = b.room_id "
            "LEFT JOIN reviews rv ON rv.booking_id = b.id "
            "WHERE b.user_id = %s "
            "ORDER BY b.created_at DESC",
            (user_id,),
        )
 
    def all(self, status=None, room_id=None):
        """Все заявки для администратора; status - необязательный фильтр."""
        sql = (
            "SELECT b.*, TO_CHAR(b.start_date, 'DD.MM.YYYY') AS start_date_text, "
            "r.name AS room_name, u.full_name, u.phone, u.email "
            "FROM bookings b "
            "JOIN rooms r ON r.id = b.room_id "
            "JOIN users u ON u.id = b.user_id "
        )
        params = []
        conditions = []
        if status:
            conditions.append("b.status = %s")
            params.append(status)
        if room_id:
            conditions.append("b.room_id = %s")
            params.append(room_id)
        if conditions:
            sql += "WHERE " + " AND ".join(conditions) + " "
        sql += "ORDER BY b.created_at DESC"
        return self.db.fetch_all(sql, params)
 
    def update_status(self, booking_id, status):
        if status not in self.STATUSES:
            raise ValueError("Недопустимый статус")
        self.db.execute(
            "UPDATE bookings SET status = %s WHERE id = %s", (status, booking_id)
        )
 
    def delete(self, booking_id):
        self.db.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
 
 
class ReviewRepository:
    """Отзывы о проведённых мероприятиях."""
 
    def __init__(self, db):
        self.db = db
 
    def create(self, booking_id, text):
        self.db.execute(
            "INSERT INTO reviews (booking_id, text) VALUES (%s, %s) "
            "ON CONFLICT (booking_id) DO NOTHING", (booking_id, text)
        )
