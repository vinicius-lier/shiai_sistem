from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ("email", "organization", "role", "is_active", "is_staff", "created_at")
    list_filter = ("role", "is_active", "is_staff", "organization")
    search_fields = ("email",)
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("email", "password", "organization", "role")}),
        ("Permissões", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Datas", {"fields": ("last_login", "created_at")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "organization", "role", "password1", "password2", "is_active", "is_staff"),
        }),
    )

    readonly_fields = ("created_at",)

    filter_horizontal = ("groups", "user_permissions")

