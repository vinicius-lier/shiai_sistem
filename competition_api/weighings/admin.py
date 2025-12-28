from django.contrib import admin

from .models import Weighing


@admin.register(Weighing)
class WeighingAdmin(admin.ModelAdmin):
    list_display = ("registration_id", "weight", "measured_at")
    search_fields = ("registration_id",)
    readonly_fields = ("registration_id", "weight", "measured_at")
