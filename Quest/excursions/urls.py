# excursions/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
app_name = 'excursions'

urlpatterns = [
    path('excursion/<int:route_id>/', views.excursion_view, name='excursion_view'),
    path('update-progress/', views.update_progress, name='update_progress'),
    # API-эндпоинты для AJAX
    path('api/get_departments/', views.get_departments_api, name='get_departments_api'),
    path('api/get_directions/', views.get_directions_api, name='get_directions_api'),
    path('api/submit-quiz-answers/', views.submit_quiz_answers, name='submit_quiz_answers'),
]
