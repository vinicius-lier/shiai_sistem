from typing import Protocol


class CompetitionReadContract(Protocol):
    def list_event_results(self, event_id) -> list[dict]: ...

    def event_is_closed(self, event_id) -> bool: ...

    def list_official_results(self, event_id) -> list[dict]: ...

