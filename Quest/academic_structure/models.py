from django.db import models

class Institute(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Название института")

    class Meta:
        db_table = 'institutes'
        verbose_name = 'Институт'
        verbose_name_plural = 'Институты'
        ordering = ['name']

    def __str__(self):
        return self.name

class Department(models.Model): # Единственное число
    name = models.CharField(max_length=255, verbose_name="Название кафедры")
    institute = models.ForeignKey(
        Institute,
        on_delete=models.CASCADE, # Если институт удаляется, удаляются и все его кафедры

        null=False,
        blank=False,
        verbose_name="Институт",
        related_name='departments'
    )

    class Meta:
        db_table = 'departments' # Соответствует твоему DDL
        verbose_name = 'Кафедра'
        verbose_name_plural = 'Кафедры'
        ordering = ['institute', 'name'] # Сортировка сначала по институту, потом по названию кафедры
        unique_together = [['name', 'institute']]

    def __str__(self):
        return f"{self.name} ({self.institute.name if self.institute else 'Без института'})"

class Direction(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название направления")
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        verbose_name="Кафедра",
        related_name='directions'
    )

    class Meta:
        db_table = 'directions'
        verbose_name = 'Направление'
        verbose_name_plural = 'Направления'
        ordering = ['department', 'name']
        unique_together = [['name', 'department']]

    def __str__(self):
        return f"{self.name} ({self.department.name if self.department else 'Без кафедры'})"