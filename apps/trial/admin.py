from django.contrib import admin

from . import models


admin.site.register(models.Questionnaire)
admin.site.register(models.Trial)
admin.site.register(models.TrialItem)
admin.site.register(models.Rating)
