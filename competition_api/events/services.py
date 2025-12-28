from events.models import Event, EventStatus


def open_event(event: Event) -> Event:
    if event.status != EventStatus.DRAFT:
        raise ValueError("Evento só pode ser aberto a partir do status DRAFT")
    event.status = EventStatus.OPEN
    event.save(update_fields=["status"])
    return event

