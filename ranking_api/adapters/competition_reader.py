from uuid import UUID
import logging

from django.db import connection
from django.db.utils import OperationalError, DatabaseError

from adapters.exceptions import CompetitionUnavailableError
from contracts.competition_read_contract import CompetitionReadContract

logger = logging.getLogger(__name__)


class CompetitionSQLReader:
    statement_timeout_ms = 2000  # fail fast

    def _set_statement_timeout(self, cursor):
        cursor.execute(f"SET LOCAL statement_timeout = {self.statement_timeout_ms}")

    def event_is_closed(self, event_id: UUID) -> bool:
        query = """
            SELECT 1
            FROM competition.events_event
            WHERE id = %s AND status = 'CLOSED'
            LIMIT 1
        """
        try:
            with connection.cursor() as cursor:
                self._set_statement_timeout(cursor)
                cursor.execute(query, [event_id])
                return cursor.fetchone() is not None
        except (OperationalError, DatabaseError) as exc:
            logger.warning("Competition indisponível ao validar evento", exc_info=exc)
            raise CompetitionUnavailableError("Competition indisponível") from exc

    def list_event_results(self, event_id: UUID) -> list[dict]:
        # Garante que só retornará dados se o evento estiver CLOSED
        if not self.event_is_closed(event_id):
            return []

        query = """
            SELECT
                event_id,
                athlete_id,
                organization_id,
                0 AS placement,
                0 AS points
            FROM competition.registrations_registration
            WHERE event_id = %s
              AND status = 'APPROVED'
        """
        try:
            with connection.cursor() as cursor:
                self._set_statement_timeout(cursor)
                cursor.execute(query, [event_id])
                rows = cursor.fetchall()
        except (OperationalError, DatabaseError) as exc:
            logger.warning("Competition indisponível ao listar resultados", exc_info=exc)
            raise CompetitionUnavailableError("Competition indisponível") from exc

        results = []
        for row in rows:
            results.append(
                {
                    "event_id": row[0],
                    "athlete_id": row[1],
                    "organization_id": row[2],
                    "placement": row[3],
                    "points": row[4],
                }
            )
        return results

    def list_official_results(self, event_id: UUID) -> list[dict]:
        if not self.event_is_closed(event_id):
            return []
        query = """
            SELECT event_id, category_code, athlete_id, organization_id, placement, fight_points_total
            FROM competition.results_officialresult
            WHERE event_id = %s
            ORDER BY category_code, placement
        """
        try:
            with connection.cursor() as cursor:
                self._set_statement_timeout(cursor)
                cursor.execute(query, [event_id])
                rows = cursor.fetchall()
        except (OperationalError, DatabaseError) as exc:
            logger.warning("Competition indisponível ao listar resultados oficiais", exc_info=exc)
            raise CompetitionUnavailableError("Competition indisponível") from exc

        results = []
        for row in rows:
            results.append(
                {
                    "event_id": row[0],
                    "category_code": row[1],
                    "athlete_id": row[2],
                    "organization_id": row[3],
                    "placement": row[4],
                    "points": row[5],
                }
            )
        return results

