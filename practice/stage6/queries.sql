-- Аналитические запросы этапа 6. Выполнять в базе conferences после schema.sql.

-- Количество заявок в каждом статусе.
SELECT status, COUNT(*) AS booking_count
FROM bookings GROUP BY status ORDER BY status;

-- Заявки на кинозалы.
SELECT b.id, u.full_name, r.name, b.start_date, b.status
FROM bookings b JOIN rooms r ON r.id=b.room_id JOIN users u ON u.id=b.user_id
WHERE r.room_type='Кинозал' ORDER BY b.start_date;

-- Пользователи, у которых нет заявок.
SELECT u.id, u.login, u.full_name
FROM users u LEFT JOIN bookings b ON b.user_id=u.id
WHERE b.id IS NULL AND u.role='user' ORDER BY u.id;

-- Будущие заявки по дате.
SELECT b.id, r.name, b.start_date
FROM bookings b JOIN rooms r ON r.id=b.room_id
WHERE b.start_date>CURRENT_DATE ORDER BY b.start_date, b.id;

-- Проверка связей и структуры.
SELECT table_name, column_name, data_type
FROM information_schema.columns WHERE table_schema='public'
ORDER BY table_name, ordinal_position;

-- CRUD в пределах транзакции: демонстрационные изменения откатываются.
BEGIN;
INSERT INTO users(login,password_hash,full_name,phone,email)
VALUES('practice2027','demonstration-only','Тестов Тест','8(900)000-00-01','test@example.ru');
INSERT INTO bookings(user_id,room_id,start_date,payment_method,participants)
SELECT u.id,r.id,CURRENT_DATE+1,'При очном посещении',10
FROM users u CROSS JOIN rooms r WHERE u.login='practice2027' AND r.name='Аудитория «Москва»';
SELECT b.*,u.full_name,r.name FROM bookings b
JOIN users u ON u.id=b.user_id JOIN rooms r ON r.id=b.room_id WHERE u.login='practice2027';
UPDATE bookings SET status='Мероприятие назначено'
WHERE user_id=(SELECT id FROM users WHERE login='practice2027');
DELETE FROM bookings WHERE user_id=(SELECT id FROM users WHERE login='practice2027');
ROLLBACK;
