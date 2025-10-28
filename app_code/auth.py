from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms import LoginForm, RegisterForm
from .models import User
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and check_password_hash(user['password'], form.password.data):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['logged_in'] = True
            flash('Inicio de sesion exitoso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    return render_template('login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        success = User.create(
            form.username.data,
            form.first_name.data,
            form.last_name.data,
            form.dni.data,
            form.email.data,
            hashed_password
        )
        if success:
            flash('Registro exitoso! Ahora puedes iniciar sesion', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('El usuario, email o DNI ya existen', 'error')
    return render_template('register.html', form=form)

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesion', 'info')
    return redirect(url_for('index'))
