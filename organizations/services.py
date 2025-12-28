from organizations.models import Organization


def get_organization_by_slug(slug: str) -> Organization:
    try:
        return Organization.objects.get(slug=slug, is_active=True)
    except Organization.DoesNotExist as exc:
        raise ValueError("Organização não encontrada ou inativa") from exc


def get_active_organization(org_id) -> Organization:
    try:
        return Organization.objects.get(id=org_id, is_active=True)
    except Organization.DoesNotExist as exc:
        raise ValueError("Organização não encontrada ou inativa") from exc

