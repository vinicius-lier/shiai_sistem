import uuid

from django.db import models


class TeamScore(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField()
    organization_id = models.UUIDField()
    points_total = models.PositiveIntegerField()

    def __str__(self) -> str:
        return f"{self.organization_id} - {self.points_total} pts"

# Create your models here.
