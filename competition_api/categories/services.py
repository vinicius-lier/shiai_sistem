from categories.models import CategoryRule


def get_rule_by_code(sex, class_code, category_code):
    return CategoryRule.objects.filter(
        sex=sex,
        class_code=class_code,
        category_code=category_code,
        is_active=True,
    ).first()


def find_rule_for_weight(sex, class_code, weight):
    return CategoryRule.objects.filter(
        sex=sex,
        class_code=class_code,
        is_active=True,
        min_weight__lte=weight,
        max_weight__gte=weight,
    ).first()

