from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    # AbstractUser уже имеет:
    # - username (используется для входа по умолчанию)
    # - first_name и last_name - убраны потому что не важны
    # - email (стандартное поле email, НЕ уникальное по умолчанию)
    # - is_staff
    # - is_active
    # - is_superuser
    # - date_joined
    # - groups
    # - user_permissions

    first_name = None
    last_name = None

    username = models.CharField(
        max_length=255,
        unique=False,
        blank=False,
        null=False,
        help_text=_('Обязательно. Не более 255 символов. Разрешены только буквы, цифры и символы @/./+/-/_.'),
    )

    email = models.EmailField(
        unique=True,
        blank=False,
        null=False,
    )

    USERNAME_FIELD = 'email'  # Оставляем email для входа
    REQUIRED_FIELDS = ['username']  # Теперь 'username'  будет запрашиваться

    def __str__(self):
        return self.email  # Или self.username, если он используется как основное представление

    def get_full_name(self):
        return self.username.strip()

    def get_short_name(self):
        return self.username.split(' ')[0].strip() if self.username else ''