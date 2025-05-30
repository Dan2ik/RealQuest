# --- Для каскадного выбора ---
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import HierarchicalSelectionForm, DirectionSearchForm
from .models import Department, Direction


@login_required
def combined_selection_view(request):
    # Инициализируем обе формы
    # hierarchical_form будет обрабатывать POST для показа выбранного направления
    # search_form будет обрабатывать GET для результатов поиска

    hierarchical_form_data = None
    search_form_data = None

    selected_direction_obj = None
    search_results = Direction.objects.none()
    is_search_active = False  # Флаг, что был выполнен поиск по названию

    if request.method == 'POST':
        # Предполагаем, что POST идет от иерархической формы (т.к. у нее method="POST")
        # Если бы обе формы отправлялись через POST, понадобилось бы различать их (например, по имени кнопки)
        hierarchical_form_data = request.POST
        form_h = HierarchicalSelectionForm(hierarchical_form_data)
        if form_h.is_valid():
            selected_direction_obj = form_h.cleaned_data.get('direction')
        hierarchical_form = form_h  # передаем в контекст форму с данными (и возможными ошибками)
        search_form = DirectionSearchForm()  # форма поиска остается чистой

    elif request.method == 'GET':
        # GET может быть для простого отображения страницы или для поиска по названию
        hierarchical_form = HierarchicalSelectionForm()  # Чистая иерархическая форма

        if 'query' in request.GET and request.GET['query'].strip():  # Если есть параметр query и он не пустой
            search_form_data = request.GET
            form_s = DirectionSearchForm(search_form_data)
            if form_s.is_valid():
                query = form_s.cleaned_data['query']
                search_results = Direction.objects.filter(name__icontains=query) \
                    .select_related('department', 'department__institute') \
                    .order_by('name')
            search_form = form_s  # передаем в контекст форму поиска с данными (и возможными ошибками)
            is_search_active = True
        else:
            search_form = DirectionSearchForm()  # Чистая форма поиска

    else:  # Другие методы (PUT, DELETE и т.д.) - маловероятно для этих форм
        hierarchical_form = HierarchicalSelectionForm()
        search_form = DirectionSearchForm()

    context = {
        'hierarchical_form': hierarchical_form,
        'search_form': search_form,
        'selected_direction': selected_direction_obj,  # Результат иерархического выбора
        'search_results': search_results,  # Результаты поиска по названию
        'is_search_active': is_search_active,  # Флаг, был ли поиск по названию
    }
    return render(request, 'academic_structure/combined_selection.html', context)


def load_departments(request):
    institute_id = request.GET.get('institute_id')
    departments = Department.objects.filter(institute_id=institute_id).order_by('name')
    return JsonResponse(list(departments.values('id', 'name')), safe=False)


def load_directions(request):
    department_id = request.GET.get('department_id')
    directions = Direction.objects.filter(department_id=department_id).order_by('name')
    return JsonResponse(list(directions.values('id', 'name')), safe=False)



