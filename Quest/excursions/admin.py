# excursions/admin.py
from django.contrib import admin
from .models import Route, Panorama, ReferenceInfo #, Sessions, Answer
admin.site.register(Route)
admin.site.register(Panorama)
admin.site.register(ReferenceInfo)
# admin.site.register(Sessions) # если добавили
# admin.site.register(Answer) # если добавили