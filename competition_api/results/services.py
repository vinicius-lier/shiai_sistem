from collections import defaultdict

from django.db import transaction

from results.models import OfficialResult
from events.models import Event, EventStatus
from brackets.models import Bracket, BracketFormat
from matches.models import MatchStatus
from brackets.services import compute_round_robin_standings


def _all_matches_completed(bracket: Bracket) -> bool:
    return not bracket.matches.filter(status=MatchStatus.SCHEDULED).exists()


def _fight_points_totals(bracket: Bracket):
    totals = defaultdict(int)
    for m in bracket.matches.filter(status=MatchStatus.FINISHED):
        if m.winner_athlete_id:
            totals[m.winner_athlete_id] += m.fight_points_winner
        loser = None
        if m.winner_athlete_id and m.blue_athlete_id and m.white_athlete_id:
            loser = m.white_athlete_id if m.winner_athlete_id == m.blue_athlete_id else m.blue_athlete_id
        if loser:
            totals[loser] += m.fight_points_loser
    return totals


@transaction.atomic
def generate_official_results_for_event(event_id):
    event = Event.objects.filter(id=event_id).first()
    if not event:
        raise ValueError("Evento não encontrado")
    if event.status != EventStatus.CLOSED:
        raise ValueError("Evento precisa estar CLOSED para gerar resultados oficiais")

    brackets = Bracket.objects.filter(event_id=event_id, is_generated=True)
    for b in brackets:
        if not _all_matches_completed(b):
            raise ValueError("Existem lutas pendentes neste evento; finalize antes de gerar resultados oficiais")

    OfficialResult.objects.filter(event_id=event_id).delete()
    created = 0

    for bracket in brackets:
        fp_totals = _fight_points_totals(bracket)
        if bracket.format == BracketFormat.ROUND_ROBIN:
            standings = compute_round_robin_standings(bracket)
            placement = 1
            for row in standings:
                OfficialResult.objects.create(
                    event_id=event_id,
                    category_code=bracket.category_code,
                    athlete_id=row["athlete_id"],
                    organization_id=None,
                    placement=placement,
                    fight_points_total=fp_totals.get(row["athlete_id"], row["fight_points"]),
                )
                placement += 1
                created += 1
        else:
            # single elim simplificado: final + semis
            matches = list(bracket.matches.filter(status__in=[MatchStatus.FINISHED, MatchStatus.WALKOVER]))
            if not matches:
                continue
            final = max(matches, key=lambda m: (m.round_number, -m.match_number))
            if not final.winner_athlete_id:
                continue
            winner = final.winner_athlete_id
            loser = final.blue_athlete_id if final.winner_athlete_id == final.white_athlete_id else final.white_athlete_id

            OfficialResult.objects.create(
                event_id=event_id,
                category_code=bracket.category_code,
                athlete_id=winner,
                organization_id=None,
                placement=1,
                fight_points_total=fp_totals.get(winner, 0),
            )
            created += 1
            if loser:
                OfficialResult.objects.create(
                    event_id=event_id,
                    category_code=bracket.category_code,
                    athlete_id=loser,
                    organization_id=None,
                    placement=2,
                    fight_points_total=fp_totals.get(loser, 0),
                )
                created += 1

            # semis losers -> 3/4 estável por athlete_id
            semis = [m for m in matches if m.round_number == final.round_number - 1]
            semi_losers = []
            for m in semis:
                if not m.winner_athlete_id:
                    continue
                if m.blue_athlete_id and m.white_athlete_id:
                    loser_id = m.white_athlete_id if m.winner_athlete_id == m.blue_athlete_id else m.blue_athlete_id
                    semi_losers.append(loser_id)
            for idx, athlete_id in enumerate(sorted(semi_losers), start=3):
                OfficialResult.objects.create(
                    event_id=event_id,
                    category_code=bracket.category_code,
                    athlete_id=athlete_id,
                    organization_id=None,
                    placement=idx,
                    fight_points_total=fp_totals.get(athlete_id, 0),
                )
                created += 1

    return created

