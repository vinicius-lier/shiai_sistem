import uuid

from django.db import models


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField()
    athlete_id = models.UUIDField()
    organization_id = models.UUIDField()
    placement = models.PositiveSmallIntegerField()
    points = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.event_id} - {self.athlete_id} ({self.points} pts)"

# Create your models here.
