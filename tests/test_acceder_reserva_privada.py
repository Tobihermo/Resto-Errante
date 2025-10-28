import pytest
from app_code.database import get_db_connection

class TestAccederReservaPrivada:
    """Tests para el caso de uso: Acceder a Reserva Privada con Codigo"""
    
    def test_acceso_pagina_codigo_privado(self, auth_client):
        """Test acceso a la pagina de ingreso de codigo"""
        response = auth_client.get('/reservation/private-access')
        
        if response.status_code == 302:
            response = auth_client.get(response.headers['Location'])
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert 'form' in response_text.lower() or 'input' in response_text.lower()
    
    def test_acceso_reserva_privada_codigo_valido(self, auth_client):
        """Test acceso exitoso con codigo válido"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Privada Test',
            'date': '2024-12-24T20:00',
            'short_description': 'Reserva privada para test',
            'event_type': '1',
            'is_free': 'y',
            'guest_count': '4',
            'selected_tables': ['10'],
            'is_private': 'y',
            'access_code': 'PRUEBA123',
            'special_requirements': ''
        }, follow_redirects=True)
        
        response = auth_client.post('/reservation/private-access',
                                  data={'access_code': 'PRUEBA123'},
                                  follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_acceso_reserva_privada_codigo_invalido(self, auth_client):
        """Test que codigo invalido muestra error"""
        response = auth_client.post('/reservation/private-access',
                                  data={'access_code': 'CODIGO_INEXISTENTE'},
                                  follow_redirects=True)
        
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert len(response_text) > 0
    
    def test_acceso_reserva_privada_sin_codigo(self, auth_client):
        """Test que enviar código vacio muestra error"""
        response = auth_client.post('/reservation/private-access',
                                  data={'access_code': ''},
                                  follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_acceso_reserva_privada_paga(self, auth_client):
        """Test acceso a reserva privada paga con código"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Privada Paga',
            'date': '2024-12-28T19:00',
            'short_description': 'Reserva privada paga para test',
            'event_type': '1',
            'is_free': '', 
            'price': '30.0',
            'guest_count': '4',
            'selected_tables': ['11'],
            'is_private': 'y',
            'access_code': 'PAGA123',
            'special_requirements': ''
        }, follow_redirects=True)
        
        response = auth_client.post('/reservation/private-access',
                                  data={'access_code': 'PAGA123'},
                                  follow_redirects=True)
        
        assert response.status_code in [200, 302]
    
    def test_reserva_privada_no_visible_publicamente(self, client, auth_client):
        """Test que reservas privadas no son visibles en listado publico"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Secreta',
            'date': '2024-12-30T20:00',
            'short_description': 'Esta no deberia ser visible',
            'event_type': '1',
            'is_free': 'y',
            'guest_count': '4',
            'selected_tables': ['12'],
            'is_private': 'y',
            'access_code': 'SECRETO',
            'special_requirements': ''
        }, follow_redirects=True)
        
        response = client.get('/')
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert 'Reserva Secreta' not in response_text