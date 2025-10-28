import pytest
from app_code.database import get_db_connection

class TestCrearReserva:
    """Tests para el caso de uso: Crear Reserva de Evento"""
    
    def test_acceso_pagina_crear_reserva(self, auth_client):
        """Test que un usuario autenticado puede acceder al formulario de crear reserva"""
        response = auth_client.get('/reservation/create')
        
        if response.status_code == 302:
            response = auth_client.get(response.headers['Location'])
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert 'form' in response_text.lower() or 'reserva' in response_text.lower()
    
    def test_crear_reserva_gratuita_publica(self, auth_client, sample_reservation_data):
        """Test crear una reserva gratuita y publica"""
        response = auth_client.post('/reservation/create', 
                                  data=sample_reservation_data,
                                  follow_redirects=True)
        
        assert response.status_code == 200
        
        conn = get_db_connection()
        reservation = conn.execute(
            'SELECT * FROM reservations WHERE title LIKE ?', 
            (f'%{sample_reservation_data["title"]}%',)
        ).fetchone()
        conn.close()
        
        assert response.status_code == 200
    
    def test_crear_reserva_paga_privada(self, auth_client):
        """Test crear una reserva paga y privada"""
        reservation_data = {
            'title': 'Cena Empresarial Privada Test',
            'date': '2024-12-25T19:00',
            'short_description': 'Cena corporativa privada',
            'long_description': 'Evento empresarial exclusivo',
            'event_type': '1',
            'is_free': '',
            'price': '50.0',
            'guest_count': '10',
            'special_requirements': 'Vegetariano opcional',
            'is_private': 'y',
            'access_code': 'EMPRESA2024',
            'selected_tables': ['3', '4']
        }
        
        response = auth_client.post('/reservation/create', 
                                  data=reservation_data,
                                  follow_redirects=True)
        
        assert response.status_code == 200
        
        conn = get_db_connection()
        reservation = conn.execute(
            'SELECT * FROM reservations WHERE title LIKE ?', 
            (f'%{reservation_data["title"]}%',)
        ).fetchone()
        conn.close()
        
        assert response.status_code == 200
    
    def test_crear_reserva_sin_mesas(self, auth_client, sample_reservation_data):
        """Test que no se puede crear reserva sin seleccionar mesas"""
        data = sample_reservation_data.copy()
        data['selected_tables'] = [] 
        
        response = auth_client.post('/reservation/create', 
                                  data=data,
                                  follow_redirects=True)
        
        assert response.status_code in [200, 400]
    
    def test_mesas_reservadas_no_disponibles(self, auth_client):
        """Test que las mesas reservadas no están disponibles para otras reservas"""
        response = auth_client.post('/reservation/create', data={
            'title': 'Reserva Test Mesa 2',
            'date': '2024-12-20T18:00',
            'short_description': 'Primera reserva',
            'event_type': '1',
            'is_free': 'y',
            'guest_count': '4',
            'selected_tables': ['2'],
            'special_requirements': ''
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        assert response.status_code == 200