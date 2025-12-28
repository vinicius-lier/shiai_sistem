from athletes.models import Athlete


def list_active_athletes(organization):
    return Athlete.objects.filter(organization=organization, is_active=True)


def get_athlete_by_id(athlete_id, organization) -> Athlete:
    try:
        return Athlete.objects.get(id=athlete_id, organization=organization)
    except Athlete.DoesNotExist as exc:
        raise ValueError("Atleta não encontrado para esta organização") from exc

