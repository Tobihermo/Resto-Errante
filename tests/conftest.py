import pytest
import os
import sys
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from app_code.database import init_db, get_db_connection
from app_code.models import User

@pytest.fixture(scope='session')
def app():
    """Fixture para la aplicacion Flask"""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    
    db_fd, flask_app.config['DATABASE_PATH'] = tempfile.mkstemp()
    
    with flask_app.app_context():
        init_db()
    
    yield flask_app
    
    os.close(db_fd)
    os.unlink(flask_app.config['DATABASE_PATH'])

@pytest.fixture
def client(app):
    """Fixture para el cliente de tests"""
    return app.test_client()

@pytest.fixture
def auth_client(client):
    """Cliente autenticado para tests"""
    with flask_app.app_context():
        conn = get_db_connection()
        conn.execute('DELETE FROM users WHERE username = ?', ('testuser',))
        conn.commit()
        conn.close()
    
    with flask_app.app_context():
        conn = get_db_connection()
        try:
            existing_user = conn.execute(
                'SELECT id FROM users WHERE username = ?', ('testuser',)
            ).fetchone()
            
            if not existing_user:
                from werkzeug.security import generate_password_hash
                hashed_password = generate_password_hash('testpass123')
                
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, first_name, last_name, dni, email, password, balance) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    ('testuser', 'Test', 'User', '12345678', 'test@example.com', hashed_password, 0.0)
                )
                user_id = cursor.lastrowid
                conn.commit()
            else:
                user_id = existing_user['id']
                
        except Exception as e:
            print(f"Error creando usuario de prueba: {e}")
            conn.rollback()
            user_id = None
        finally:
            conn.close()
    
    if user_id:
        with client.session_transaction() as session:
            session['user_id'] = user_id
            session['username'] = 'testuser'
            session['logged_in'] = True
    
    return client

@pytest.fixture
def sample_reservation_data():
    """Datos de ejemplo para reservas"""
    return {
        'title': 'Cena de Cumpleaños Test',
        'date': '2024-12-31T20:00',
        'short_description': 'Cena de cumpleaños de prueba',
        'long_description': 'Descripción detallada de la cena de cumpleaños',
        'event_type': '1',
        'is_free': 'y',
        'price': '0',
        'guest_count': '4',
        'special_requirements': 'Sin gluten',
        'is_private': '',
        'selected_tables': ['1']
    }
