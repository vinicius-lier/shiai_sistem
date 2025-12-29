import logging
from django.utils import timezone

from registrations.models import Registration, RegistrationStatus
from events.models import Event, EventStatus
from contracts.core_read_contract import CoreReadContract
from adapters.core_reader import CoreSQLReader
from adapters.exceptions import CoreUnavailableError
from brackets.belt_groups import canonical_class_code


def _validate_event_open(event: Event):
    if event.status != EventStatus.OPEN:
        raise ValueError("Não é possível operar inscrição em evento que não está OPEN")


def _validate_core(reader, athlete_id, organization_id):
    try:
        if not reader.organization_exists_and_active(organization_id):
            raise ValueError("Organização inexistente ou inativa")
        if not reader.athlete_belongs_to_org(athlete_id, organization_id):
            raise ValueError("Atleta inexistente, inativo ou fora da organização")
    except CoreUnavailableError as exc:
        logging.getLogger(__name__).warning("Falha ao consultar Core", exc_info=exc)
        raise


def request_registration(
    event: Event,
    athlete_id,
    organization_id,
    class_code,
    requested_by_user_id,
    category_code_requested=None,
    core_reader: CoreReadContract | None = None,
) -> Registration:
    _validate_event_open(event)
    reader = core_reader or CoreSQLReader()
    _validate_core(reader, athlete_id, organization_id)
    profile = reader.get_athlete_profile(athlete_id)
    class_code_canon = canonical_class_code(class_code)
    if not class_code_canon:
        raise ValueError("class_code inválido ou ausente")

    return Registration.objects.create(
        event_id=event.id,
        athlete_id=athlete_id,
        organization_id=organization_id,
        class_code=class_code_canon,
        sex=profile["sex"],
        belt_snapshot=profile["belt"],
        status=RegistrationStatus.PENDING,
        is_confirmed=False,
        requested_by_user_id=requested_by_user_id,
        category_code_requested=category_code_requested,
    )


def register_athlete_operational(
    event: Event,
    athlete_id,
    organization_id,
    class_code,
    requested_by_user_id,
    category_code_requested,
    confirmed_by_user_id,
    core_reader: CoreReadContract | None = None,
) -> Registration:
    _validate_event_open(event)
    reader = core_reader or CoreSQLReader()
    _validate_core(reader, athlete_id, organization_id)
    profile = reader.get_athlete_profile(athlete_id)
    class_code_canon = canonical_class_code(class_code)
    if not class_code_canon:
        raise ValueError("class_code inválido ou ausente")

    return Registration.objects.create(
        event_id=event.id,
        athlete_id=athlete_id,
        organization_id=organization_id,
        class_code=class_code_canon,
        sex=profile["sex"],
        belt_snapshot=profile["belt"],
        status=RegistrationStatus.PENDING,
        is_confirmed=True,
        confirmed_at=timezone.now(),
        confirmed_by_user_id=confirmed_by_user_id,
        requested_by_user_id=requested_by_user_id,
        category_code_requested=category_code_requested,
    )


def confirm_registration(registration: Registration, confirmed_by_user_id):
    if registration.is_confirmed:
        raise ValueError("Inscrição já confirmada")
    class_code_canon = canonical_class_code(registration.class_code)
    if not class_code_canon:
        raise ValueError("class_code ausente na inscrição")

    # backfill sexo/faixa se legado sem snapshot
    if not registration.sex or not registration.belt_snapshot:
        reader = CoreSQLReader()
        profile = reader.get_athlete_profile(registration.athlete_id)
        registration.sex = profile["sex"]
        registration.belt_snapshot = profile["belt"]
    registration.class_code = class_code_canon
    registration.is_confirmed = True
    registration.confirmed_at = timezone.now()
    registration.confirmed_by_user_id = confirmed_by_user_id
    registration.save(update_fields=["is_confirmed", "confirmed_at", "confirmed_by_user_id"])
    return registration


def register_athlete(
    event: Event,
    athlete_id,
    organization_id,
    class_code,
    core_reader: CoreReadContract | None = None,
) -> Registration:
    return register_athlete_operational(
        event=event,
        athlete_id=athlete_id,
        organization_id=organization_id,
        class_code=class_code,
        requested_by_user_id=None,
        category_code_requested=None,
        confirmed_by_user_id=None,
        core_reader=core_reader,
    )


def registration_is_eligible_to_fight(registration: Registration) -> bool:
    return (
        registration.is_confirmed
        and registration.status in {RegistrationStatus.APPROVED, RegistrationStatus.WEIGHED}
        and not registration.disqualified
        and registration.status != RegistrationStatus.BLOCKED
    )


def approve_registration(registration: Registration) -> Registration:
    if registration.status != RegistrationStatus.WEIGHED:
        raise ValueError("Só é possível aprovar inscrições no status WEIGHED")
    registration.status = RegistrationStatus.APPROVED
    registration.save(update_fields=["status"])
    return registration


def block_registration(registration: Registration) -> Registration:
    registration.status = RegistrationStatus.BLOCKED
    registration.save(update_fields=["status"])
    return registration

