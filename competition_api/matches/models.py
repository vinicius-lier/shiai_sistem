import uuid

from django.db import models
from brackets.models import Bracket


class MatchStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    FINISHED = "FINISHED", "Finished"
    WALKOVER = "WALKOVER", "Walkover"


class WinMethod(models.TextChoices):
    IPPON = "IPPON", "Ippon"
    WAZA_ARI = "WAZA_ARI", "Waza-ari"
    YUKO = "YUKO", "Yuko"
    HANSOKUMAKE = "HANSOKUMAKE", "Hansokumake"
    WO = "WO", "Walk Over"


class Match(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bracket = models.ForeignKey(Bracket, on_delete=models.CASCADE, related_name="matches", null=True, blank=True)
    round_number = models.PositiveSmallIntegerField(default=1)
    match_number = models.PositiveSmallIntegerField(default=1)
    phase = models.CharField(
        max_length=20,
        choices=[
            ("MAIN", "Main"),
            ("REPECHAGE", "Repechage"),
            ("BRONZE", "Bronze"),
            ("FINAL", "Final"),
        ],
        default="MAIN",
    )
    source_blue_match_id = models.UUIDField(null=True, blank=True)
    source_white_match_id = models.UUIDField(null=True, blank=True)
    blue_athlete_id = models.UUIDField(null=True, blank=True)
    white_athlete_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=MatchStatus.choices, default=MatchStatus.SCHEDULED)
    winner_athlete_id = models.UUIDField(null=True, blank=True)
    win_method = models.CharField(max_length=20, choices=WinMethod.choices, null=True, blank=True)
    fight_points_winner = models.IntegerField(default=0)
    fight_points_loser = models.IntegerField(default=0)
    finished_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    finished_by_user_id = models.UUIDField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["bracket"]),
            models.Index(fields=["bracket", "round_number", "match_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.bracket_id} R{self.round_number} M{self.match_number}"
