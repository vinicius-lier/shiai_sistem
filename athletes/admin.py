from django.contrib import admin

from .models import Athlete


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "sex", "belt", "is_active", "created_at")
    list_filter = ("sex", "belt", "is_active", "organization")
    search_fields = ("name",)

