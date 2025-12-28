from django.utils import timezone

from matches.models import Match, MatchStatus, WinMethod
from brackets.models import BracketFormat


def fight_points(win_method: WinMethod) -> int:
    return {
        WinMethod.IPPON: 10,
        WinMethod.WAZA_ARI: 7,
        WinMethod.YUKO: 5,
        WinMethod.HANSOKUMAKE: 3,
        WinMethod.WO: 1,
    }.get(win_method, 0)


def record_match_result(
    match: Match,
    winner_athlete_id,
    win_method: WinMethod,
    finished_by_user_id=None,
    notes="",
):
    if match.status != MatchStatus.SCHEDULED:
        raise ValueError("Resultado só pode ser registrado para lutas agendadas")
    if not winner_athlete_id:
        raise ValueError("Vencedor é obrigatório")
    if not win_method:
        raise ValueError("Método de vitória é obrigatório")
    if winner_athlete_id not in [match.blue_athlete_id, match.white_athlete_id]:
        raise ValueError("Vencedor não pertence à luta")

    match.winner_athlete_id = winner_athlete_id
    match.win_method = win_method
    match.fight_points_winner = fight_points(win_method)
    match.fight_points_loser = 0
    match.finished_at = timezone.now()
    match.finished_by_user_id = finished_by_user_id
    match.status = MatchStatus.WALKOVER if win_method == WinMethod.WO else MatchStatus.FINISHED
    match.notes = notes or ""
    match.save(
        update_fields=[
            "winner_athlete_id",
            "win_method",
            "fight_points_winner",
            "fight_points_loser",
            "finished_at",
            "finished_by_user_id",
            "status",
            "notes",
        ]
    )
    return match


def advance_single_elimination(bracket, finished_match: Match):
    if bracket.format != BracketFormat.SINGLE_ELIMINATION:
        raise ValueError("Bracket não é single-elimination")
    # final reached
    last_round = bracket.matches.filter(round_number__gt=finished_match.round_number).exists()
    if not last_round:
        return None
    parent_match_number = (finished_match.match_number + 1) // 2
    parent_round = finished_match.round_number + 1
    parent = bracket.matches.filter(
        round_number=parent_round, match_number=parent_match_number
    ).first()
    if not parent:
        return None
    slot_field = "blue_athlete_id" if finished_match.match_number % 2 == 1 else "white_athlete_id"
    setattr(parent, slot_field, finished_match.winner_athlete_id)
    parent.save(update_fields=[slot_field])
    return parent


def void_match(match: Match, reason, finished_by_user_id=None):
    match.status = MatchStatus.WALKOVER
    match.finished_at = timezone.now()
    match.finished_by_user_id = finished_by_user_id
    match.notes = reason or ""
    match.save(update_fields=["status", "finished_at", "finished_by_user_id", "notes"])
    return match

