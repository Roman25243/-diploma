from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, FloatField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, ValidationError, NumberRange
from models import User


class RegistrationForm(FlaskForm):
    """Форма реєстрації користувача"""
    name = StringField('Ім\'я', validators=[
        DataRequired(message='Ім\'я обов\'язкове'),
        Length(min=2, max=100, message='Ім\'я має бути від 2 до 100 символів')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(message='Email обов\'язковий'),
        Email(message='Введіть коректний email адресу')
    ])
    
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обов\'язковий'),
        Length(min=6, message='Пароль має бути мінімум 6 символів')
    ])
    
    def validate_email(self, email):
        """Перевірка унікальності email"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Цей email вже зареєстрований. Використайте інший.')


class LoginForm(FlaskForm):
    """Форма входу"""
    email = StringField('Email', validators=[
        DataRequired(message='Email обов\'язковий'),
        Email(message='Введіть коректний email адресу')
    ])
    
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обов\'язковий')
    ])


class FilmForm(FlaskForm):
    """Форма додавання/редагування фільму"""
    title = StringField('Назва фільму', validators=[
        DataRequired(message='Назва обов\'язкова'),
        Length(max=100, message='Назва занадто довга (максимум 100 символів)')
    ])
    
    description = TextAreaField('Опис', validators=[
        DataRequired(message='Опис обов\'язковий'),
        Length(min=10, message='Опис має бути мінімум 10 символів')
    ])
    
    genre = StringField('Жанр', validators=[
        Length(max=100, message='Жанр занадто довгий (максимум 100 символів)')
    ])
    
    director = StringField('Режисер', validators=[
        Length(max=100, message='Ім\'я режисера занадто довге (максимум 100 символів)')
    ])
    
    actors = TextAreaField('Актори (через кому)', validators=[
        Length(max=500, message='Список акторів занадто довгий (максимум 500 символів)')
    ])
    
    duration = IntegerField('Тривалість (хвилин)', validators=[
        NumberRange(min=1, max=500, message='Тривалість має бути від 1 до 500 хвилин')
    ])
    
    age_rating = SelectField('Віковий рейтинг', 
        choices=[
            ('', 'Не вказано'),
            ('G', 'G - Для всіх'),
            ('PG', 'PG - Рекомендовано з батьками'),
            ('PG-13', 'PG-13 - Дітям до 13 з батьками'),
            ('R', 'R - 16+'),
            ('NC-17', 'NC-17 - 18+')
        ]
    )
    
    release_year = IntegerField('Рік випуску', validators=[
        NumberRange(min=1900, max=2030, message='Рік випуску має бути від 1900 до 2030')
    ])
    
    trailer = StringField('URL трейлера (YouTube)', validators=[
        Length(max=200, message='URL занадто довгий')
    ])
    
    image = FileField('Постер фільму', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 
                   message='Дозволені тільки зображення (jpg, png, gif, webp)')
    ])


class SessionForm(FlaskForm):
    """Форма створення сеансу"""
    start_time = StringField('Час початку (наприклад: 2024-03-15 18:00)', validators=[
        DataRequired(message='Час початку обов\'язковий'),
        Length(max=50, message='Формат часу занадто довгий')
    ])
    
    price = FloatField('Ціна квитка (грн)', validators=[
        DataRequired(message='Ціна обов\'язкова'),
        NumberRange(min=0, max=10000, message='Ціна має бути від 0 до 10000 грн')
    ])


class ReviewForm(FlaskForm):
    """Форма додавання відгуку"""
    rating = SelectField('Оцінка', 
        choices=[(5, '⭐⭐⭐⭐⭐ Чудово'), 
                 (4, '⭐⭐⭐⭐ Добре'), 
                 (3, '⭐⭐⭐ Нормально'), 
                 (2, '⭐⭐ Погано'), 
                 (1, '⭐ Жахливо')],
        coerce=int,
        validators=[DataRequired(message='Оберіть оцінку')]
    )
    
    comment = TextAreaField('Відгук (необов\'язково)', validators=[
        Length(max=1000, message='Відгук занадто довгий (максимум 1000 символів)')
    ])
