# excursions/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Route, Panorama, HotSpot # Добавили HotSpot
from academic_structure.models import Department, Direction
from django.db.models import Prefetch # Для эффективной выборки связанных объектов
from django.conf import settings
from django.views.decorators.http import require_POST

@require_POST
@login_required
def update_progress(request):
    data = json.loads(request.body)
    route_id = data.get('route_id')
    scene_id = data.get('scene_id')

    route = get_object_or_404(Route, id=route_id)
    all_scene_ids = list(route.panoramas.values_list('scene_id', flat=True))

    progress_obj, created = UserRouteProgress.objects.get_or_create(
        user=request.user,
        route=route,
        defaults={'visited_scenes': [], 'last_scene_id': scene_id}
    )

    if scene_id not in progress_obj.visited_scenes:
        progress_obj.visited_scenes.append(scene_id)

    progress_obj.last_scene_id = scene_id
    progress_obj.progress_percent = round(len(progress_obj.visited_scenes) / len(all_scene_ids) * 100, 2)
    progress_obj.updated_at = timezone.now()
    progress_obj.save()

    return JsonResponse({
        "success": True,
        "progress_percent": progress_obj.progress_percent
    })
@login_required
def update_progress(request):
    data = json.loads(request.body)
    route_id = data.get('route_id')
    scene_id = data.get('scene_id')

    route = get_object_or_404(Route, id=route_id)
    all_scene_ids = list(route.panoramas.values_list('scene_id', flat=True))

    progress_obj, created = UserRouteProgress.objects.get_or_create(
        user=request.user,
        route=route,
        defaults={'visited_scenes': [], 'last_scene_id': scene_id}
    )

    if scene_id not in progress_obj.visited_scenes:
        progress_obj.visited_scenes.append(scene_id)

    progress_obj.last_scene_id = scene_id
    progress_obj.progress_percent = round(len(progress_obj.visited_scenes) / len(all_scene_ids) * 100, 2)
    progress_obj.updated_at = timezone.now()
    progress_obj.save()

    return JsonResponse({
        "success": True,
        "progress_percent": progress_obj.progress_percent
    })

@login_required
def excursion_view(request, route_id):
    # Получение маршрута по id из базы данных сортировка по order
    # также загружаются сразу hotspotы
    route = get_object_or_404(
        Route.objects.prefetch_related(
            Prefetch(
                'panoramas',
                queryset=Panorama.objects.order_by('order').prefetch_related('hotspots')
            )
        ),
        id=route_id
    )
    #словарь для хренения сцен(панорам
    scenes = {}
    #id первой сцены берем сразу или ищем ниже
    first_scene_id = route.first_scene if route.first_scene else None

    # Итерируем по панорамам маршрута
    for panorama in route.panoramas.all():
        count=0
        scene_id = panorama.scene_id
        # Если в маршруте не указана первая сцена, используем первую панораму в порядке
        if not first_scene_id:
            first_scene_id = scene_id

        hotspots_for_pannellum = []
        # Итерируем по горячим точкам, связанным с текущей панорамой
        for hotspot_obj in panorama.hotspots.all():
            count+=1
            hotspot_data = {
                "pitch": hotspot_obj.pitch,
                "yaw": hotspot_obj.yaw,
                "text": hotspot_obj.text,
            }
            print("hotspot:" + str(hotspot_data))

            if hotspot_obj.target_scene:  # Убрали искусственное if True
                # Это горячая точка-ссылка на другую сцену
                hotspot_data["type"] = "scene"
                hotspot_data["sceneId"] = hotspot_obj.target_scene.scene_id
                if hotspot_obj.target_pitch is not None:
                    hotspot_data["targetPitch"] = hotspot_obj.target_pitch
                if hotspot_obj.target_yaw is not None:
                    hotspot_data["targetYaw"] = hotspot_obj.target_yaw

            hotspots_for_pannellum.append(hotspot_data)
            print("hotspot_for_pannellum:" + str(hotspots_for_pannellum))
            print("count hotspots:" + str(count))
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

    print(f"Загрузка маршрута: {route.name} (ID: {route.id}) (Congig: {config}")
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