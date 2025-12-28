from teams.models import TeamScore


def _ensure_int(value, field_name: str):
    if value is None:
        raise ValueError(f"{field_name} não pode ser nulo")
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} deve ser int")


def add_points_to_team(event_id, organization_id, points_delta):
    _ensure_int(points_delta, "points_delta")

    team_score = TeamScore.objects.filter(
        event_id=event_id,
        organization_id=organization_id,
    ).first()

    if team_score is None:
        team_score = TeamScore.objects.create(
            event_id=event_id,
            organization_id=organization_id,
            points_total=points_delta,
        )
    else:
        team_score.points_total += points_delta
        team_score.save(update_fields=["points_total"])

    return team_score


def set_team_score(event_id, organization_id, points_total):
    _ensure_int(points_total, "points_total")

    team_score, _ = TeamScore.objects.get_or_create(
        event_id=event_id,
        organization_id=organization_id,
        defaults={"points_total": points_total},
    )
    if team_score.points_total != points_total:
        team_score.points_total = points_total
        team_score.save(update_fields=["points_total"])
    return team_score


def get_team_score(event_id, organization_id):
    return TeamScore.objects.filter(
        event_id=event_id,
        organization_id=organization_id,
    ).first()

