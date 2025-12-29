import uuid

from django.db import models


class Weighing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_id = models.UUIDField()
    weight = models.DecimalField(max_digits=7, decimal_places=2)
    measured_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.registration_id} - {self.weight}"

# Create your models here.
