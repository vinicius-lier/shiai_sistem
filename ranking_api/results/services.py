import logging

from results.models import Result
from contracts.competition_read_contract import CompetitionReadContract
from adapters.competition_reader import CompetitionSQLReader
from adapters.exceptions import CompetitionUnavailableError
from teams.services import add_points_to_team


def _ensure_points(points):
    if points is None:
        raise ValueError("points não pode ser nulo")
    if isinstance(points, bool) or not isinstance(points, int):
        raise ValueError("points deve ser int")
    if points < 0:
        raise ValueError("points deve ser >= 0")


def register_result(event_id, athlete_id, organization_id, placement, points):
    _ensure_points(points)
    if Result.objects.filter(event_id=event_id, athlete_id=athlete_id).exists():
        raise ValueError("Já existe resultado para este atleta neste evento")
    result = Result.objects.create(
        event_id=event_id,
        athlete_id=athlete_id,
        organization_id=organization_id,
        placement=placement,
        points=points,
    )
    return result


def upsert_result(event_id, athlete_id, organization_id, placement, points):
    _ensure_points(points)
    result, created = Result.objects.get_or_create(
        event_id=event_id,
        athlete_id=athlete_id,
        defaults={
            "organization_id": organization_id,
            "placement": placement,
            "points": points,
        },
    )
    if not created:
        result.organization_id = organization_id
        result.placement = placement
        result.points = points
        result.save(update_fields=["organization_id", "placement", "points"])
    return result


def get_results_by_event(event_id):
    return Result.objects.filter(event_id=event_id)


def get_results_by_organization(event_id, organization_id):
    return Result.objects.filter(event_id=event_id, organization_id=organization_id)


def import_results_from_competition(event_id, reader: CompetitionReadContract | None = None):
    reader = reader or CompetitionSQLReader()

    try:
        if not reader.event_is_closed(event_id):
            raise ValueError("Evento não está fechado na Competition")
        external_results = reader.list_official_results(event_id)
    except CompetitionUnavailableError as exc:
        logging.getLogger(__name__).warning("Competition indisponível ao importar resultados oficiais", exc_info=exc)
        raise

    imported = []
    for res in external_results:
        points_value = res.get("points", 0) or 0
        result = upsert_result(
            res["event_id"],
            res["athlete_id"],
            res["organization_id"],
            res["placement"],
            points_value,
        )
        add_points_to_team(res["event_id"], res["organization_id"], points_value)
        imported.append(result)

    return imported

