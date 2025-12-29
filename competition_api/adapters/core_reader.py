from uuid import UUID
import logging

from django.db import connection
from django.db.utils import OperationalError, DatabaseError

from adapters.exceptions import CoreUnavailableError

logger = logging.getLogger(__name__)


class CoreSQLReader:
    statement_timeout_ms = 2000  # fail fast

    def _set_statement_timeout(self, cursor):
        cursor.execute(f"SET LOCAL statement_timeout = {self.statement_timeout_ms}")

    def organization_exists_and_active(self, organization_id: UUID) -> bool:
        query = """
            SELECT 1
            FROM core.organizations_organization
            WHERE id = %s AND is_active = TRUE
            LIMIT 1
        """
        try:
            with connection.cursor() as cursor:
                self._set_statement_timeout(cursor)
                cursor.execute(query, [organization_id])
                return cursor.fetchone() is not None
        except (OperationalError, DatabaseError) as exc:
            logger.warning("Core indisponível ao validar organização", exc_info=exc)
            raise CoreUnavailableError("Core indisponível para validar organização") from exc

    def athlete_belongs_to_org(self, athlete_id: UUID, organization_id: UUID) -> bool:
        query = """
            SELECT 1
            FROM core.athletes_athlete
            WHERE id = %s AND organization_id = %s AND is_active = TRUE
            LIMIT 1
        """
        try:
            with connection.cursor() as cursor:
                self._set_statement_timeout(cursor)
                cursor.execute(query, [athlete_id, organization_id])
                return cursor.fetchone() is not None
        except (OperationalError, DatabaseError) as exc:
            logger.warning("Core indisponível ao validar atleta", exc_info=exc)
            raise CoreUnavailableError("Core indisponível para validar atleta") from exc

    def get_athlete_profile(self, athlete_id: UUID) -> dict:
        query = """
            SELECT sexo, faixa
            FROM core.atletas_atleta
            WHERE id = %s AND status_ativo = TRUE
            LIMIT 1
        """
        try:
            with connection.cursor() as cursor:
                self._set_statement_timeout(cursor)
                cursor.execute(query, [athlete_id])
                row = cursor.fetchone()
        except (OperationalError, DatabaseError) as exc:
            logger.warning("Core indisponível ao obter perfil do atleta", exc_info=exc)
            raise CoreUnavailableError("Core indisponível para obter perfil") from exc

        if not row:
            raise ValueError("Perfil do atleta não encontrado ou inativo")
        sexo, faixa = row
        if not sexo or not faixa:
            raise ValueError("Perfil do atleta incompleto (sexo/faixa ausentes)")
        return {"sex": sexo, "belt": faixa}

