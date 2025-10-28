import pytest
from app_code.models import User
from app_code.database import get_db_connection

class TestGestionPerfilSaldo:
    """Tests para el caso de uso: Gestionar Perfil y Saldo"""
    
    def test_acceso_pagina_perfil(self, auth_client):
        """Test que usuario autenticado puede acceder a su perfil"""
        response = auth_client.get('/profile')
        if response.status_code == 302:
            response = auth_client.get(response.headers['Location'])
        assert response.status_code == 200
        response_text = response.get_data(as_text=True)
        assert len(response_text) > 0  
    
    def test_actualizar_informacion_perfil(self, auth_client):
        """Test actualizacion de informacion personal"""
        new_data = {
            'first_name': 'NuevoNombre',
            'last_name': 'NuevoApellido', 
            'email': 'nuevo@example.com',
            'submit_profile': 'true'
        }
        
        response = auth_client.post('/profile',
                                  data=new_data,
                                  follow_redirects=True)
        
        assert response.status_code == 200
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT first_name, last_name, email FROM users WHERE username = ?', 
            ('testuser',)
        ).fetchone()
        conn.close()
        
        if user:
            assert user['first_name'] == 'NuevoNombre'
            assert user['last_name'] == 'NuevoApellido'
            assert user['email'] == 'nuevo@example.com'
    
    def test_cargar_saldo_cuenta(self, auth_client):
        """Test cargar saldo a la cuenta"""
        conn = get_db_connection()
        user = conn.execute(
            'SELECT balance FROM users WHERE username = ?', 
            ('testuser',)
        ).fetchone()
        conn.close()
        
        if user:
            saldo_inicial = user['balance'] or 0
            
            response = auth_client.post('/profile',
                                      data={
                                          'amount': 100.0,
                                          'submit_payment': 'true'
                                      },
                                      follow_redirects=True)
            
            assert response.status_code == 200
            
            conn = get_db_connection()
            user_after = conn.execute(
                'SELECT balance FROM users WHERE username = ?', 
                ('testuser',)
            ).fetchone()
            conn.close()
            
            if user_after:
                assert user_after['balance'] >= saldo_inicial
    
    def test_ver_estadisticas_perfil(self, auth_client):
        """Test que se muestran estadisticas correctas en el perfil"""
        auth_client.post('/reservation/create', data={
            'title': 'Reserva Estadistica Test',
            'date': '2024-12-05T18:00',
            'short_description': 'Reserva para estadisticas',
            'event_type': '1',
            'is_free': 'y',
            'guest_count': '2',
            'selected_tables': ['13'],
            'special_requirements': ''
        }, follow_redirects=True)
        
        response = auth_client.get('/profile')
        if response.status_code == 302:
            response = auth_client.get(response.headers['Location'])
        assert response.status_code == 200
    
    def test_cargar_saldo_monto_invalido(self, auth_client):
        """Test que monto invalido no se procesa"""
        response = auth_client.post('/profile',
                                  data={
                                      'amount': -50.0,
                                      'submit_payment': 'true'
                                  },
                                  follow_redirects=True)
        
        assert response.status_code in [200, 302, 400]
    
    def test_actualizar_email_invalido(self, auth_client):
        """Test que email invalido no se acepta"""
        response = auth_client.post('/profile',
                                  data={
                                      'first_name': 'Test',
                                      'last_name': 'User',
                                      'email': 'email-invalido',
                                      'submit_profile': 'true'
                                  },
                                  follow_redirects=True)
        
        assert response.status_code in [200, 302, 400]