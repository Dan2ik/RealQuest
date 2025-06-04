# excursions/views.py

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from .models import Route, Panorama, HotSpot, ReferenceInfo, Quiz, Question, Choice, \
    SessionLog  # SessionLog уже импортирован
from academic_structure.models import Department, Direction
from django.db.models import Prefetch
from django.views.decorators.csrf import csrf_exempt  # Используется для submit_quiz_answers
from django.views.decorators.http import require_POST  # NEW: для log_scene_change_api
import json
from django.utils import timezone


@login_required
def excursion_view(request, route_id):
    # ... (код excursion_view остается таким же, как ты предоставил в предыдущем сообщении)
    # Он уже корректно создает/находит SessionLog, записывает 'excursion_started',
    # добавляет panorama.title в config и передает session_log_id в контекст.
    # Я не буду его здесь повторять для краткости, он у тебя есть.
    route = get_object_or_404(
        Route.objects.select_related('direction__department').prefetch_related(
            Prefetch(
                'panoramas',
                queryset=Panorama.objects.order_by('order').prefetch_related('hotspots')
            ),
            Prefetch(
                'quiz_for_route',
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

    actual_first_scene_id = route.first_scene
    actual_first_scene_title = "Начальная сцена не определена (маршрут без панорам?)"
    panoramas_on_route = list(route.panoramas.all())

    if not actual_first_scene_id and panoramas_on_route:
        actual_first_scene_id = panoramas_on_route[0].scene_id

    scenes_for_pannellum = {}
    if panoramas_on_route:
        for panorama in panoramas_on_route:
            scene_id = panorama.scene_id
            if scene_id == actual_first_scene_id:
                actual_first_scene_title = panorama.title

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
                elif hotspot_obj.type == 'info' and hotspot_obj.tooltip_func_name:
                    hotspot_data["type"] = "info"
                    hotspot_data["clickHandlerFunc"] = hotspot_obj.tooltip_func_name
                    hotspot_data["clickHandlerArgs"] = {"hotspotId": hotspot_obj.id, "text": hotspot_obj.text}
                hotspots_for_pannellum.append(hotspot_data)

            scenes_for_pannellum[scene_id] = {
                "title": panorama.title,
                "type": "equirectangular",
                "panorama": panorama.image.url,
                "hotSpots": hotspots_for_pannellum
            }

    config = {
        "default": {
            "firstScene": actual_first_scene_id,
            "autoLoad": True,
            "sceneFadeDuration": 1000
        },
        "scenes": scenes_for_pannellum
    }

    session_log, created = SessionLog.objects.get_or_create(
        user=request.user,
        route=route,
        is_completed=False,
        defaults={'start_time': timezone.now()}
    )

    if created:
        initial_event = {
            "timestamp": timezone.now().isoformat(),
            "type": "excursion_started",
            "message": f"Экскурсия '{route.name}' начата.",
        }
        if actual_first_scene_id:
            initial_event["scene_id"] = actual_first_scene_id
            initial_event["scene_title"] = actual_first_scene_title
        else:
            initial_event["message"] += " Начальная сцена не найдена."
        session_log.events.append(initial_event)
        session_log.save()

    department_info = None
    department_reference_infos = []
    if route.direction and route.direction.department:
        department_info = route.direction.department
        department_reference_infos = ReferenceInfo.objects.filter(
            department=department_info
        ).order_by('title')

    quiz_data_for_js = None
    if hasattr(route, 'quiz_for_route'):
        single_quiz = route.quiz_for_route
        quiz_json = {
            'id': single_quiz.pk,
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

    context = {
        'route': route,
        'pannellum_config': config,
        'department_info': department_info,
        'department_reference_infos': department_reference_infos,
        'quiz_data_for_js': quiz_data_for_js,
        'session_log_id': session_log.id
    }
    return render(request, 'excursions/excursion.html', context)


# NEW: API endpoint для логирования смены сцены
@login_required
@require_POST  # Эта view будет принимать только POST запросы
@csrf_exempt  # Пока оставляем, но в идеале JS должен отправлять CSRF-токен.
# Если JS будет отправлять 'X-CSRFToken' заголовок, этот декоратор можно будет убрать.
def log_scene_change_api(request):
    try:
        data = json.loads(request.body)
        session_log_id = data.get('session_log_id')
        scene_id = data.get('scene_id')
        scene_title = data.get('scene_title')  # Мы добавили title в pannellum_config

        if not all([session_log_id, scene_id, scene_title]):
            return JsonResponse({'status': 'error', 'message': 'Missing data'}, status=400)

        try:
            # Ищем лог сессии, принадлежащий текущему пользователю
            session_log = SessionLog.objects.get(id=session_log_id, user=request.user)
        except SessionLog.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Session log not found or access denied'}, status=404)

        event = {
            "timestamp": timezone.now().isoformat(),
            "type": "scene_change",
            "scene_id": scene_id,
            "scene_title": scene_title
        }
        session_log.events.append(event)
        session_log.save(update_fields=['events'])  # Обновляем только поле events для эффективности

        return JsonResponse({'status': 'success', 'message': 'Scene change logged'})

    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        # Логируем ошибку на сервере для отладки
        print(f"Error in log_scene_change_api: {e}")
        return JsonResponse({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}, status=500)


@login_required
@csrf_exempt  # Оставляем для совместимости с текущим JS кодом отправки теста
def submit_quiz_answers(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quiz_id = data.get('quiz_id')
            user_answers = data.get('answers')
            # ПОДГОТОВКА: Нам понадобится session_log_id, который JS должен будет передать
            session_log_id = data.get('session_log_id')

            if not quiz_id or not user_answers:  # session_log_id пока не обязателен для текущей логики ответа
                return JsonResponse({'error': 'Missing quiz_id or answers'}, status=400)

            quiz = get_object_or_404(Quiz, pk=quiz_id)
            score = 0
            total_questions = 0
            results_for_log = []  # Для будущего логирования в SessionLog
            detailed_results_for_response = []  # Для ответа клиенту

            for question_id, submitted_choice_id in user_answers.items():
                try:
                    question = Question.objects.get(id=question_id, quiz=quiz)
                    total_questions += 1
                    correct_choice = question.choices.filter(is_correct=True).first()
                    is_correct_answer = False
                    if correct_choice and str(correct_choice.id) == str(submitted_choice_id):
                        score += 1
                        is_correct_answer = True

                    detailed_results_for_response.append({
                        'question_id': question.id,
                        'question_text': question.question_text,
                        'submitted_choice_id': submitted_choice_id,
                        'correct_choice_id': correct_choice.id if correct_choice else None,
                        'is_correct': is_correct_answer
                    })
                    results_for_log.append({  # Это будет использоваться для записи в SessionLog.events
                        'question_id': question.id,
                        'question_text_preview': question.question_text[:50] + "...",  # Краткий текст вопроса
                        'submitted_choice_id': submitted_choice_id,
                        'is_correct': is_correct_answer
                    })
                except Question.DoesNotExist:
                    detailed_results_for_response.append({
                        'question_id': question_id, 'error': 'Question not found in quiz'
                    })
                    results_for_log.append({
                        'question_id': question_id, 'error': 'Question not found'
                    })
                except Exception as e:  # Обработка других ошибок для конкретного вопроса
                    detailed_results_for_response.append({
                        'question_id': question_id, 'error': f'Error processing question: {str(e)}'
                    })
                    results_for_log.append({
                        'question_id': question_id, 'error': f'Error processing question: {str(e)}'
                    })

            # ЗАДЕЛ НА БУДУЩЕЕ: Логирование результатов теста в SessionLog
            # Этот блок будет раскомментирован и доработан, когда мы займемся логированием теста.
            # JS должен будет передавать session_log_id.
            if session_log_id:
                try:
                    log_entry = SessionLog.objects.get(id=session_log_id, user=request.user)
                    quiz_event = {
                        "timestamp": timezone.now().isoformat(),
                        "type": "quiz_submitted",
                        "quiz_id": quiz_id,
                        "quiz_title": quiz.title,  # Добавим название теста для удобства
                        "score": score,
                        "total_questions": total_questions,
                        "percentage": (score / total_questions * 100) if total_questions > 0 else 0,
                        "answers_summary": results_for_log  # Сохраняем подготовленные данные
                    }
                    log_entry.events.append(quiz_event)

                    # Если прохождение теста означает завершение маршрута,
                    # можно здесь установить is_completed = True и end_time
                    # log_entry.is_completed = True
                    # log_entry.end_time = timezone.now()

                    log_entry.save(update_fields=['events'])  # , 'is_completed', 'end_time']) # если обновляем и их
                    print(f"Quiz results logged for session {session_log_id}")  # Для отладки
                except SessionLog.DoesNotExist:
                    print(f"Error: SessionLog with id {session_log_id} not found for quiz submission.")
                except Exception as e:
                    print(f"Error saving quiz results to SessionLog: {e}")
            else:
                print("Warning: session_log_id not provided for quiz submission, results not logged in SessionLog.")

            return JsonResponse({
                'success': True, 'quiz_id': quiz_id, 'score': score,
                'total_questions': total_questions,
                'percentage': (score / total_questions * 100) if total_questions > 0 else 0,
                'results': detailed_results_for_response
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            print(f"Error in submit_quiz_answers: {e}")  # Логируем ошибку на сервере
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)
    else:
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)


# API endpoints для динамической фильтрации (оставляем без изменений)
def get_departments_api(request):
    # ... (ваш код) ...
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
    # ... (ваш код) ...
    department_id = request.GET.get('department_id')
    directions_data = []

    if department_id:
        directions = Direction.objects.filter(department_id=department_id).order_by('name')
        directions_data = [{'id': direc.id, 'name': direc.name} for direc in directions]

    return JsonResponse(directions_data, safe=False)


# Ваша заглушка, пока не нужна для логирования сцен
def update_progress(request):
    return HttpResponse("OK")