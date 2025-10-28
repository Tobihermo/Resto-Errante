# Resto-Errante

Resto Errante

Integrante del Grupo
- Tobias Hermosilla Mercato


Sistema web completo para la gestion de reservas en un restaurante, que permite a los usuarios crear eventos, unirse a reservas existentes, gestionar perfiles y realizar pagos virtuales, entre otras cosas

Caracteristicas Principales
- Sistema de autenticacion de usuarios
- Creacion de reservas publicas y privadas
- Sistema de pagos integrado con saldo virtual
- Gestion de mesas y capacidad
- Sistema de notificaciones
- Reseñas y calificaciones
- Favoritos y listas personalizadas
- Tests automatizados

Tecnologias Utilizadas
- Backend: Python, Flask, SQLite
- Frontend: HTML, CSS, JavaScript
- Base de datos: SQLite con SQLAlchemy
- Testing: Pytest, Flask-Testing

Instalacion y Configuración

Prerrequisitos
- Python
- pip (gestor de paquetes de Python)


Pasos de Instalacion

Descargar el repositorio
Crear un venv
Instalar dependencias (pip install -r requirements.txt
)
Iniciar app.py
La base de datos se crea automaticamente en la carpeta `bd/restaurante.db`

Estructura del Proyecto

RestoErrante/
├── app.py                          
├── requirements.txt                
├── README.md                       
├── static/                        
│   ├── css/
│   │   └── style.css              
│   └── js/
│       └── script.js              
├── tests/                          
│   ├── conftest.py
│   ├── test_crear_reserva.py
│   ├── test_gestion_perfil_saldo.py
│   ├── test_unirse_reserva_publica.py
│   └── test_acceder_reserva_privada.py
├── templates/                      
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── create_reservation.html
│   ├── reservation_detail.html
│   ├── my_reservations.html
│   ├── profile.html
│   ├── notifications.html
│   ├── attend_reservation.html
│   ├── payment.html
│   ├── access_private_reservation.html
│   ├── add_review.html
│   ├── favorites.html
│   ├── menu.html
│   ├── tables.html
│   └── my_private_reservations.html
├── app_code/                       
│   ├── __init__.py
│   ├── database.py                 
│   ├── models.py                  
│   ├── forms.py                    
│   └── auth.py                     
└── bd/                             
    └── restaurante.db

Ejecutar todos los tests
pytest


Decisiones de Diseño

Arquitectura del Sistema; Arquitectura en capas, osea, capa de presentación (con htmls),capa de negocio (con Python flask) y capa de persistencia (hecha con SQLite)

Gestion de Reservas
- Reservas publicas: Visibles para todos los usuarios registrados
- Reservas privadas: Acceso mediante codigo, ideales para eventos corporativos
- Sistema de mesas: Gestion automatica de disponibilidad de mesas
- Limites de capacidad: Control basado en número de mesas reservadas

Sistema de Pagos
- Saldo virtual: Los usuarios cargan dinero a sus cuentas
- Transacciones atomicas: Las operaciones de pago son todo-o-nada
- Reembolsos automáticos: En caso de cancelación de reservas pagas

Seguridad
- Hash de contraseñas: Usando werkzeug.security
- Validación de entrada: WTForms para todos los formularios
- Control de acceso: Decoradores para rutas protegidas

Experiencia de Usuario
- Notificaciones en tiempo real: Sistema de alertas para acciones importantes
- Navegacion intuitiva: Diseño consistente en todas las paginas
- Feedback inmediato: Mensajes flash para todas las acciones

Casos de Uso Implementados

1) Gestion de Perfil y Saldo
- Registro y autenticacion de usuarios
- Actualizacion de información personal
- Carga y gestion de saldo virtual
- Visualizacion de estadisticas de uso

2) Creacion de Reservas de Evento
- Creacion de reservas públicas y privadas
- Seleccion de mesas disponibles
- Configuracion de precios (gratuitas o pagas)
- Especificacion de requisitos especiales

3) Unirse a Reserva Publica
- Exploración de reservas disponibles
- Proceso de union a reservas gratuitas
- Sistema de selección de comida
- Confirmacion de asistencia

4) Acceder a Reserva Privada con Codigo
- Sistema de codigos de acceso únicos
- Validación de codigos en tiempo real
- Proceso de pago para reservas privadas pagas
- Control de acceso granular

API Endpoints Principales

Autenticacion
- `POST /auth/login` - Inicio de sesion
- `POST /auth/register` - Registro de usuario
- `GET /auth/logout` - Cierre de sesion

Reservas
- `GET /` - Listado de reservas publicas
- `GET /reservation/create` - Formulario de creacion
- `POST /reservation/create` - Crear reserva
- `GET /reservation/<id>` - Detalle de reserva
- `POST /reservation/<id>/attend` - Unirse a reserva
- `POST /reservation/<id>/cancel` - Cancelar reserva

Perfil y Saldo
- `GET /profile` - Perfil de usuario
- `POST /profile` - Actualizar perfil/cargar saldo
- `GET /my-reservations` - Mis reservas

