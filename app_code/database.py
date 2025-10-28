import sqlite3
import os

def get_db_path():
    """Obtiene la ruta de la base de datos"""
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db', 'restaurante.db')

def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dni TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category_id INTEGER,
            is_special BOOLEAN DEFAULT FALSE,
            dietary_info TEXT, -- vegano, sin lactosa, etc.
            FOREIGN KEY (category_id) REFERENCES food_categories (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TIMESTAMP NOT NULL,
            short_description TEXT NOT NULL,
            long_description TEXT,
            location TEXT NOT NULL,
            event_type_id INTEGER,
            is_free BOOLEAN DEFAULT TRUE,
            is_cancelled BOOLEAN DEFAULT FALSE,
            is_private BOOLEAN DEFAULT FALSE,
            access_code TEXT, -- Para reservas privadas
            price REAL DEFAULT 0.0,
            creator_id INTEGER NOT NULL,
            table_count INTEGER DEFAULT 1,
            guest_count INTEGER DEFAULT 1,
            special_requirements TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (creator_id) REFERENCES users (id),
            FOREIGN KEY (event_type_id) REFERENCES event_types (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservation_foods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            menu_item_id INTEGER NOT NULL,
            quantity INTEGER DEFAULT 1,
            special_instructions TEXT,
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservation_attendees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reservation_id INTEGER NOT NULL,
            tickets_count INTEGER DEFAULT 1,
            food_selections TEXT, -- JSON con selecciones de comida
            is_confirmed BOOLEAN DEFAULT TRUE,
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            UNIQUE(user_id, reservation_id)
        )
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO event_types (name, description) VALUES 
        ('Cumpleaños', 'Celebracion de cumpleaños'),
        ('Reunión Familiar', 'Encuentro familiar'),
        ('Casamiento', 'Celebracion de matrimonio'),
        ('Aniversario', 'Celebracion de aniversario'),
        ('Cena de Negocios', 'Reunion empresarial'),
        ('Fiesta de Graduacion', 'Celebracion de graduacion'),
        ('Otro', 'Otro tipo de evento')
    ''')
    
    cursor.execute('''
        INSERT OR IGNORE INTO food_categories (name) VALUES 
        ('Entradas'),
        ('Platos Principales'),
        ('Postres'),
        ('Bebidas'),
        ('Especiales')
    ''')
    
    menu_items_data = [
        ('Empanadas', 'Empanadas de carne', 8.99, 1, 'Contiene gluten'),
        ('Bruschetta', 'Pan tostado con tomate y albahaca', 7.50, 1, 'Vegetariano'),
        ('Bife de Chorizo', 'Corte premium con guarnicion', 25.99, 2, 'Sin lactosa'),
        ('Risotto de Hongos', 'Risotto cremoso con hongos silvestres', 18.50, 2, 'Vegetariano'),
        ('Tiramisu', 'Postre italiano clasico', 9.99, 3, 'Contiene lactosa'),
        ('Ensalada Cesar', 'Ensalada con pollo y aderezo cesar', 12.99, 2, 'Sin lactosa'),
        ('Tarta de Chocolate', 'Tarta sin harina con salsa de frutos rojos', 10.50, 3, 'Sin gluten'),
        ('Agua Mineral', 'Botella 500ml', 3.50, 4, 'Vegano'),
        ('Vino Tinto', 'Copa de vino malbec', 8.00, 4, 'Vegano'),
        ('Cerveza Artesanal', 'Pinta de cerveza local', 6.50, 4, 'Vegano'),
        ('Sopa del Día', 'Sopa casera según temporada', 6.99, 1, 'Vegetariano'),
        ('Pasta Carbonara', 'Pasta con salsa cremosa y pancetta', 16.99, 2, 'Contiene lactosa'),
        ('Helado Artesanal', 'Selección de sabores caseros', 7.50, 3, 'Contiene lactosa')
    ]

    for item in menu_items_data:
        cursor.execute('''
            INSERT OR IGNORE INTO menu_items (name, description, price, category_id, dietary_info) 
            VALUES (?, ?, ?, ?, ?)
        ''', item)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            type TEXT NOT NULL, -- 'info', 'warning', 'success', 'error'
            is_read BOOLEAN DEFAULT FALSE,
            related_reservation_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (related_reservation_id) REFERENCES reservations (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(reservation_id, user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reservation_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            UNIQUE(user_id, reservation_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reservation_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            UNIQUE(user_id, reservation_id)
        )
    ''')
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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservation_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id INTEGER NOT NULL,
            table_number INTEGER NOT NULL,
            FOREIGN KEY (reservation_id) REFERENCES reservations (id),
            FOREIGN KEY (table_number) REFERENCES tables (table_number),
            UNIQUE(reservation_id, table_number)
        )
    ''')
    conn.commit()
    conn.close()
    

    
def get_db_connection():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn