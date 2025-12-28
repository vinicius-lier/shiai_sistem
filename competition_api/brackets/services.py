import math
from collections import defaultdict

from django.db import transaction

from brackets.models import Bracket, BracketParticipant, BracketFormat
from brackets.belt_groups import (
    resolve_belt_group,
    allowed_groups_for_class,
    canonical_class_code,
)
from registrations.models import Registration, RegistrationStatus
from events.models import Event, EventStatus
from matches.models import Match, MatchStatus, WinMethod
from registrations.services import registration_is_eligible_to_fight


def list_eligible_registrations_for_brackets(event_id):
    return Registration.objects.filter(
        event_id=event_id,
        is_confirmed=True,
        disqualified=False,
        category_code_final__isnull=False,
    ).exclude(status=RegistrationStatus.BLOCKED).filter(
        status__in=[RegistrationStatus.WEIGHED, RegistrationStatus.APPROVED]
    ).exclude(class_code__isnull=True).exclude(sex__isnull=True).exclude(belt_snapshot__isnull=True)


def _pairwise(lst):
    it = iter(lst)
    return list(zip(it, it))


def _next_power_of_two(n):
    return 1 << (n - 1).bit_length()


def _create_single_elim_matches(bracket: Bracket, participants):
    # Seeds by order given
    slots = [p for p in participants]
    size = _next_power_of_two(len(slots))
    while len(slots) < size:
        slots.append(None)  # bye

    matches_created = []
    round_number = 1
    current = slots
    match_number = 1
    while len(current) > 1:
        next_round = []
        for a, b in _pairwise(current):
            blue = a.athlete_id if a else None
            white = b.athlete_id if b else None
            match = Match.objects.create(
                bracket=bracket,
                round_number=round_number,
                match_number=match_number,
                blue_athlete_id=blue,
                white_athlete_id=white,
                status=MatchStatus.SCHEDULED,
            )
            matches_created.append(match)
            next_round.append(match)
            match_number += 1
        current = next_round
        round_number += 1
        match_number = 1
    return matches_created


def _create_round_robin_matches(bracket: Bracket, participants):
    matches_created = []
    athletes = [p.athlete_id for p in participants]
    n = len(athletes)
    match_no = 1
    for i in range(n):
        for j in range(i + 1, n):
            match = Match.objects.create(
                bracket=bracket,
                round_number=1,
                match_number=match_no,
                blue_athlete_id=athletes[i],
                white_athlete_id=athletes[j],
                status=MatchStatus.SCHEDULED,
            )
            matches_created.append(match)
            match_no += 1
    return matches_created


def _create_best_of_3(bracket: Bracket, participants):
    matches_created = []
    athletes = [p.athlete_id for p in participants]
    if len(athletes) != 2:
        raise ValueError("Best of 3 requer exatamente 2 atletas")
    for num in range(1, 4):
        match = Match.objects.create(
            bracket=bracket,
            round_number=1,
            match_number=num,
            blue_athlete_id=athletes[0],
            white_athlete_id=athletes[1],
            status=MatchStatus.SCHEDULED,
        )
        matches_created.append(match)
    return matches_created


def _select_format(n, override=None):
    if override:
        return override
    if n == 1:
        return None  # sem matches
    if n == 2:
        return BracketFormat.BEST_OF_3
    if n in {3, 4, 5}:
        return BracketFormat.ROUND_ROBIN
    if n >= 6:
        return BracketFormat.ELIMINATION_WITH_REPECHAGE
    return None


def _ensure_allowed_group(reg: Registration):
    cls = canonical_class_code(reg.class_code)
    allowed = allowed_groups_for_class(cls)
    group = resolve_belt_group(cls, reg.sex, reg.belt_snapshot)
    if group is None or (allowed and group not in allowed):
        return None
    return group


def _next_power_of_two(n):
    return 1 << (n - 1).bit_length()


def _pairwise(lst):
    it = iter(lst)
    return list(zip(it, it))


def _build_main_bracket(participants):
    slots = [p for p in participants]
    size = _next_power_of_two(len(slots))
    while len(slots) < size:
        slots.append(None)

    matches = []
    round_number = 1
    current = slots
    match_number = 1
    while len(current) > 1:
        next_round = []
        for a, b in _pairwise(current):
            blue = a.athlete_id if a else None
            white = b.athlete_id if b else None
            match = {
                "round": round_number,
                "number": match_number,
                "blue": blue,
                "white": white,
                "phase": "MAIN",
            }
            matches.append(match)
            next_round.append(match)
            match_number += 1
        current = next_round
        round_number += 1
        match_number = 1
    return matches


def _create_elim_with_repechage(bracket: Bracket, participants):
    main_matches = _build_main_bracket(participants)
    # Persist main matches
    persisted = []
    for m in main_matches:
        obj = Match.objects.create(
            bracket=bracket,
            round_number=m["round"],
            match_number=m["number"],
            blue_athlete_id=m["blue"],
            white_athlete_id=m["white"],
            status=MatchStatus.SCHEDULED,
            phase="MAIN",
        )
        m["id"] = obj.id
        persisted.append(obj)

    # Determine finalist paths
    rounds = {}
    for m in main_matches:
        rounds.setdefault(m["round"], []).append(m)
    max_round = max(rounds.keys())
    final_match = [m for m in main_matches if m["round"] == max_round][0]

    # map winners to next
    def parent_id(round_no, match_no):
        return (round_no + 1, (match_no + 1) // 2)

    tree = {}
    for m in main_matches:
        tree[(m["round"], m["number"])] = m
    for m in main_matches:
        pr = parent_id(m["round"], m["number"])
        if pr in tree:
            pm = tree[pr]
            # mark source for clarity
            if m["number"] % 2 == 1:
                pm.setdefault("sources", {})["blue"] = tree[(m["round"], m["number"])]
            else:
                pm.setdefault("sources", {})["white"] = tree[(m["round"], m["number"])]

    # Collect losers to each finalist
    finalist_slots = {"top": [], "bottom": []}

    def collect_losers(m, slot):
        if "sources" not in m:
            return
        for side, child in m["sources"].items():
            # child is a dict; attach loser list when result arrives; for structure, we store match id
            finalist_slots[slot].append(child)
            collect_losers(child, slot)

    # assume top finalist from first half, bottom from second half
    # finals sources:
    if "sources" in final_match:
        if "blue" in final_match["sources"]:
            collect_losers(final_match["sources"]["blue"], "top")
        if "white" in final_match["sources"]:
            collect_losers(final_match["sources"]["white"], "bottom")

    # Helper to get match by round/number persisted id
    id_map = {(m["round"], m["number"]): m["id"] for m in main_matches}

    def losers_chain(chain):
        # chain is list of match dicts; losers are the athlete not winner (manual later). For structure, keep match ids.
        return [c for c in chain if c.get("id")]

    repechage_matches = []

    def build_repechage_side(chain, side_name):
        # chain is matches that lost to finalist; they enter repescagem
        # create linear elimination until one remains; then bronze vs semifinal loser of same side
        entries = losers_chain(chain)
        if len(entries) <= 0:
            return None, []
        # order by round descending (losers closer to final enter later)
        entries.sort(key=lambda cid: -tree[(final_match["round"], final_match["number"])]["round"] if False else 0)
        # simplistic: pair sequentially
        current = [e for e in entries]
        rep_round = 1
        match_no = 1
        created = []
        while len(current) > 1:
            next_level = []
            it = iter(current)
            for a in it:
                b = next(it, None)
                match = Match.objects.create(
                    bracket=bracket,
                    round_number=rep_round,
                    match_number=match_no,
                    status=MatchStatus.SCHEDULED,
                    phase="REPECHAGE",
                    source_blue_match_id=id_map.get(getattr(a, "key", (0, 0)), None),
                    source_white_match_id=id_map.get(getattr(b, "key", (0, 0)), None) if b else None,
                )
                created.append(match)
                next_level.append(match)
                match_no += 1
            current = next_level
            rep_round += 1
            match_no = 1
        final_rep = current[0] if current else None
        return final_rep, created

    bronze_matches = []

    def create_bronze(rep_winner, semifinal_match):
        return Match.objects.create(
            bracket=bracket,
            round_number=final_match["round"],  # align with final round
            match_number=0,
            status=MatchStatus.SCHEDULED,
            phase="BRONZE",
            source_blue_match_id=rep_winner.id if rep_winner else None,
            source_white_match_id=id_map.get((semifinal_match["round"], semifinal_match["number"]), None) if semifinal_match else None,
        )

    # Identify semifinals (round before final)
    semifinal_round = max_round - 1
    semifinals = [m for m in main_matches if m["round"] == semifinal_round]
    semi_top = semifinals[0] if semifinals else None
    semi_bottom = semifinals[1] if len(semifinals) > 1 else None

    rep_top_final, rep_top_created = build_repechage_side(finalist_slots["top"], "top")
    rep_bottom_final, rep_bottom_created = build_repechage_side(finalist_slots["bottom"], "bottom")

    if rep_top_final and semi_top:
        bronze_matches.append(create_bronze(rep_top_final, semi_top))
    if rep_bottom_final and semi_bottom:
        bronze_matches.append(create_bronze(rep_bottom_final, semi_bottom))

    return persisted + rep_top_created + rep_bottom_created + bronze_matches


@transaction.atomic
def generate_brackets_for_event(event_id, format_by_category=None):
    event = Event.objects.filter(id=event_id).first()
    if not event:
        raise ValueError("Evento não encontrado")
    if event.status != EventStatus.CLOSED:
        raise ValueError("Evento precisa estar CLOSED para gerar chaves")

    regs = list_eligible_registrations_for_brackets(event_id)
    grouped = defaultdict(list)
    for reg in regs:
        group_id = _ensure_allowed_group(reg)
        if group_id is None:
            continue
        cls = canonical_class_code(reg.class_code)
        grouped[(cls, reg.sex, reg.category_code_final, group_id)].append(reg)

    brackets = []
    for key, regs_cat in grouped.items():
        cls, sex, category_code, group_id = key
        n = len(regs_cat)
        fmt_override = None
        if format_by_category and category_code in format_by_category:
            fmt_override = format_by_category[category_code]
        fmt = _select_format(n, fmt_override)

        bracket, _ = Bracket.objects.get_or_create(
            event_id=event_id,
            category_code=category_code,
            class_code=cls,
            sex=sex,
            belt_group=group_id,
            defaults={"format": fmt or BracketFormat.SINGLE_ELIMINATION},
        )
        participants = []
        for idx, reg in enumerate(regs_cat, start=1):
            participant, _ = BracketParticipant.objects.get_or_create(
                bracket=bracket,
                athlete_id=reg.athlete_id,
                registration_id=reg.id,
                organization_id=reg.organization_id,
                defaults={"seed": idx},
            )
            participants.append(participant)

        if n == 1:
            bracket.is_generated = True
            bracket.save(update_fields=["is_generated"])
            brackets.append(bracket)
            continue

        if fmt == BracketFormat.BEST_OF_3:
            _create_best_of_3(bracket, participants)
        elif fmt == BracketFormat.ROUND_ROBIN:
            _create_round_robin_matches(bracket, participants)
        elif fmt == BracketFormat.ELIMINATION_WITH_REPECHAGE:
            _create_elim_with_repechage(bracket, participants)
        else:
            _create_single_elim_matches(bracket, participants)

        bracket.format = fmt or BracketFormat.SINGLE_ELIMINATION
        bracket.is_generated = True
        bracket.save(update_fields=["format", "is_generated"])
        brackets.append(bracket)

    return brackets


def compute_round_robin_standings(bracket: Bracket):
    if bracket.format != BracketFormat.ROUND_ROBIN:
        raise ValueError("Bracket não é round-robin")

    matches = bracket.matches.filter(status=MatchStatus.FINISHED)
    stats = {}

    def ensure(athlete_id):
        if athlete_id not in stats:
            stats[athlete_id] = {"wins": 0, "losses": 0, "fight_points": 0}

    for m in matches:
        if not m.winner_athlete_id:
            continue
        ensure(m.blue_athlete_id)
        ensure(m.white_athlete_id)

        winner = m.winner_athlete_id
        loser = m.white_athlete_id if winner == m.blue_athlete_id else m.blue_athlete_id

        stats[winner]["wins"] += 1
        stats[winner]["fight_points"] += m.fight_points_winner
        stats[loser]["losses"] += 1
        stats[loser]["fight_points"] += m.fight_points_loser

    # confronto direto helper
    def head_to_head(a, b):
        match = bracket.matches.filter(
            status=MatchStatus.FINISHED,
            winner_athlete_id__in=[a, b],
        ).filter(
            blue_athlete_id__in=[a, b],
            white_athlete_id__in=[a, b],
        ).first()
        if match and match.winner_athlete_id in (a, b):
            return match.winner_athlete_id
        return None

    athletes = list(stats.keys())

    def sort_key(a):
        return (-stats[a]["wins"], -stats[a]["fight_points"], a)

    athletes.sort(key=sort_key)

    i = 0
    while i < len(athletes) - 1:
        a, b = athletes[i], athletes[i + 1]
        if (
            stats[a]["wins"] == stats[b]["wins"]
            and stats[a]["fight_points"] == stats[b]["fight_points"]
        ):
            winner = head_to_head(a, b)
            if winner and winner != a:
                athletes[i], athletes[i + 1] = athletes[i + 1], athletes[i]
        i += 1

    ordered = []
    for athlete_id in athletes:
        ordered.append(
            {
                "athlete_id": athlete_id,
                "wins": stats[athlete_id]["wins"],
                "losses": stats[athlete_id]["losses"],
                "fight_points": stats[athlete_id]["fight_points"],
            }
        )
    return ordered

