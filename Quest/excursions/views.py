from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Route, Panorama, HotSpot, ReferenceInfo, Quiz, Question, Choice
from academic_structure.models import Department, Direction
from django.db.models import Prefetch
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def excursion_view(request, route_id):
    # Получение маршрута.
    # Используем select_related для 'direction__department'.
    # Для получения теста, используем Prefetch для обратной связи 'quiz_for_route'
    # с вложенными вопросами и ответами.
    route = get_object_or_404(
        Route.objects.select_related('direction__department').prefetch_related(
            Prefetch(
                'panoramas',
                queryset=Panorama.objects.order_by('order').prefetch_related('hotspots')
            ),
            # НОВОЕ: Prefetch для получения связанного Quiz (через обратную связь)
            # и его вопросов/вариантов ответов
            Prefetch(
                'quiz_for_route', # Имя related_name из OneToOneField в модели Quiz
                queryset=Quiz.objects.prefetch_related(
                    Prefetch(
                        'questions',
                        queryset=Question.objects.order_by('order').prefetch_related('choices')
                    )
                )
            )
        ),
        id=route_id
    )

    scenes = {}
    first_scene_id = route.first_scene if route.first_scene else None

    for panorama in route.panoramas.all():
        scene_id = panorama.scene_id
        if not first_scene_id:
            first_scene_id = scene_id

        hotspots_for_pannellum = []
        for hotspot_obj in panorama.hotspots.all():
            hotspot_data = {
                "pitch": hotspot_obj.pitch,
                "yaw": hotspot_obj.yaw,
                "text": hotspot_obj.text,
            }
            if hotspot_obj.target_scene:
                hotspot_data["type"] = "scene"
                hotspot_data["sceneId"] = hotspot_obj.target_scene.scene_id
                if hotspot_obj.target_pitch is not None:
                    hotspot_data["targetPitch"] = hotspot_obj.target_pitch
                if hotspot_obj.target_yaw is not None:
                    hotspot_data["targetYaw"] = hotspot_obj.target_yaw

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

    department_info = None
    department_reference_infos = []

    if route.direction and route.direction.department:
        department_info = route.direction.department
        department_reference_infos = ReferenceInfo.objects.filter(
            department=department_info
        ).order_by('title')

    # Данные теста для JavaScript
    quiz_data_for_js = None
    # Теперь тест доступен через обратную связь: route.quiz_for_route
    if hasattr(route, 'quiz_for_route'): # Проверяем, существует ли связанный тест
        single_quiz = route.quiz_for_route # Получаем объект теста, он уже Prefetched

        quiz_json = {
            'id': single_quiz.pk, # Используем primary key, который является PK Route
            'title': single_quiz.title,
            'description': single_quiz.description,
            'questions': []
        }
        for question in single_quiz.questions.all():
            question_json = {
                'id': question.id,
                'question_text': question.question_text,
                'choices': []
            }
            for choice in question.choices.all():
                question_json['choices'].append({
                    'id': choice.id,
                    'choice_text': choice.choice_text,
                })
            quiz_json['questions'].append(question_json)
        quiz_data_for_js = quiz_json


    return render(request, 'excursions/excursion.html', {
        'route': route, # route сам по себе, но у него теперь есть доступ к quiz_for_route
        'pannellum_config': config,
        'department_info': department_info,
        'department_reference_infos': department_reference_infos,
        'quiz_data_for_js': quiz_data_for_js
    })

# API endpoint для обработки ответов на тест (ОСТАЕТСЯ БЕЗ ИЗМЕНЕНИЙ)
@login_required
@csrf_exempt
def submit_quiz_answers(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quiz_id = data.get('quiz_id') # quiz_id здесь будет PK Route
            user_answers = data.get('answers')

            if not quiz_id or not user_answers:
                return JsonResponse({'error': 'Missing quiz_id or answers'}, status=400)

            # Получаем объект Quiz по его PK (который является PK Route)
            quiz = get_object_or_404(Quiz, pk=quiz_id)

            score = 0
            total_questions = 0
            results = []

            for question_id, submitted_choice_id in user_answers.items():
                try:
                    question = Question.objects.get(id=question_id, quiz=quiz)
                    total_questions += 1
                    correct_choice = question.choices.filter(is_correct=True).first()

                    is_correct_answer = False
                    if correct_choice and str(correct_choice.id) == str(submitted_choice_id):
                        score += 1
                        is_correct_answer = True

                    results.append({
                        'question_id': question.id,
                        'question_text': question.question_text,
                        'submitted_choice_id': submitted_choice_id,
                        'correct_choice_id': correct_choice.id if correct_choice else None,
                        'is_correct': is_correct_answer
                    })
                except Question.DoesNotExist:
                    results.append({
                        'question_id': question_id,
                        'error': 'Question not found in quiz'
                    })
                except Exception as e:
                    results.append({
                        'question_id': question_id,
                        'error': f'Error processing question: {str(e)}'
                    })

            return JsonResponse({
                'success': True,
                'quiz_id': quiz_id,
                'score': score,
                'total_questions': total_questions,
                'percentage': (score / total_questions * 100) if total_questions > 0 else 0,
                'results': results
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
# API endpoints для динамической фильтрации (оставляем без изменений)
# ... (get_departments_api, get_directions_api)
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
