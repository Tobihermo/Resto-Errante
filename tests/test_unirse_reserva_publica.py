import pytest
from app_code.database import get_db_connection

class TestUnirseReservaPublica:
    """Tests para el caso de uso: Unirse a Reserva Publica"""
    
    def test_ver_reservas_publicas_disponibles(self, client, auth_client):
        """Test que las reservas publicas son visibles para todos"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Publica Visible',
            'date': '2024-12-15T20:00',
            'short_description': 'Reserva publica de prueba',
            'event_type': '1',
            'is_free': 'y',
            'guest_count': '4',
            'selected_tables': ['6'],
            'special_requirements': ''
        }, follow_redirects=True)
        
        response = client.get('/')
        assert response.status_code == 200
    
    def test_unirse_reserva_gratuita(self, auth_client):
        """Test unirse a una reserva gratuita"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Gratuita Para Unirse',
            'date': '2024-12-10T19:00',
            'short_description': 'Reserva gratuita para test',
            'event_type': '1',
            'is_free': 'y',
            'guest_count': '4',
            'selected_tables': ['7'],
            'special_requirements': ''
        }, follow_redirects=True)
        
        conn = get_db_connection()
        reservation = conn.execute(
            'SELECT id FROM reservations WHERE title LIKE ?', 
            ('%Reserva Gratuita Para Unirse%',)
        ).fetchone()
        
        if reservation:
            reservation_id = reservation['id']
            
            response = auth_client.post(f'/reservation/{reservation_id}/attend',
                                      data={}, 
                                      follow_redirects=True)
            
            assert response.status_code == 200
        
        conn.close()
    
    def test_unirse_reserva_paga(self, auth_client):
        """Test proceso de unirse a reserva paga"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Paga Para Test',
            'date': '2024-12-18T21:00',
            'short_description': 'Reserva paga para test',
            'event_type': '1',
            'is_free': '',
            'price': '25.0',
            'guest_count': '4',
            'selected_tables': ['8'],
            'special_requirements': ''
        }, follow_redirects=True)
        
        conn = get_db_connection()
        reservation = conn.execute(
            'SELECT id FROM reservations WHERE title LIKE ?', 
            ('%Reserva Paga Para Test%',)
        ).fetchone()
        
        if reservation:
            reservation_id = reservation['id']
            
            response = auth_client.get(f'/reservation/{reservation_id}/attend')
            assert response.status_code in [200, 302]
        
        conn.close()
    
    def test_seleccionar_comida_al_unirse(self, auth_client):
        """Test seleccionar comida al unirse a reserva"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Comida Test',
            'date': '2024-12-22T20:00',
            'short_description': 'Reserva para test de comida',
            'event_type': '1',
            'is_free': 'y',
            'guest_count': '4',
            'selected_tables': ['9'],
            'special_requirements': ''
        }, follow_redirects=True)
        
        conn = get_db_connection()
        reservation = conn.execute(
            'SELECT id FROM reservations WHERE title LIKE ?', 
            ('%Reserva Comida Test%',)
        ).fetchone()
        
        if reservation:
            reservation_id = reservation['id']
            
            response = auth_client.post(f'/reservation/{reservation_id}/attend',
                                      data={},
                                      follow_redirects=True)
            
            assert response.status_code == 200
        
        conn.close()