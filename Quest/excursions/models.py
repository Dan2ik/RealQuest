from django.db import models
from academic_structure.models import Institute, Department, Direction


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