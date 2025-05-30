from django.urls import path
from . import views

app_name = 'academic_structure'

urlpatterns = [
    #search/ path('academic/search/', views.hierarchical_selection_view, name='hierarchical_selection'),
    path('search/', views.combined_selection_view, name='combined_selection'),
    path('ajax/load-departments/', views.load_departments, name='ajax_load_departments'),
    path('ajax/load-directions/', views.load_directions, name='ajax_load_directions'),
]