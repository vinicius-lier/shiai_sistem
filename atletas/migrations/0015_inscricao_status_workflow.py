from django.db import migrations, models


ENUM_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_inscricao') THEN
        CREATE TYPE status_inscricao AS ENUM (
            'RASCUNHO',
            'CONFIRMADA',
            'PESADA',
            'BLOQUEADA',
            'CANCELADA'
        );
    END IF;
END$$;
"""

ENUM_SQL_REVERSE = """
DROP TYPE IF EXISTS status_inscricao;
"""

ALTER_COLUMN_SQL = """
ALTER TABLE atletas_inscricao
    ALTER COLUMN status TYPE status_inscricao
    USING status::status_inscricao;
"""

ALTER_COLUMN_SQL_REVERSE = """
"""

TRANSITIONS_SQL = """
CREATE TABLE IF NOT EXISTS atletas_inscricao_status_transicao (
    id bigserial PRIMARY KEY,
    de_status status_inscricao NOT NULL,
    para_status status_inscricao NOT NULL,
    UNIQUE (de_status, para_status)
);

INSERT INTO atletas_inscricao_status_transicao (de_status, para_status)
VALUES
    ('RASCUNHO','CONFIRMADA'),
    ('CONFIRMADA','PESADA'),
    ('PESADA','BLOQUEADA'),
    ('RASCUNHO','CANCELADA'),
    ('CONFIRMADA','CANCELADA')
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION atletas_validar_transicao_status_inscricao()
RETURNS trigger AS $$
DECLARE
    permitido boolean;
BEGIN
    IF OLD.status = 'BLOQUEADA' THEN
        RAISE EXCEPTION 'Inscrição BLOQUEADA não pode ser alterada';
    END IF;

    IF OLD.status = 'CANCELADA' THEN
        RAISE EXCEPTION 'Inscrição CANCELADA não pode ser alterada';
    END IF;

    IF NEW.status = OLD.status THEN
        RETURN NEW;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM atletas_inscricao_status_transicao t
        WHERE t.de_status = OLD.status
          AND t.para_status = NEW.status
    )
    INTO permitido;

    IF NOT permitido THEN
        RAISE EXCEPTION 'Transição inválida: % -> %', OLD.status, NEW.status;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_transicao_status_inscricao ON atletas_inscricao;
CREATE TRIGGER trg_validar_transicao_status_inscricao
BEFORE UPDATE OF status ON atletas_inscricao
FOR EACH ROW
EXECUTE FUNCTION atletas_validar_transicao_status_inscricao();

CREATE OR REPLACE FUNCTION atletas_bloquear_delete_inscricao()
RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'Exclusão de inscrição proibida (histórico imutável)';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_bloquear_delete_inscricao ON atletas_inscricao;
CREATE TRIGGER trg_bloquear_delete_inscricao
BEFORE DELETE ON atletas_inscricao
FOR EACH ROW
EXECUTE FUNCTION atletas_bloquear_delete_inscricao();
"""

TRANSITIONS_SQL_REVERSE = """
DROP TRIGGER IF EXISTS trg_validar_transicao_status_inscricao ON atletas_inscricao;
DROP FUNCTION IF EXISTS atletas_validar_transicao_status_inscricao();

DROP TRIGGER IF EXISTS trg_bloquear_delete_inscricao ON atletas_inscricao;
DROP FUNCTION IF EXISTS atletas_bloquear_delete_inscricao();

DROP TABLE IF EXISTS atletas_inscricao_status_transicao;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("atletas", "0014_classe_elegivel"),
    ]

    operations = [
        migrations.RunSQL(ENUM_SQL, ENUM_SQL_REVERSE),
        migrations.AddField(
            model_name="inscricao",
            name="status",
            field=models.CharField(
                choices=[
                    ("RASCUNHO", "Rascunho"),
                    ("CONFIRMADA", "Confirmada"),
                    ("PESADA", "Pesada"),
                    ("BLOQUEADA", "Bloqueada"),
                    ("CANCELADA", "Cancelada"),
                ],
                db_index=False,
                default="RASCUNHO",
                max_length=20,
                verbose_name="Status (Workflow)",
            ),
        ),
        migrations.RunSQL(ALTER_COLUMN_SQL, ALTER_COLUMN_SQL_REVERSE),
        migrations.RunSQL(TRANSITIONS_SQL, TRANSITIONS_SQL_REVERSE),
    ]
