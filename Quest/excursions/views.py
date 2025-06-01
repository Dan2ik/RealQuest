# excursions/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Route, Panorama
# import json  <-- Этот импорт больше не нужен здесь, если вы используете только для pannellum_config
from academic_structure.models import Department, Direction
from django.db.models import Prefetch

@login_required
def excursion_view(request, route_id):

    route = get_object_or_404(
        Route.objects.prefetch_related('panoramas'),
        id=route_id
    )



    scenes = {}
    for i, panorama in enumerate(route.panoramas.all(), start=1):
        scenes[f"scene{i}"] = {
            "type": "equirectangular",
            "panorama": panorama.image.url,  # Используем .url поля ImageField
            "hotSpots": []
        }

    config = {
        "default": {
            "firstScene": "scene1",
            "autoLoad": True,
            "sceneFadeDuration": 1000
        },
        "scenes": scenes
    }
    print(route)
    return render(request, 'excursions/excursion.html', {
        'route': route,
        'pannellum_config': config # <--- ПЕРЕДАЙТЕ Python-ОБЪЕКТ НАПРЯМУЮ!
    })

# API endpoints для динамической фильтрации (оставляем без изменений)
def get_departments_api(request):
    try:
        institute_id = request.GET.get('institute_id')
        if not institute_id:
            return JsonResponse({'error': 'Missing institute_id'}, status=400)

        departments = Department.objects.filter(institute_id=institute_id).order_by('name')
        return JsonResponse(
            [{'id': dep.id, 'name': dep.name} for dep in departments],
            safe=False
        )
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_directions_api(request):
    department_id = request.GET.get('department_id')
    directions_data = []

    if department_id:
        directions = Direction.objects.filter(department_id=department_id).order_by('name')
        directions_data = [{'id': direc.id, 'name': direc.name} for direc in directions]

    return JsonResponse(directions_data, safe=False)