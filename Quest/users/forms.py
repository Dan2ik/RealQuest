from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _

from .models import *


class UserCreationForm(UserCreationForm):
    """
    Кастомная форма для регистрации пользователей.
    Запрашивает email (для входа), username (который используется как "полное имя")
    и пароль с подтверждением.
    """

    username = forms.CharField(
        label=_('Полное имя'), #
        max_length=255,
        help_text=_('Введите ваше полное имя.')
    )

    # Email уже будет включен UserCreationForm, так как он является USERNAME_FIELD.
    # Мы можем переопределить его виджет или label, если нужно, но обычно это не требуется.
    email = forms.EmailField(label=_("Электронная почта"))

    class Meta(UserCreationForm.Meta):
        model = User
        # Поля, которые будут отображаться на форме регистрации.
        # 'email' (USERNAME_FIELD) и 'password' (с подтверждением)
        # автоматически обрабатываются UserCreationForm.
        # Нам нужно только добавить 'username' (наше "полное имя").
        fields = ('email', 'username')

    def clean_email(self):
        # Валидация на уникальность email (регистронезависимая)
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_("Пользователь с таким email уже существует."))
        return email

    # def clean_username(self):
    #     # Если нужна какая-то специфическая валидация для "полного имени" (нашего username)
    #     username = self.cleaned_data.get('username')
    #     # Например, проверка на минимальную длину или допустимые символы (хотя CharField это уже делает)
    #     # if len(username) < 2:
    #     #     raise forms.ValidationError(_("Полное имя должно содержать хотя бы 2 символа."))
    #     return username

    # Метод save из UserCreationForm уже корректно сохранит все поля,
    # включая наш 'username' (полное имя) и 'email'.
    # Пароль также будет корректно хеширован.


class UserLoginForm(AuthenticationForm):
    """
    Форма входа. Мы можем использовать стандартную AuthenticationForm,
    она будет работать с нашим USERNAME_FIELD='email'.
    Если нужны какие-то кастомные поля или логика, можно переопределить.
    """
    # AuthenticationForm по умолчанию использует 'username' как label для поля логина.
    # Так как у нас USERNAME_FIELD = 'email', мы хотим, чтобы label был "Email".
    # Это можно сделать, переопределив поле.
    username = forms.EmailField( # Тип поля EmailField, чтобы была валидация email
        label=_("Email"),
        widget=forms.EmailInput(attrs={'autofocus': True})
    )

    # Поле password уже есть в AuthenticationForm.

    # Если ты хочешь полностью свою форму, а не наследовать от AuthenticationForm:
    # email = forms.EmailField(label=_("Email"), widget=forms.EmailInput(attrs={'autofocus': True}))
    # password = forms.CharField(
    #     label=_("Пароль"),
    #     strip=False, # Не удалять пробелы в начале/конце пароля
    #     widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    # )

    # Если наследуешься от AuthenticationForm, то метод clean и обработка ошибок
    # (например, "неактивный пользователь" или "неверные учетные данные")
    # уже встроены.