from organizations.models import Organization
from athletes.models import Athlete


def get_active_organization(org_id):
    try:
        return Organization.objects.get(id=org_id, is_active=True)
    except Organization.DoesNotExist as exc:
        raise ValueError("Organização inexistente ou inativa") from exc


def get_active_athlete(athlete_id, org_id):
    try:
        return Athlete.objects.get(id=athlete_id, organization_id=org_id, is_active=True)
    except Athlete.DoesNotExist as exc:
        raise ValueError("Atleta inexistente, inativo ou fora da organização") from exc

