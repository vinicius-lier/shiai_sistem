from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "status", "start_date", "end_date", "organization_id", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "organization_id")
