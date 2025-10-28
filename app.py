from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from app_code.database import init_db  
from app_code.models import User, Reservation, ReservationAttendee, Menu, EventType, Favorite, Review, Notification  
from app_code.forms import ReservationForm, PaymentForm, ProfileForm, FoodSelectionForm
from app_code.auth import auth_bp
import os
import json
from app_code.models import User, Reservation, ReservationAttendee, Menu, EventType, Favorite, Review, Notification  
from app_code.models import User, Reservation, ReservationAttendee, Menu, EventType, Table, Review, Notification 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'codigo_secreta_restaurante'

app.config['DATABASE_PATH'] = os.path.join(os.path.dirname(__file__), 'bd', 'restaurante.db')

app.register_blueprint(auth_bp)

def login_user(user):
    session['user_id'] = user['id']
    session['username'] = user['username']
    session['logged_in'] = True

def logout_user():
    session.clear()

def get_current_user():
    if 'user_id' in session:
        return User.get_by_id(session['user_id'])
    return None

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Por favor inicia sesion para acceder a esta pagina', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    query = request.args.get('q', '')
    event_type = request.args.get('event_type', '')
    is_free = request.args.get('is_free')
    
    if is_free == 'true':
        is_free = True
    elif is_free == 'false':
        is_free = False
    else:
        is_free = None
    
    event_types = EventType.get_all()
    reservations = Reservation.search_reservations(query=query, event_type=event_type, is_free=is_free)
    
    return render_template('index.html', 
                         reservations=reservations, 
                         query=query, 
                         is_free=is_free,
                         event_types=event_types,
                         selected_event_type=event_type)

@app.route('/menu')
def menu():
    categories = Menu.get_all_categories()
    menu_items = Menu.get_items_by_category()
    return render_template('menu.html', categories=categories, menu_items=menu_items)

@app.route('/reservation/<int:reservation_id>')
def reservation_detail(reservation_id):
    reservation = Reservation.get_by_id(reservation_id)
    if not reservation:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('index'))
    
    user = get_current_user()
    is_attending = False
    is_favorite = False
    user_has_reviewed = False
    
    if user:
        is_attending = ReservationAttendee.is_attending(user['id'], reservation_id)
        is_favorite = Favorite.is_favorite(user['id'], reservation_id)
        user_has_reviewed = Review.user_has_reviewed(reservation_id, user['id'])
    
    reviews = Review.get_by_reservation(reservation_id)
    
    reservation_tables = Reservation.get_reservation_tables(reservation_id)
    
    return render_template('reservation_detail.html', 
                         reservation=reservation, 
                         is_attending=is_attending,
                         is_favorite=is_favorite,
                         user_has_reviewed=user_has_reviewed,
                         reviews=reviews,
                         reservation_tables=reservation_tables)

@app.route('/reservation/create', methods=['GET', 'POST'])
@login_required
def create_reservation():
    form = ReservationForm()
    event_types = EventType.get_all()
    form.event_type.choices = [(et['id'], et['name']) for et in event_types]
    
    available_tables = Table.get_all_tables()
    
    if form.validate_on_submit():
        selected_tables = request.form.getlist('selected_tables')
        
        if not selected_tables:
            flash('Debes seleccionar al menos una mesa', 'error')
            return render_template('create_reservation.html', 
                                 form=form, 
                                 event_types=event_types,
                                 available_tables=available_tables)
        
        is_free = form.is_free.data
        price = 0.0 if is_free else form.price.data
        
        reservation_id = Reservation.create(
            title=form.title.data,
            date=form.date.data,
            short_description=form.short_description.data,
            long_description=form.long_description.data,
            location=f"Mesas: {', '.join([f'Mesa {t}' for t in selected_tables])}",
            event_type_id=form.event_type.data,
            is_free=is_free,  
            price=price,
            creator_id=session['user_id'],
            table_count=len(selected_tables),
            guest_count=form.guest_count.data,
            special_requirements=form.special_requirements.data,
            is_private=form.is_private.data,
            access_code=form.access_code.data if form.is_private.data else None
        )
        
        Table.reserve_tables(selected_tables, reservation_id)
        Reservation.add_tables_to_reservation(reservation_id, selected_tables)
        
        Notification.create(
            session['user_id'],
            'Reserva Creada',
            f'Tu reserva "{form.title.data}" ha sido creada exitosamente para el {form.date.data[:16]}',
            'success',
            reservation_id
        )
        
        tipo_reserva = "gratuita" if is_free else f"paga (${price} por persona)"
        flash(f'Reserva {tipo_reserva} creada exitosamente! Mesas reservadas: {", ".join([f"Mesa {t}" for t in selected_tables])}', 'success')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    return render_template('create_reservation.html', 
                         form=form, 
                         event_types=event_types,
                         available_tables=available_tables)

@app.route('/reservation/private-access', methods=['GET', 'POST'])
@login_required
def access_private_reservation():
    if request.method == 'POST':
        access_code = request.form.get('access_code', '').strip()
        
        if not access_code:
            flash('Por favor ingresa un codigo de acceso', 'error')
            return render_template('access_private_reservation.html')
        
        reservation = Reservation.get_by_access_code(access_code)
        
        if reservation:
            if reservation['is_cancelled']:
                flash('Esta reserva ha sido cancelada', 'error')
                return redirect(url_for('index'))
            
            user_id = session['user_id']
            
            is_attending = ReservationAttendee.is_attending(user_id, reservation['id'])
            
            if is_attending:
                flash('Ya estas registrado en esta reserva', 'info')
                return redirect(url_for('reservation_detail', reservation_id=reservation['id']))
            
            try:
                if reservation['is_free']:
                    success = ReservationAttendee.attend_reservation(
                        user_id, 
                        reservation['id']
                    )
                    if success:
                        flash('Codigo valido! Has sido registrado exitosamente en la reserva', 'success')
                    else:
                        flash('Error al registrarte en la reserva', 'error')
                else:
                    session['pending_reservation'] = reservation['id']
                    session['pending_access_code'] = access_code
                    flash('Codigo valido! Ahora puedes proceder con el pago', 'success')
                    return redirect(url_for('purchase_tickets', reservation_id=reservation['id']))
                
                return redirect(url_for('reservation_detail', reservation_id=reservation['id']))
                
            except Exception as e:
                flash('Error al procesar tu registro', 'error')
                print(f"Error registrando usuario en reserva privada: {e}")
                
        else:
            flash('Codigo de acceso invalido. Verifica el codigo e intenta nuevamente', 'error')
    
    return render_template('access_private_reservation.html')

@app.route('/reservation/<int:reservation_id>/attend', methods=['GET', 'POST'])
@login_required
def attend_reservation(reservation_id):
    reservation = Reservation.get_by_id(reservation_id)
    user = get_current_user()
    
    if not reservation:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('index'))
    
    if ReservationAttendee.is_attending(user['id'], reservation_id):
        flash('Ya estas registrado en esta reserva', 'info')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    if reservation['is_cancelled']:
        flash('Esta reserva ha sido cancelada', 'error')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    if reservation['is_private']:
        flash('Esta es una reserva privada. Necesitas un codigo de acceso', 'error')
        return redirect(url_for('access_private_reservation'))
    
    if request.method == 'POST':
        food_selections = {}
        for key, value in request.form.items():
            if key.startswith('food_') and value and value.isdigit() and int(value) > 0:
                item_id = key.replace('food_', '')
                food_selections[item_id] = int(value)
        
        try:
            success = ReservationAttendee.attend_reservation(
                user['id'], 
                reservation_id, 
                tickets_count=1,
                food_selections=food_selections
            )
            
            if success:
                if reservation['creator_id'] != user['id']:
                    create_reservation_notifications(reservation, 'new_attendee')
                
                flash('Asistencia confirmada exitosamente!', 'success')
                return redirect(url_for('reservation_detail', reservation_id=reservation_id))
            else:
                flash('No se pudo confirmar tu asistencia. Ya estas en la reserva', 'error')
                return redirect(url_for('reservation_detail', reservation_id=reservation_id))
                
        except Exception as e:
            flash('Error al procesar tu solicitud', 'error')
            print(f"Error en attend_reservation: {e}")
            return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    categories = Menu.get_all_categories()
    menu_items = Menu.get_items_by_category()
    return render_template('attend_reservation.html', 
                         reservation=reservation, 
                         categories=categories, 
                         menu_items=menu_items)

@app.route('/reservation/<int:reservation_id>/cancel-attendance', methods=['GET', 'POST'])
@login_required
def cancel_attendance(reservation_id):
    reservation = Reservation.get_by_id(reservation_id)
    user = get_current_user()
    
    if not reservation:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('index'))
    
    if reservation['is_cancelled']:
        flash('Esta reserva ya ha sido cancelada', 'info')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    if not ReservationAttendee.is_attending(user['id'], reservation_id):
        flash('No estas registrado en esta reserva', 'error')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    ReservationAttendee.cancel_attendance(user['id'], reservation_id)
    
    Notification.create(
        user['id'],
        'Asistencia Cancelada',
        f'Has cancelado tu asistencia a la reserva "{reservation["title"]}"',
        'info',
        reservation_id
    )
    
    if reservation['creator_id'] != user['id']:
        Notification.create(
            reservation['creator_id'],
            'Asistente Cancelado',
            f'El usuario {user["username"]} ha cancelado su asistencia a tu reserva "{reservation["title"]}"',
            'warning',
            reservation_id
        )
    
    if not reservation['is_free']:
        User.update_balance(user['id'], reservation['price'])
        flash('Asistencia cancelada. Ya te devolvieron tu saldo.', 'info')
    else:
        flash('Asistencia cancelada exitosamente', 'info')
    
    return redirect(url_for('reservation_detail', reservation_id=reservation_id))
@app.route('/reservation/<int:reservation_id>/cancel', methods=['POST'])
@app.route('/reservation/<int:reservation_id>/cancel-get', methods=['GET']) 
def cancel_reservation(reservation_id):
    user = get_current_user()
    reservation = Reservation.get_by_id(reservation_id)
    
    if not reservation:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('my_reservations'))
    
    if reservation['creator_id'] != user['id']:
        flash('No tenes permisos para cancelar esta reserva', 'error')
        return redirect(url_for('my_reservations'))
    
    if reservation['is_cancelled']:
        flash('Esta reserva ya esta cancelada', 'info')
        return redirect(url_for('my_reservations'))
    
    try:
        reservation_tables = Reservation.get_reservation_tables(reservation_id)
        table_numbers = [table['table_number'] for table in reservation_tables]
        
        if table_numbers:
            Table.free_tables(table_numbers)
        
        ReservationAttendee.remove_tables_from_reservation(reservation_id)
        
        Reservation.cancel_reservation(reservation_id, user['id'])
        
        Notification.create(
            user['id'],
            'Reserva Cancelada',
            f'Tu reserva "{reservation["title"]}" ha sido cancelada exitosamente',
            'warning',
            reservation_id
        )
        
        attendees = ReservationAttendee.get_attendees(reservation_id)
        for attendee in attendees:
            if attendee['id'] != user['id']:
                Notification.create(
                    attendee['id'],
                    'Reserva Cancelada',
                    f'La reserva "{reservation["title"]}" a la que estabas inscrito ha sido cancelada',
                    'warning',
                    reservation_id
                )
        
        flash('Reserva cancelada exitosamente', 'success')
        
    except Exception as e:
        flash('Error al cancelar la reserva', 'error')
        print(f"Error cancelando reserva: {e}")
    
    return redirect(url_for('my_reservations'))


@app.route('/reservation/<int:reservation_id>/purchase', methods=['GET', 'POST'])
@login_required
def purchase_tickets(reservation_id):
    reservation = Reservation.get_by_id(reservation_id)
    user = get_current_user()
    
    if not reservation or reservation['is_free']:
        flash('Reserva no disponible para compra', 'error')
        return redirect(url_for('index'))
    
    access_code = session.get('pending_access_code')
    if access_code and reservation['is_private']:
        valid_reservation = Reservation.get_by_access_code(access_code)
        if not valid_reservation or valid_reservation['id'] != reservation_id:
            flash('Acceso no autorizado', 'error')
            return redirect(url_for('index'))
    
    food_selections = session.get('pending_food_selections', {})
    total_food_cost = 0
    
    for item_id, quantity in food_selections.items():
        menu_item = Menu.get_item_by_id(item_id)
        if menu_item:
            total_food_cost += menu_item['price'] * quantity
    
    total_cost = (reservation['price'] + total_food_cost)
    
    if request.method == 'POST':
        tickets_count = int(request.form.get('tickets_count', 1))
        final_cost = total_cost * tickets_count
        
        if user['balance'] >= final_cost:
            User.update_balance(user['id'], -final_cost)
            success = ReservationAttendee.attend_reservation(
                user['id'], 
                reservation_id, 
                tickets_count,
                food_selections
            )
            
            if success:
                if reservation['creator_id'] != user['id']:
                    create_reservation_notifications(reservation, 'new_attendee')
                
                session.pop('pending_reservation', None)
                session.pop('pending_food_selections', None)
                session.pop('pending_access_code', None)
                
                flash(f'Compra exitosa! Se descontaron ${final_cost} de tu saldo', 'success')
                return redirect(url_for('reservation_detail', reservation_id=reservation_id))
            else:
                flash('Error al procesar tu registro', 'error')
        else:
            flash('Saldo insuficiente. Por favor carga dinero a tu cuenta', 'error')
            return redirect(url_for('profile'))
    
    all_menu_items = Menu.get_items_by_category()
    return render_template('payment.html', 
                         reservation=reservation, 
                         user=user, 
                         total_cost=total_cost,
                         food_selections=food_selections,
                         all_menu_items=all_menu_items)
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_current_user()
    payment_form = PaymentForm()
    profile_form = ProfileForm(
        first_name=user['first_name'],
        last_name=user['last_name'],
        email=user['email']
    )
    
    if 'submit_payment' in request.form and payment_form.validate_on_submit():
        User.update_balance(user['id'], payment_form.amount.data)
        flash(f'Se cargaron ${payment_form.amount.data} a tu cuenta', 'success')
        return redirect(url_for('profile'))
    
    if 'submit_profile' in request.form and profile_form.validate_on_submit():
        User.update_profile(
            user['id'],
            profile_form.first_name.data,
            profile_form.last_name.data,
            profile_form.email.data
        )
        flash('Perfil actualizado exitosamente!', 'success')
        return redirect(url_for('profile'))
    
    from app_code.database import get_db_connection 
    conn = get_db_connection()
    
    created_reservations_count = conn.execute(
        'SELECT COUNT(*) FROM reservations WHERE creator_id = ? AND is_cancelled = FALSE', 
        (user['id'],)
    ).fetchone()[0]
    
    attending_reservations_count = conn.execute('''
        SELECT COUNT(*) FROM reservation_attendees ra
        JOIN reservations r ON ra.reservation_id = r.id
        WHERE ra.user_id = ? AND r.is_cancelled = FALSE
    ''', (user['id'],)).fetchone()[0]
    
    conn.close()
    
    return render_template('profile.html', 
                         user=user, 
                         payment_form=payment_form,
                         profile_form=profile_form,
                         created_reservations_count=created_reservations_count,
                         attending_reservations_count=attending_reservations_count)

@app.route('/my-reservations')
@login_required
def my_reservations():
    user = get_current_user()
    
    reservations = ReservationAttendee.get_user_reservations(user['id'])
    reservations = [r for r in reservations if not r['is_cancelled']]
    
    created_reservations = Reservation.get_by_creator(user['id'])
    created_reservations = [r for r in created_reservations if not r['is_cancelled']]
    
    all_menu_items = Menu.get_items_by_category()
    menu_items_dict = {str(item['id']): item for item in all_menu_items}
    
    return render_template('my_reservations.html', 
                         reservations=reservations, 
                         created_reservations=created_reservations,
                         menu_items_dict=menu_items_dict,
                         all_menu_items=all_menu_items)





@app.route('/notifications')
@login_required
def notifications():
    user = get_current_user()
    
    notifications_list = Notification.get_user_notifications_with_details(user['id'])
    
    return render_template('notifications.html', notifications=notifications_list)

@app.route('/notifications/mark-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    user = get_current_user()
    
    if Notification.mark_as_read(notification_id, user['id']):
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Notificacion no encontrada'}), 404

@app.route('/notifications/mark-all-read')
@login_required
def mark_all_notifications_read():
    user = get_current_user()
    
    count = Notification.mark_all_as_read(user['id'])
    flash(f'Se marcaron {count} notificaciones como leidas', 'success')
    
    return redirect(url_for('notifications'))

@app.route('/notifications/count')
@login_required
def notifications_count():
    user = get_current_user()
    count = Notification.get_unread_count(user['id'])
    return jsonify({'count': count})

def create_reservation_notifications(reservation, action, extra_info=None):
    """Crear notificaciones automaticas para eventos de reservas"""
    creator_id = reservation['creator_id']
    reservation_title = reservation['title']
    
    notifications_map = {
        'new_attendee': {
            'title': 'Nuevo Asistente',
            'message': f'Un nuevo usuario se ha unido a tu reserva "{reservation_title}"',
            'type': 'info'
        },
        'reservation_cancelled': {
            'title': 'Reserva Cancelada', 
            'message': f'Tu reserva "{reservation_title}" ha sido cancelada',
            'type': 'warning'
        },
        'reservation_reminder': {
            'title': 'Recordatorio de Reserva',
            'message': f'Tu reserva "{reservation_title}" es en menos de 24 horas', 
            'type': 'info'
        },
        'new_review': {
            'title': 'Nueva Reseña',
            'message': f'Tienes una nueva reseña en tu reserva "{reservation_title}"',
            'type': 'info'
        }
    }
    
    if action in notifications_map:
        notification_data = notifications_map[action]
        Notification.create(
            creator_id,
            notification_data['title'],
            notification_data['message'], 
            notification_data['type'],
            reservation['id']
        )

@app.route('/reservation/<int:reservation_id>/review', methods=['GET', 'POST'])
@login_required
def add_review(reservation_id):
    reservation = Reservation.get_by_id(reservation_id)
    user = get_current_user()
    
    if not reservation:
        flash('Reserva no encontrada', 'error')
        return redirect(url_for('index'))
    
    if reservation['is_cancelled']:
        flash('No puedes dejar reseña de una reserva cancelada', 'error')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    if not ReservationAttendee.is_attending(user['id'], reservation_id):
        flash('Solo los asistentes pueden dejar reseñas', 'error')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    if Review.user_has_reviewed(reservation_id, user['id']):
        flash('Ya has dejado una reseña para esta reserva', 'error')
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    if request.method == 'POST':
        rating = int(request.form.get('rating', 0))
        comment = request.form.get('comment', '').strip()
        
        if not rating or rating < 1 or rating > 5:
            flash('Por favor selecciona una calificacion valida (1-5 estrellas)', 'error')
            return render_template('add_review.html', reservation=reservation)
        
        if len(comment) > 500:
            flash('El comentario no puede tener mas de 500 caracteres', 'error')
            return render_template('add_review.html', reservation=reservation)
        
        if Review.create(reservation_id, user['id'], rating, comment):
            flash('Reseña agregada exitosamente!', 'success')
            
            if reservation['creator_id'] != user['id']:
                Notification.create(
                    reservation['creator_id'],
                    'Nueva Reseña',
                    f'El usuario {user["username"]} ha dejado una reseña en tu reserva "{reservation["title"]}"',
                    'info',
                    reservation_id
                )
        else:
            flash('Error al agregar la reseña', 'error')
        
        return redirect(url_for('reservation_detail', reservation_id=reservation_id))
    
    return render_template('add_review.html', reservation=reservation)

@app.route('/review/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    user = get_current_user()
    
    if Review.delete_review(review_id, user['id']):
        flash('Reseña eliminada exitosamente', 'success')
    else:
        flash('No se pudo eliminar la reseña o no teenes permisos', 'error')
    
    return redirect(request.referrer or url_for('index'))

@app.route('/api/reservation/<int:reservation_id>/reviews')
def api_reservation_reviews(reservation_id):
    """API para obtener reseñas de una reserva"""
    reviews = Review.get_by_reservation(reservation_id)
    reviews_list = []
    
    for review in reviews:
        reviews_list.append({
            'id': review['id'],
            'user_name': review['first_name'] + ' ' + review['last_name'],
            'username': review['username'],
            'rating': review['rating'],
            'comment': review['comment'],
            'created_at': review['created_at'],
            'is_own_review': 'user_id' in review and review['user_id'] == session.get('user_id')
        })
    
    return jsonify(reviews_list)


@app.route('/reservation/<int:reservation_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(reservation_id):
    user = get_current_user()
    
    if Favorite.is_favorite(user['id'], reservation_id):
        Favorite.remove_favorite(user['id'], reservation_id)
        flash('Reserva eliminada de favoritos', 'info')
    else:
        if Favorite.add_favorite(user['id'], reservation_id):
            flash('Reserva agregada a favoritos', 'success')
        else:
            flash('Error al agregar a favoritos', 'error')
    
    return redirect(url_for('reservation_detail', reservation_id=reservation_id))

@app.route('/favorites')
@login_required
def favorites():
    user = get_current_user()
    favorites = Favorite.get_user_favorites(user['id'])
    return render_template('favorites.html', favorites=favorites)



@app.route('/reservation/<int:reservation_id>/unfavorite', methods=['POST'])
@login_required
def unfavorite_reservation(reservation_id):
    user = get_current_user()
    Favorite.remove_favorite(user['id'], reservation_id)
    flash('Reserva eliminada de favoritos', 'info')
    return redirect(url_for('reservation_detail', reservation_id=reservation_id))





@app.route('/tables')
def tables():
    available_tables = Table.get_available_tables()
    return render_template('tables.html', tables=available_tables)

@app.route('/my-private-reservations')
@login_required
def my_private_reservations():
    user = get_current_user()
    conn = get_db_connection()
    
    private_reservations = conn.execute('''
        SELECT r.*, et.name as event_type_name
        FROM reservations r
        LEFT JOIN event_types et ON r.event_type_id = et.id
        WHERE r.creator_id = ? AND r.is_private = TRUE AND r.is_cancelled = FALSE
        ORDER BY r.date
    ''', (user['id'],)).fetchall()
    
    conn.close()
    
    return render_template('my_private_reservations.html', 
                         private_reservations=private_reservations)





@app.template_filter('from_json')
def from_json_filter(value):
    """Filtro para parsear JSON en templates"""
    if value and isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return value


if __name__ == '__main__':
    os.makedirs('db', exist_ok=True)
    init_db()
    app.run(debug=True)