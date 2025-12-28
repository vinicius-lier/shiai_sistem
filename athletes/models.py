import uuid

from django.db import models

from organizations.models import Organization
from .constants import BeltChoices


class Athlete(models.Model):
    class Sex(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMININO = "F", "Feminino"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="athletes"
    )
    name = models.CharField(max_length=255)
    birth_date = models.DateField()
    sex = models.CharField(max_length=1, choices=Sex.choices)
    belt = models.CharField(max_length=20, choices=BeltChoices.choices)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

