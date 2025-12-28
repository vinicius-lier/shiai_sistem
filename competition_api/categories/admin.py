from django.contrib import admin

from .models import CategoryRule


@admin.register(CategoryRule)
class CategoryRuleAdmin(admin.ModelAdmin):
    list_display = ("sex", "class_code", "category_code", "min_weight", "max_weight", "is_active")
    list_filter = ("sex", "class_code", "is_active")
    search_fields = ("class_code", "category_code")
