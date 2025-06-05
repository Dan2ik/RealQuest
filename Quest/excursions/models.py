from django.db import models
from academic_structure.models import Institute, Department, Direction
from django.conf import settings

class Route(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название маршрута")
    direction = models.ForeignKey(Direction, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Направление")
    first_scene = models.CharField(max_length=100, blank=True, verbose_name="Первая сцена")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Маршрут"
        verbose_name_plural = "Маршруты"

class Quiz(models.Model):
    # OneToOneField должен быть здесь, указывая на Route.
    # primary_key=True делает PK Quiz таким же, как PK Route, обеспечивая 1:1 связь.
    route = models.OneToOneField(Route, on_delete=models.CASCADE, primary_key=True,
                                 related_name='quiz_for_route', verbose_name="Маршрут")
    title = models.CharField(max_length=255, verbose_name="Название теста")
    description = models.TextField(blank=True, verbose_name="Описание теста")

    def __str__(self):
        return f"Тест для маршрута: {self.route.name}" # Теперь можем обращаться к route.name

    class Meta:
        verbose_name = "Тест маршрута"
        verbose_name_plural = "Тесты маршрутов"

class Panorama(models.Model):
    route = models.ForeignKey(Route, related_name='panoramas', on_delete=models.CASCADE, verbose_name="Маршрут")
    scene_id = models.CharField(max_length=100, verbose_name="ID сцены")
    title = models.CharField(max_length=255, verbose_name="Название")
    image = models.ImageField(upload_to='panoramas/', verbose_name="Изображение")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Панорама"
        verbose_name_plural = "Панорамы"
        ordering = ['order']


class HotSpot(models.Model):
    panorama = models.ForeignKey(Panorama, related_name='hotspots', on_delete=models.CASCADE, verbose_name="Панорама")
    # Обратите внимание: ForeignKey на Panorama здесь является "прямой" ссылкой,
    # т.к. Panorama определена выше в этом же файле.
    target_scene = models.ForeignKey(Panorama, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='target_hotspots', verbose_name="Целевая сцена")
    pitch = models.FloatField(verbose_name="Питч")
    yaw = models.FloatField(verbose_name="Яв")
    type = models.CharField(max_length=50, verbose_name="Тип") # Это поле не используется в текущей логике pannellum_config, но может быть полезно
    text = models.CharField(max_length=255, blank=True, verbose_name="Текст")
    target_pitch = models.FloatField(null=True, blank=True, verbose_name="Целевой питч")
    target_yaw = models.FloatField(null=True, blank=True, verbose_name="Целевой яв")

    # Добавьте это поле, чтобы указать, какая JS-функция должна быть вызвана
    # для инфо-точек. Это поле можно будет заполнять в админке.
    # Если вы хотите, чтобы Pannellum всегда использовал одну и ту же функцию для info-точек,
    # то это поле не обязательно, и вы можете захардкодить имя функции в views.py.
    # Но если хотите гибкости, то это поле полезно.
    tooltip_func_name = models.CharField(max_length=100, blank=True, null=True,
                                         verbose_name="Имя JS-функции для подсказки (для типа 'info')")


    def __str__(self):
        return f"Горячая точка {self.id}"

    class Meta:
        verbose_name = "Горячая точка"
        verbose_name_plural = "Горячие точки"


class ReferenceInfo(models.Model):
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Кафедра")
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержание")

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Справочная информация"
        verbose_name_plural = "Справочная информация"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE,
                             verbose_name="Тест")
    question_text = models.TextField(verbose_name="Текст вопроса")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    def __str__(self):
        return f"Вопрос {self.order}: {self.question_text[:50]}..."
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ['order']
        unique_together = ('quiz', 'order')

class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE,
                                 verbose_name="Вопрос")
    choice_text = models.CharField(max_length=255, verbose_name="Текст варианта ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")

    def __str__(self):
        return self.choice_text

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"

class SessionLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Ссылка на вашу кастомную модель User
        on_delete=models.CASCADE,
        verbose_name="Пользователь"
    )
    route = models.ForeignKey(
        'Route', # Если Route определена в этом же файле models.py
        on_delete=models.CASCADE,
        verbose_name="Маршрут"
    )
    start_time = models.DateTimeField(
        auto_now_add=True, # Автоматически устанавливается при создании записи
        verbose_name="Время начала"
    )
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время окончания"
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Маршрут завершен"
    )
    events = models.JSONField(
        default=list, # По умолчанию пустой список для хранения событий
        blank=True,   # Разрешаем быть пустым на уровне формы/админки
        verbose_name="События сессии"
    )

    def __str__(self):
        return f"Сессия {self.user.username} на маршруте '{self.route.name}' (начало: {self.start_time.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = "Лог сессии экскурсии"
        verbose_name_plural = "Логи сессий экскурсий"
        ordering = ['-start_time'] # Сортировка по убыванию времени начала