import uuid

from django.db import models


class OfficialResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField()
    category_code = models.CharField(max_length=50)
    athlete_id = models.UUIDField()
    organization_id = models.UUIDField()
    placement = models.PositiveIntegerField()
    fight_points_total = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event_id", "category_code", "athlete_id")

    def __str__(self):
        return f"{self.event_id} - {self.category_code} - {self.athlete_id} ({self.placement})"

