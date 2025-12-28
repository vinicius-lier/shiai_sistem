import uuid

from django.db import models


class BracketFormat(models.TextChoices):
    SINGLE_ELIMINATION = "SINGLE_ELIMINATION", "Single Elimination"
    ROUND_ROBIN = "ROUND_ROBIN", "Round Robin"
    BEST_OF_3 = "BEST_OF_3", "Best of 3"
    ELIMINATION_WITH_REPECHAGE = "ELIMINATION_WITH_REPECHAGE", "Elimination with Repechage"


class Bracket(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField()
    category_code = models.CharField(max_length=50)
    class_code = models.CharField(max_length=20, null=True, blank=True)
    sex = models.CharField(max_length=1, choices=[("M", "M"), ("F", "F")], null=True, blank=True)
    belt_group = models.PositiveSmallIntegerField(null=True, blank=True)
    format = models.CharField(max_length=30, choices=BracketFormat.choices)
    is_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event_id", "category_code", "class_code", "sex", "belt_group")
        indexes = [
            models.Index(fields=["event_id", "category_code", "class_code", "sex", "belt_group"]),
            models.Index(fields=["event_id", "category_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_id} - {self.category_code} ({self.format})"


class BracketParticipant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name="participants")
    registration_id = models.UUIDField()
    athlete_id = models.UUIDField()
    organization_id = models.UUIDField()
    seed = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("bracket", "athlete_id")

    def __str__(self) -> str:
        return f"{self.bracket_id} - {self.athlete_id}"

