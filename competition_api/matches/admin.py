from django.contrib import admin

from .models import Match, MatchStatus


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "bracket",
        "round_number",
        "match_number",
        "status",
        "winner_athlete_id",
        "win_method",
        "fight_points_winner",
        "finished_at",
    )
    list_filter = ("status", "round_number")
    search_fields = ("bracket__id", "round_number", "match_number")

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ()
        if obj.status != MatchStatus.SCHEDULED:
            return (
                "bracket",
                "round_number",
                "match_number",
                "blue_athlete_id",
                "white_athlete_id",
                "status",
                "winner_athlete_id",
                "win_method",
                "fight_points_winner",
                "fight_points_loser",
                "finished_at",
                "finished_by_user_id",
                "notes",
            )
        return ()
