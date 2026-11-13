"""Портал «Конференции.РФ» - главный файл приложения (маршруты Flask)."""
from functools import wraps
 
from flask import Flask, flash, redirect, render_template, request, session, url_for
 
import config
from db import Database
from repositories import BookingRepository, ReviewRepository, RoomRepository, UserRepository
from validators import RegistrationValidator, is_future_or_today, parse_date
 
app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", MAX_CONTENT_LENGTH=64 * 1024)
 
# Объекты для работы с таблицами
db = Database(config.DB_SETTINGS)
users = UserRepository(db)
rooms = RoomRepository(db)
bookings = BookingRepository(db)
reviews = ReviewRepository(db)
 
 
# ---------- Декораторы доступа ----------
 
def login_required(view):
    """Пускать на страницу только вошедших пользователей."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Сначала войдите в систему", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper
 
 
def admin_required(view):
    """Пускать на страницу только администратора."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Доступ только для администратора", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper
 
 
# ---------- Главная, регистрация, вход, выход ----------
 
@app.route("/")
def index():
    return render_template("index.html", rooms=rooms.all())
 
 
@app.route("/register", methods=["GET", "POST"])
def register():
    errors = {}
    form = request.form
    if request.method == "POST":
        validator = RegistrationValidator(form)
        if not validator.validate():
            errors = validator.errors
        elif users.login_exists(form["login"].strip()):
            errors = {"login": "Такой логин уже занят"}
        else:
            users.create(
                form["login"].strip(),
                form["password"],
                form["full_name"].strip(),
                form["phone"].strip(),
                form["email"].strip(),
            )
            flash("Пользователь создан. Теперь войдите в систему.", "success")
            return redirect(url_for("login"))
    return render_template("register.html", errors=errors, form=form)
 
 
@app.route("/login", methods=["GET", "POST"])
def login():
    errors = {}
    form = request.form
    if request.method == "POST":
        login_value = form.get("login", "").strip()
        password = form.get("password", "")
        if not login_value:
            errors["login"] = "Введите логин"
        if not password:
            errors["password"] = "Введите пароль"
        if not errors:
            user = users.authenticate(login_value, password)
            if user is None:
                errors["common"] = "Неверный логин или пароль"
            else:
                session.clear()
                session["user_id"] = user["id"]
                session["role"] = user["role"]
                session["full_name"] = user["full_name"]
                if user["role"] == "admin":
                    return redirect(url_for("admin"))
                return redirect(url_for("cabinet"))
    return render_template("login.html", errors=errors, form=form)
 
 
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))
 
 
# ---------- Личный кабинет пользователя ----------
 
@app.route("/cabinet")
@login_required
def cabinet():
    return render_template("cabinet.html", bookings=bookings.for_user(session["user_id"]))
 
 
@app.route("/booking/new", methods=["GET", "POST"])
@login_required
def booking_new():
    errors = {}
    form = request.form
    if request.method == "POST":
        # Помещение: из выпадающего списка (room_id) или из текстового поля (room_name)
        if form.get("room_id"):
            room = rooms.get(form["room_id"])
        else:
            room = rooms.find_by_name(form.get("room_name", "").strip())
        if room is None:
            errors["room"] = "Выберите помещение из списка"
 
        start_date = parse_date(form.get("start_date", ""))
        if start_date is None:
            errors["start_date"] = "Укажите дату в формате ДД.ММ.ГГГГ"
        elif not is_future_or_today(start_date):
            errors["start_date"] = "Дата не может быть в прошлом"
 
        payment = form.get("payment_method", "")
        if payment not in BookingRepository.PAYMENT_METHODS:
            errors["payment_method"] = "Выберите способ оплаты"

        raw_participants = form.get("participants", "").strip()
        if not raw_participants.isascii() or not raw_participants.isdigit() or not 1 <= int(raw_participants) <= 500:
            errors["participants"] = "Введите целое число от 1 до 500"
 
        if not errors:
            bookings.create(session["user_id"], room["id"], start_date, payment, int(raw_participants))
            flash("Заявка отправлена администратору", "success")
            return redirect(url_for("cabinet"))
    return render_template(
        "booking_new.html",
        errors=errors,
        form=form,
        rooms=rooms.all(),
        payment_methods=BookingRepository.PAYMENT_METHODS,
    )
 
 
@app.route("/booking/<int:booking_id>/delete", methods=["POST"])
@login_required
def booking_delete(booking_id):
    booking = bookings.get(booking_id)
    if booking and booking["user_id"] == session["user_id"] and booking["status"] == "Новая":
        bookings.delete(booking_id)
        flash("Заявка удалена", "success")
    return redirect(url_for("cabinet"))
 
 
@app.route("/booking/<int:booking_id>/review", methods=["POST"])
@login_required
def booking_review(booking_id):
    booking = bookings.get(booking_id)
    text = request.form.get("text", "").strip()
    if not booking or booking["user_id"] != session["user_id"]:
        flash("Заявка не найдена", "danger")
    elif booking["status"] != "Завершено":
        flash("Отзыв можно оставить только после завершения мероприятия", "warning")
    elif not text:
        flash("Напишите текст отзыва", "warning")
    else:
        reviews.create(booking_id, text)
        flash("Спасибо за отзыв!", "success")
    return redirect(url_for("cabinet"))
 
 
# ---------- Панель администратора ----------
 
@app.route("/admin")
@admin_required
def admin():
    status = request.args.get("status", "")
    room_id = request.args.get("room_id", "")
    if status not in BookingRepository.STATUSES:
        status = ""
    if not room_id.isascii() or not room_id.isdigit():
        room_id = ""
    return render_template(
        "admin.html",
        bookings=bookings.all(status or None, int(room_id) if room_id else None),
        statuses=BookingRepository.STATUSES,
        current_status=status,
        current_room=room_id,
        rooms=rooms.all(),
    )
 
 
@app.route("/admin/booking/<int:booking_id>/status", methods=["POST"])
@admin_required
def admin_change_status(booking_id):
    try:
        bookings.update_status(booking_id, request.form.get("status", ""))
        flash(f"Статус заявки №{booking_id} изменён", "success")
    except ValueError:
        flash("Недопустимый статус", "danger")
    return redirect(url_for("admin", status=request.args.get("status", "")))
 
 
@app.route("/admin/booking/<int:booking_id>/delete", methods=["POST"])
@admin_required
def admin_delete(booking_id):
    bookings.delete(booking_id)
    flash(f"Заявка №{booking_id} удалена", "success")
    return redirect(url_for("admin"))
 
 
if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=False)
