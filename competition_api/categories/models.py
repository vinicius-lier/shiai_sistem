import uuid

from django.db import models


class SexChoices(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMININO = "F", "Feminino"


class CategoryRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sex = models.CharField(max_length=1, choices=SexChoices.choices)
    class_code = models.CharField(max_length=50)
    category_code = models.CharField(max_length=50)
    min_weight = models.DecimalField(max_digits=5, decimal_places=2)
    max_weight = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("sex", "class_code", "category_code")

    def __str__(self) -> str:
        return f"{self.class_code} - {self.category_code} ({self.sex})"
