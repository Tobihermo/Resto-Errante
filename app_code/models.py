from .database import get_db_connection
import sqlite3
import json

class User:
    @staticmethod
    def create(username, first_name, last_name, dni, email, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (username, first_name, last_name, dni, email, password) VALUES (?, ?, ?, ?, ?, ?)',
                (username, first_name, last_name, dni, email, password)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_by_username(username):
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        return user

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE id = ?', (user_id,)
        ).fetchone()
        conn.close()
        return user

    @staticmethod
    def update_balance(user_id, amount):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET balance = balance + ? WHERE id = ?',
            (amount, user_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_profile(user_id, first_name, last_name, email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE users SET first_name = ?, last_name = ?, email = ? WHERE id = ?',
            (first_name, last_name, email, user_id)
        )
        conn.commit()
        conn.close()

class Reservation:
    @staticmethod
    def create(title, date, short_description, long_description, location, 
               event_type_id, is_free, price, creator_id, table_count, 
               guest_count, special_requirements, is_private=False, access_code=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO reservations 
            (title, date, short_description, long_description, location, 
             event_type_id, is_free, price, creator_id, table_count,
             guest_count, special_requirements, is_private, access_code) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (title, date, short_description, long_description, location,
             event_type_id, is_free, price, creator_id, table_count,
             guest_count, special_requirements, is_private, access_code)
        )
        reservation_id = cursor.lastrowid
        
        cursor.execute(
            'INSERT INTO reservation_attendees (user_id, reservation_id) VALUES (?, ?)',
            (creator_id, reservation_id)
        )
        
        conn.commit()
        conn.close()
        return reservation_id

    @staticmethod
    def get_all():
        conn = get_db_connection()
        reservations = conn.execute('''
            SELECT r.*, u.username as creator_username, et.name as event_type_name
            FROM reservations r 
            JOIN users u ON r.creator_id = u.id 
            LEFT JOIN event_types et ON r.event_type_id = et.id
            WHERE r.is_cancelled = FALSE 
            ORDER BY r.date
        ''').fetchall()
        conn.close()
        return reservations

    @staticmethod
    def get_by_id(reservation_id):
        conn = get_db_connection()
        reservation = conn.execute('''
            SELECT r.*, u.username as creator_username, et.name as event_type_name
            FROM reservations r 
            JOIN users u ON r.creator_id = u.id 
            LEFT JOIN event_types et ON r.event_type_id = et.id
            WHERE r.id = ?
        ''', (reservation_id,)).fetchone()
        conn.close()
        return reservation

    @staticmethod
    def get_by_creator(creator_id):
        conn = get_db_connection()
        reservations = conn.execute('''
            SELECT r.*, et.name as event_type_name 
            FROM reservations r 
            LEFT JOIN event_types et ON r.event_type_id = et.id
            WHERE creator_id = ? 
            ORDER BY date
        ''', (creator_id,)).fetchall()
        conn.close()
        return reservations

    @staticmethod
    def search_reservations(query=None, event_type=None, is_free=None):
        conn = get_db_connection()
        sql = '''
            SELECT r.*, u.username as creator_username, et.name as event_type_name
            FROM reservations r 
            JOIN users u ON r.creator_id = u.id 
            LEFT JOIN event_types et ON r.event_type_id = et.id
            WHERE r.is_cancelled = FALSE AND r.is_private = FALSE
        '''
        params = []
        
        if query:
            sql += ' AND (r.title LIKE ? OR r.short_description LIKE ?)'
            params.extend([f'%{query}%', f'%{query}%'])
        
        if event_type:
            sql += ' AND r.event_type_id = ?'
            params.append(event_type)
        
        if is_free is not None:
            sql += ' AND r.is_free = ?'
            params.append(is_free)
        
        sql += ' ORDER BY r.date'
        
        reservations = conn.execute(sql, params).fetchall()
        conn.close()
        return reservations

    @staticmethod
    def cancel_reservation(reservation_id, creator_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE reservations SET is_cancelled = TRUE WHERE id = ? AND creator_id = ?',
            (reservation_id, creator_id)
        )
        
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_access_code(access_code):
        conn = get_db_connection()
        reservation = conn.execute('''
            SELECT r.*, u.username as creator_username, et.name as event_type_name
            FROM reservations r 
            JOIN users u ON r.creator_id = u.id 
            LEFT JOIN event_types et ON r.event_type_id = et.id
            WHERE r.access_code = ? AND r.is_private = TRUE AND r.is_cancelled = FALSE
        ''', (access_code,)).fetchone()
        conn.close()
        return reservation

    @staticmethod
    def get_reservation_tables(reservation_id):
        """Obtener mesas de una reserva"""
        conn = get_db_connection()
        tables = conn.execute('''
            SELECT t.* FROM tables t
            JOIN reservation_tables rt ON t.table_number = rt.table_number
            WHERE rt.reservation_id = ?
            ORDER BY t.table_number
        ''', (reservation_id,)).fetchall()
        conn.close()
        return tables

    @staticmethod
    def add_tables_to_reservation(reservation_id, table_numbers):
        """Agregar mesas a una reserva"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for table_number in table_numbers:
            cursor.execute(
                'INSERT OR IGNORE INTO reservation_tables (reservation_id, table_number) VALUES (?, ?)',
                (reservation_id, table_number)
            )
        
        conn.commit()
        conn.close()

class ReservationAttendee:
    @staticmethod
    def attend_reservation(user_id, reservation_id, tickets_count=1, food_selections=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            food_json = json.dumps(food_selections) if food_selections else None
            cursor.execute(
                '''INSERT INTO reservation_attendees (user_id, reservation_id, tickets_count, food_selections) 
                VALUES (?, ?, ?, ?)''',
                (user_id, reservation_id, tickets_count, food_json)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def cancel_attendance(user_id, reservation_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM reservation_attendees WHERE user_id = ? AND reservation_id = ?',
            (user_id, reservation_id)
        )
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0

    @staticmethod
    def get_user_reservations(user_id):
        conn = get_db_connection()
        reservations = conn.execute('''
            SELECT r.*, ra.tickets_count, ra.food_selections, u.username as creator_username, et.name as event_type_name
            FROM reservations r
            JOIN reservation_attendees ra ON r.id = ra.reservation_id
            JOIN users u ON r.creator_id = u.id
            LEFT JOIN event_types et ON r.event_type_id = et.id
            WHERE ra.user_id = ? AND r.is_cancelled = FALSE
            ORDER BY r.date
        ''', (user_id,)).fetchall()
        conn.close()
        return reservations

    @staticmethod
    def is_attending(user_id, reservation_id):
        conn = get_db_connection()
        attendance = conn.execute(
            'SELECT * FROM reservation_attendees WHERE user_id = ? AND reservation_id = ?',
            (user_id, reservation_id)
        ).fetchone()
        conn.close()
        return attendance is not None

    @staticmethod
    def remove_tables_from_reservation(reservation_id):
        """Eliminar todas las mesas asociadas a una reserva"""
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM reservation_tables WHERE reservation_id = ?',
            (reservation_id,)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_attendees(reservation_id):
        """Obtener todos los asistentes de una reserva"""
        conn = get_db_connection()
        attendees = conn.execute('''
            SELECT u.id, u.username, u.email 
            FROM reservation_attendees ra
            JOIN users u ON ra.user_id = u.id
            WHERE ra.reservation_id = ?
        ''', (reservation_id,)).fetchall()
        conn.close()
        return attendees

class Menu:
    @staticmethod
    def get_all_categories():
        conn = get_db_connection()
        categories = conn.execute('SELECT * FROM food_categories ORDER BY name').fetchall()
        conn.close()
        return categories

    @staticmethod
    def get_items_by_category(category_id=None):
        conn = get_db_connection()
        if category_id:
            items = conn.execute(
                'SELECT * FROM menu_items WHERE category_id = ? ORDER BY name',
                (category_id,)
            ).fetchall()
        else:
            items = conn.execute('SELECT * FROM menu_items ORDER BY category_id, name').fetchall()
        conn.close()
        return items

    @staticmethod
    def get_item_by_id(item_id):
        conn = get_db_connection()
        item = conn.execute(
            'SELECT mi.*, fc.name as category_name FROM menu_items mi JOIN food_categories fc ON mi.category_id = fc.id WHERE mi.id = ?',
            (item_id,)
        ).fetchone()
        conn.close()
        return item

class EventType:
    @staticmethod
    def get_all():
        conn = get_db_connection()
        types = conn.execute('SELECT * FROM event_types ORDER BY name').fetchall()
        conn.close()
        return types

class Notification:
    @staticmethod
    def create(user_id, title, message, type='info', related_reservation_id=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO notifications (user_id, title, message, type, related_reservation_id) 
            VALUES (?, ?, ?, ?, ?)''',
            (user_id, title, message, type, related_reservation_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_user_notifications_with_details(user_id):
        """Obtener notificaciones con detalles de reservas"""
        conn = get_db_connection()
        notifications = conn.execute('''
            SELECT n.*, r.title as reservation_title 
            FROM notifications n
            LEFT JOIN reservations r ON n.related_reservation_id = r.id
            WHERE n.user_id = ?
            ORDER BY n.created_at DESC
        ''', (user_id,)).fetchall()
        conn.close()
        return notifications

    @staticmethod
    def get_unread_count(user_id):
        """Obtener numero de notificaciones no leídas"""
        conn = get_db_connection()
        count = conn.execute(
            'SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = FALSE',
            (user_id,)
        ).fetchone()[0]
        conn.close()
        return count

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Marcar una notificacion como leida"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE notifications SET is_read = TRUE WHERE id = ? AND user_id = ?',
            (notification_id, user_id)
        )
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0

    @staticmethod
    def mark_all_as_read(user_id):
        """Marcar todas las notificaciones como leidas"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE notifications SET is_read = TRUE WHERE user_id = ? AND is_read = FALSE',
            (user_id,)
        )
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows

class Review:
    @staticmethod
    def create(reservation_id, user_id, rating, comment=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO reviews (reservation_id, user_id, rating, comment) VALUES (?, ?, ?, ?)',
                (reservation_id, user_id, rating, comment)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def get_by_reservation(reservation_id):
        """Obtener todas las reseñas de una reserva"""
        conn = get_db_connection()
        reviews = conn.execute('''
            SELECT r.*, u.username, u.first_name, u.last_name
            FROM reviews r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.reservation_id = ?
            ORDER BY r.created_at DESC
        ''', (reservation_id,)).fetchall()
        conn.close()
        return reviews

    @staticmethod
    def user_has_reviewed(reservation_id, user_id):
        """Verificar si un usuario ya dejo reseña para una reserva"""
        conn = get_db_connection()
        review = conn.execute(
            'SELECT * FROM reviews WHERE reservation_id = ? AND user_id = ?',
            (reservation_id, user_id)
        ).fetchone()
        conn.close()
        return review is not None

    @staticmethod
    def delete_review(review_id, user_id):
        """Eliminar una reseña (solo el usuario que la creo)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'DELETE FROM reviews WHERE id = ? AND user_id = ?',
            (review_id, user_id)
        )
        affected_rows = cursor.rowcount
        conn.commit()
        conn.close()
        return affected_rows > 0

class Favorite:
    @staticmethod
    def get_user_favorites(user_id):
        conn = get_db_connection()
        favorites = conn.execute('''
            SELECT r.*, u.username as creator_username, et.name as event_type_name
            FROM reservations r
            JOIN users u ON r.creator_id = u.id
            LEFT JOIN event_types et ON r.event_type_id = et.id
            JOIN user_favorites uf ON r.id = uf.reservation_id
            WHERE uf.user_id = ? AND r.is_cancelled = FALSE
            ORDER BY r.date
        ''', (user_id,)).fetchall()
        conn.close()
        return favorites

    @staticmethod
    def add_favorite(user_id, reservation_id):
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT OR IGNORE INTO user_favorites (user_id, reservation_id) VALUES (?, ?)',
                (user_id, reservation_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    @staticmethod
    def remove_favorite(user_id, reservation_id):
        conn = get_db_connection()
        conn.execute(
            'DELETE FROM user_favorites WHERE user_id = ? AND reservation_id = ?',
            (user_id, reservation_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def is_favorite(user_id, reservation_id):
        conn = get_db_connection()
        favorite = conn.execute(
            'SELECT * FROM user_favorites WHERE user_id = ? AND reservation_id = ?',
            (user_id, reservation_id)
        ).fetchone()
        conn.close()
        return favorite is not None

class Table:
    @staticmethod
    def get_available_tables():
        conn = get_db_connection()
        tables = conn.execute('''
            SELECT * FROM tables 
            WHERE is_available = TRUE 
            ORDER BY table_number
        ''').fetchall()
        conn.close()
        return tables

    @staticmethod
    def get_all_tables():
        conn = get_db_connection()
        tables = conn.execute('''
            SELECT * FROM tables 
            ORDER BY table_number
        ''').fetchall()
        conn.close()
        return tables

    @staticmethod
    def reserve_tables(table_numbers, reservation_id):
        """Reservar multiples mesas"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for table_number in table_numbers:
            cursor.execute(
                'UPDATE tables SET is_available = FALSE WHERE table_number = ?',
                (table_number,)
            )
        
        conn.commit()
        conn.close()

    @staticmethod
    def free_tables(table_numbers):
        """Liberar multiples mesas"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for table_number in table_numbers:
            cursor.execute(
                'UPDATE tables SET is_available = TRUE WHERE table_number = ?',
                (table_number,)
            )
        
        conn.commit()
        conn.close()

    @staticmethod
    def get_tables_by_reservation(reservation_id):
        """Obtener mesas asociadas a una reserva"""
        conn = get_db_connection()
        tables = conn.execute('''
            SELECT t.* FROM tables t
            JOIN reservation_tables rt ON t.table_number = rt.table_number
            WHERE rt.reservation_id = ?
            ORDER BY t.table_number
        ''', (reservation_id,)).fetchall()
        conn.close()
        return tables

    @staticmethod
    def init_tables():
        """Inicializar las 20 mesas en la base de datos"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_number INTEGER UNIQUE NOT NULL,
                capacity INTEGER NOT NULL,
                is_available BOOLEAN DEFAULT TRUE,
                location TEXT
            )
        ''')
        
        for i in range(1, 21):
            cursor.execute(
                'INSERT OR IGNORE INTO tables (table_number, capacity, location) VALUES (?, ?, ?)',
                (i, 4, 'Salón Principal')
            )
        
        conn.commit()
        conn.close()