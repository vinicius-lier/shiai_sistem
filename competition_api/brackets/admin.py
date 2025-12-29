from django.contrib import admin

from .models import Bracket, BracketParticipant


@admin.register(Bracket)
class BracketAdmin(admin.ModelAdmin):
    list_display = ("event_id", "category_code", "format", "is_generated", "created_at")
    list_filter = ("format", "is_generated")
    search_fields = ("event_id", "category_code")


@admin.register(BracketParticipant)
class BracketParticipantAdmin(admin.ModelAdmin):
    list_display = ("bracket", "athlete_id", "organization_id", "seed", "created_at")
    search_fields = ("bracket__id", "athlete_id", "organization_id")

