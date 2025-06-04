from django.contrib import admin
from .models import Route, Panorama, HotSpot, ReferenceInfo, Quiz, Question, Choice

# --- Инлайны для Тестов ---
class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    min_num = 2

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    min_num = 1
    inlines = [ChoiceInline]  # Вложенность инлайнов в стандартном ModelAdmin

class QuizInline(admin.StackedInline):
    model = Quiz
    extra = 1
    max_num = 1
    can_delete = True
    inlines = [QuestionInline]  # Вложенность инлайнов в стандартном ModelAdmin

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'direction', 'first_scene')
    search_fields = ('name',)
    inlines = [QuizInline]

@admin.register(Panorama)
class PanoramaAdmin(admin.ModelAdmin):
    list_display = ('title', 'route', 'order', 'scene_id')
    list_filter = ('route',)
    search_fields = ('title', 'scene_id')
    ordering = ('route', 'order',)

@admin.register(HotSpot)
class HotSpotAdmin(admin.ModelAdmin):
    list_display = ('panorama', 'pitch', 'yaw', 'text', 'target_scene', 'type')
    list_filter = ('panorama__route', 'panorama')
    search_fields = ('text',)

@admin.register(ReferenceInfo)
class ReferenceInfoAdmin(admin.ModelAdmin):
    list_display = ('title', 'department')
    list_filter = ('department',)
    search_fields = ('title', 'content')