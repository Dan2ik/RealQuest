from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserAdmin(UserAdmin):
    # Поля, которые будут отображаться в списке пользователей
    list_display = ('email', 'username', 'is_staff', 'is_active')

    # Поля, по которым можно фильтровать
    list_filter = ('is_staff', 'is_superuser', 'is_active')

    # Поля для поиска
    search_fields = ('email', 'username')

    # Порядок полей при редактировании пользователя
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Поля при создании пользователя
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

    # Сортировка по email по умолчанию
    ordering = ('email',)

    # Убираем стандартные поля имени, так как они None
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        # Удаляем поля first_name и last_name, если они есть
        for fieldset in fieldsets:
            if 'fields' in fieldset:
                fieldset_fields = list(fieldset['fields'])
                if 'first_name' in fieldset_fields:
                    fieldset_fields.remove('first_name')
                if 'last_name' in fieldset_fields:
                    fieldset_fields.remove('last_name')
                fieldset['fields'] = tuple(fieldset_fields)
        return fieldsets


# Регистрируем модель с кастомной админ-панелью
admin.site.register(User, CustomUserAdmin)