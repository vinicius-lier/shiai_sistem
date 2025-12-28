from django.contrib import admin

from .models import Registration, RegistrationStatus


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "event_id",
        "athlete_id",
        "organization_id",
        "status",
        "is_confirmed",
        "was_rematched",
        "disqualified",
        "created_at",
    )
    list_filter = ("status", "is_confirmed", "was_rematched", "disqualified")
    search_fields = ("event_id", "athlete_id", "organization_id", "category_code_requested", "category_code_final")

    def get_readonly_fields(self, request, obj=None):
        base_readonly = ("event_id", "athlete_id", "organization_id", "created_at")
        if not obj:
            return base_readonly
        if obj.status != RegistrationStatus.PENDING:
            return base_readonly + (
                "status",
                "is_confirmed",
                "confirmed_at",
                "confirmed_by_user_id",
                "requested_by_user_id",
                "category_code_requested",
                "category_code_final",
                "was_rematched",
                "event_penalty_points",
                "disqualified",
                "disqualified_reason",
            )
        return base_readonly
