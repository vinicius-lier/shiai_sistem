from typing import Protocol
from uuid import UUID


class CoreReadContract(Protocol):
    def organization_exists_and_active(self, org_id: UUID) -> bool: ...

    def athlete_belongs_to_org(self, athlete_id: UUID, org_id: UUID) -> bool: ...

    def get_athlete_profile(self, athlete_id: UUID) -> dict: ...

