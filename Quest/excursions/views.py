# excursions/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Route, Panorama, HotSpot # Добавили HotSpot
from academic_structure.models import Department, Direction
from django.db.models import Prefetch # Для эффективной выборки связанных объектов

@login_required
def excursion_view(request, route_id):
    # Предварительно загружаем панорамы маршрута, упорядоченные по 'order',
    # и их связанные горячие точки.
    # Это позволяет избежать множества запросов к БД (N+1 проблема).
    route = get_object_or_404(
        Route.objects.prefetch_related(
            Prefetch(
                'panoramas',
                queryset=Panorama.objects.order_by('order').prefetch_related('hotspots')
            )
        ),
        id=route_id
    )

    scenes = {}
    first_scene_id = route.first_scene if route.first_scene else None

    # Итерируем по панорамам маршрута
    for panorama in route.panoramas.all():
        scene_id = panorama.scene_id

        # Если в маршруте не указана первая сцена, используем первую панораму в порядке
        if not first_scene_id:
            first_scene_id = scene_id

        hotspots_for_pannellum = []
        # Итерируем по горячим точкам, связанным с текущей панорамой
        for hotspot_obj in panorama.hotspots.all():
            hotspot_data = {
                "pitch": hotspot_obj.pitch,
                "yaw": hotspot_obj.yaw,
                "text": hotspot_obj.text,
                # Свойство 'type' для Pannellum будет определено ниже
            }

            if hotspot_obj.target_scene:
                # Это горячая точка-ссылка на другую сцену
                hotspot_data["type"] = "scene"
                hotspot_data["target"] = hotspot_obj.target_scene.scene_id
                if hotspot_obj.target_pitch is not None:
                    hotspot_data["targetPitch"] = hotspot_obj.target_pitch
                if hotspot_obj.target_yaw is not None:
                    hotspot_data["targetYaw"] = hotspot_obj.target_yaw
            else:
                hotspot_data["type"] = "info"  # Или hotspot_obj.type, если у вас это поле используется
                # Имя JS-функции для подсказки
                if hotspot_obj.tooltip_func_name:  # Проверяем, что поле заполнено
                    hotspot_data["tooltip_func_name"] = hotspot_obj.tooltip_func_name
                else:
                    # Если tooltip_func_name не указано, можно использовать дефолтную функцию
                    hotspot_data["tooltip_func_name"] = "hotspotInfo"

            hotspots_for_pannellum.append(hotspot_data)

        scenes[scene_id] = {
            "type": "equirectangular",
            "panorama": panorama.image.url,
            "hotSpots": hotspots_for_pannellum
        }

    config = {
        "default": {
            "firstScene": first_scene_id,
            "autoLoad": True,
            "sceneFadeDuration": 1000
        },
        "scenes": scenes
    }

    print(f"Загрузка маршрута: {route.name} (ID: {route.id})")
    return render(request, 'excursions/excursion.html', {
        'route': route,
        'pannellum_config': config
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