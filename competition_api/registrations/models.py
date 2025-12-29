import uuid

from django.db import models


class RegistrationStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    WEIGHED = "WEIGHED", "Weighed"
    APPROVED = "APPROVED", "Approved"
    BLOCKED = "BLOCKED", "Blocked"


class Registration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.UUIDField()
    athlete_id = models.UUIDField()
    organization_id = models.UUIDField()
    class_code = models.CharField(max_length=20, null=True, blank=True)
    sex = models.CharField(max_length=1, choices=[('M', 'M'), ('F', 'F')], null=True, blank=True)
    belt_snapshot = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=RegistrationStatus.choices, default=RegistrationStatus.PENDING
    )
    is_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    confirmed_by_user_id = models.UUIDField(null=True, blank=True)
    requested_by_user_id = models.UUIDField(null=True, blank=True)
    category_code_requested = models.CharField(max_length=50, null=True, blank=True)
    category_code_final = models.CharField(max_length=50, null=True, blank=True)
    was_rematched = models.BooleanField(default=False)
    event_penalty_points = models.IntegerField(default=0)
    disqualified = models.BooleanField(default=False)
    disqualified_reason = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.event_id} - {self.athlete_id}"
