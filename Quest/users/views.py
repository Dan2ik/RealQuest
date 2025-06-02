from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, \
    logout
from django.shortcuts import render, redirect

from .forms import UserCreationForm as CustomUserCreationForm, UserLoginForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate # Добавлен authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm # Импортируем, если UserLoginForm её наследует или используется

from .forms import UserCreationForm as CustomUserCreationForm, UserLoginForm # Предполагаем, что UserLoginForm - это ваша форма
from django.contrib.auth.decorators import login_required

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('login') # Имя URL-шаблона для страницы входа
        else:
            for field in form:
                for error in field.errors:
                     messages.error(request, f"{form.fields[field.name].label or field.name}: {error}")
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):

    if request.user.is_authenticated:
        return redirect('academic_structure:combined_selection')

    if request.method == 'POST':
        # UserLoginForm (наследник AuthenticationForm) принимает request первым аргументом
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            display_name = user.get_full_name() or user.email
            messages.success(request, f'Добро пожаловать, {display_name}!')
            return redirect(settings.LOGIN_REDIRECT_URL) # Убедись, что LOGIN_REDIRECT_URL определен
        else:
            pass
            # messages.error(request, 'Неверный Email (или логин) или пароль. Пожалуйста, проверьте введенные данные.')
    else:
        form = UserLoginForm(request) # Передаем request и для GET-запроса
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    # Убедись, что LOGOUT_REDIRECT_URL определен в settings.py
    # Если не определен, можно перенаправить на главную или страницу входа:
    # return redirect(settings.LOGOUT_REDIRECT_URL or 'login')
    return redirect(settings.LOGOUT_REDIRECT_URL)

@login_required
def dashboard_view(request):
    return render(request, 'users/dashboard.html')