from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, FloatField, BooleanField, SubmitField, SelectField, IntegerField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange, Optional
from datetime import datetime

def simple_email_validator(form, field):
    """Validacion simple de email sin dependencias externas"""
    email = field.data
    if email and '@' not in email:
        from wtforms import ValidationError
        raise ValidationError('Por favor ingresa un email valido')

class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesion')

class RegisterForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired(), Length(min=3, max=20)])
    first_name = StringField('Nombre', validators=[DataRequired()])
    last_name = StringField('Apellido', validators=[DataRequired()])
    dni = StringField('DNI', validators=[DataRequired(), Length(min=7, max=10)])
    email = StringField('Email', validators=[DataRequired(), simple_email_validator])
    password = PasswordField('Contraseña', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Contraseña', 
                                   validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrarse')

class ReservationForm(FlaskForm):
    title = StringField('Titulo de la Reserva', validators=[DataRequired(), Length(max=100)])
    date = StringField('Fecha y Hora', validators=[DataRequired()], description='Formato: YYYY-MM-DDTHH:MM')
    short_description = TextAreaField('Descripción Breve', 
                                    validators=[DataRequired(), Length(max=200)])
    long_description = TextAreaField('Descripcion Ampliada (Opcional)')
    event_type = SelectField('Tipo de Evento', coerce=int, validators=[DataRequired()])
    is_private = BooleanField('Reserva Privada')
    access_code = StringField('Codigo de Acceso (para reservas privadas)', validators=[Optional()])
    is_free = BooleanField('Reserva Gratuita', default=True)
    price = FloatField('Precio por Persona (solo si no es gratuita)', 
                      validators=[Optional(), NumberRange(min=0)], 
                      default=0)
    guest_count = IntegerField('Numero de Invitados', validators=[DataRequired(), NumberRange(min=1)], default=1)
    special_requirements = TextAreaField('Requisitos Especiales (dietas, alergias, etc.)')
    submit = SubmitField('Crear Reserva')

    def validate_date(self, field):
        """Validacion personalizada para la fecha"""
        try:
            if 'T' not in field.data:
                from wtforms import ValidationError
                raise ValidationError('Formato de fecha invalido. Use: YYYY-MM-DDTHH:MM')
            
            datetime.strptime(field.data, '%Y-%m-%dT%H:%M')
        except ValueError:
            from wtforms import ValidationError
            raise ValidationError('Formato de fecha invalido. Use: YYYY-MM-DDTHH:MM')

    def validate_price(self, field):
        """Validacion personalizada para el precio"""
        if not self.is_free.data and (field.data is None or field.data <= 0):
            from wtforms import ValidationError
            raise ValidationError('Debes especificar un precio mayor a 0 si la reserva no es gratuita')

class PaymentForm(FlaskForm):
    amount = FloatField('Monto a cargar', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Cargar Saldo')

class ProfileForm(FlaskForm):
    first_name = StringField('Nombre', validators=[DataRequired()])
    last_name = StringField('Apellido', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), simple_email_validator])
    submit = SubmitField('Actualizar Perfil')

class FoodSelectionForm(FlaskForm):
    submit = SubmitField('Confirmar Seleccion de Comida')

