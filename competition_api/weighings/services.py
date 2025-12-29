from enum import Enum

from django.utils import timezone

from registrations.models import Registration, RegistrationStatus
from events.models import Event, EventStatus
from weighings.models import Weighing
from categories.services import get_rule_by_code, find_rule_for_weight


class OutOfRangeDecision(Enum):
    REMATCH = "REMATCH"
    DISQUALIFY = "DISQUALIFY"


def record_weighing(registration: Registration, weight) -> Weighing:
    raise ValueError("Use record_weighing_with_rules para registrar pesagem")


def record_weighing_with_rules(
    registration: Registration,
    weight,
    sex,
    class_code,
    decision_if_out_of_range: OutOfRangeDecision,
):
    if registration.disqualified:
        raise ValueError("Inscrição desclassificada não pode registrar pesagem")
    if registration.status == RegistrationStatus.BLOCKED:
        raise ValueError("Não é possível registrar peso para inscrição BLOQUEADA")
    if registration.status != RegistrationStatus.PENDING:
        raise ValueError("Somente inscrições no status PENDING podem registrar pesagem")
    if not registration.is_confirmed:
        raise ValueError("Inscrição precisa estar confirmada antes da pesagem")

    event = Event.objects.filter(id=registration.event_id).first()
    if not event or event.status != EventStatus.OPEN:
        raise ValueError("Evento não está aberto para pesagem")

    if not registration.category_code_requested:
        raise ValueError("Categoria solicitada não definida na inscrição")

    requested_rule = get_rule_by_code(
        sex=sex,
        class_code=class_code,
        category_code=registration.category_code_requested,
    )
    if not requested_rule:
        raise ValueError("Regra de categoria solicitada não encontrada ou inativa")

    within_range = requested_rule.min_weight <= weight <= requested_rule.max_weight

    if within_range:
        weighing = Weighing.objects.create(
            registration_id=registration.id,
            weight=weight,
            measured_at=timezone.now(),
        )
        registration.category_code_final = registration.category_code_requested
        registration.status = RegistrationStatus.WEIGHED
        registration.save(update_fields=["category_code_final", "status"])
        return weighing

    if decision_if_out_of_range == OutOfRangeDecision.REMATCH:
        new_rule = find_rule_for_weight(sex=sex, class_code=class_code, weight=weight)
        if not new_rule:
            raise ValueError("Peso fora de faixa e sem regra compatível para remanejamento")
        weighing = Weighing.objects.create(
            registration_id=registration.id,
            weight=weight,
            measured_at=timezone.now(),
        )
        registration.category_code_final = new_rule.category_code
        registration.was_rematched = True
        registration.event_penalty_points = -1
        registration.status = RegistrationStatus.WEIGHED
        registration.save(
            update_fields=[
                "category_code_final",
                "was_rematched",
                "event_penalty_points",
                "status",
            ]
        )
        return weighing

    if decision_if_out_of_range == OutOfRangeDecision.DISQUALIFY:
        registration.disqualified = True
        registration.disqualified_reason = "WEIGHT_OUT_OF_RANGE"
        registration.status = RegistrationStatus.BLOCKED
        registration.save(update_fields=["disqualified", "disqualified_reason", "status"])
        return None

    raise ValueError("Decisão inválida para peso fora da faixa")

