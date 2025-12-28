from django.db import migrations, models


ELIGIBILIDADE_SQL = """
CREATE TABLE IF NOT EXISTS atletas_classeelegivel (
    id bigserial PRIMARY KEY,
    classe_origem_id bigint NOT NULL REFERENCES atletas_classe(id) ON DELETE CASCADE,
    classe_destino_id bigint NOT NULL REFERENCES atletas_classe(id) ON DELETE CASCADE
);

INSERT INTO atletas_classeelegivel (classe_origem_id, classe_destino_id)
SELECT DISTINCT id, id FROM atletas_classe;

INSERT INTO atletas_classeelegivel (classe_origem_id, classe_destino_id)
SELECT DISTINCT o.id, d.id
FROM atletas_classe o
JOIN atletas_classe d ON d.nome IN ('SUB-18', 'SUB-21', 'SÊNIOR')
WHERE o.nome = 'SUB-18';

INSERT INTO atletas_classeelegivel (classe_origem_id, classe_destino_id)
SELECT DISTINCT o.id, d.id
FROM atletas_classe o
JOIN atletas_classe d ON d.nome IN ('SUB-21', 'SÊNIOR')
WHERE o.nome = 'SUB-21';

INSERT INTO atletas_classeelegivel (classe_origem_id, classe_destino_id)
SELECT DISTINCT o.id, d.id
FROM atletas_classe o
JOIN atletas_classe d ON d.nome IN ('VETERANO', 'VETERANOS', 'MASTER', 'SÊNIOR')
WHERE o.nome IN ('VETERANO', 'VETERANOS', 'MASTER');

DELETE FROM atletas_classeelegivel a
USING atletas_classeelegivel b
WHERE a.id > b.id
  AND a.classe_origem_id = b.classe_origem_id
  AND a.classe_destino_id = b.classe_destino_id;

ALTER TABLE atletas_classeelegivel
    ADD CONSTRAINT atletas_classeelegivel_unique
    UNIQUE (classe_origem_id, classe_destino_id);
"""

ELIGIBILIDADE_SQL_REVERSE = """
DROP TABLE IF EXISTS atletas_classeelegivel;
"""

TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION atletas_validar_classe_elegivel()
RETURNS trigger AS $$
DECLARE
    v_ano_evento integer;
    v_ano_nasc integer;
    v_idade integer;
    v_classe_origem_id integer;
    v_permitido boolean;
BEGIN
    IF NEW.classe_real_id IS NULL THEN
        RAISE EXCEPTION 'classe_real_id é obrigatório para validar elegibilidade';
    END IF;

    SELECT EXTRACT(YEAR FROM c.data_competicao)::int
    INTO v_ano_evento
    FROM atletas_campeonato c
    WHERE c.id = NEW.campeonato_id;

    IF v_ano_evento IS NULL THEN
        RAISE EXCEPTION 'campeonato.data_competicao inválida para elegibilidade';
    END IF;

    SELECT COALESCE(EXTRACT(YEAR FROM a.data_nascimento)::int, a.ano_nasc)
    INTO v_ano_nasc
    FROM atletas_atleta a
    WHERE a.id = NEW.atleta_id;

    IF v_ano_nasc IS NULL THEN
        RAISE EXCEPTION 'atleta sem ano de nascimento para elegibilidade';
    END IF;

    v_idade := v_ano_evento - v_ano_nasc;

    SELECT cl.id
    INTO v_classe_origem_id
    FROM atletas_classe cl
    WHERE v_idade BETWEEN cl.idade_min AND cl.idade_max
    ORDER BY cl.idade_min
    LIMIT 1;

    IF v_classe_origem_id IS NULL THEN
        RAISE EXCEPTION 'classe de origem não encontrada para idade %', v_idade;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM atletas_classeelegivel ce
        WHERE ce.classe_origem_id = v_classe_origem_id
          AND ce.classe_destino_id = NEW.classe_real_id
    )
    INTO v_permitido;

    IF NOT v_permitido THEN
        RAISE EXCEPTION 'classe destino % não elegível para classe base %',
            NEW.classe_real_id, v_classe_origem_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS atletas_validar_classe_elegivel_trg ON atletas_inscricao;
CREATE TRIGGER atletas_validar_classe_elegivel_trg
BEFORE INSERT OR UPDATE OF classe_real_id, atleta_id, campeonato_id
ON atletas_inscricao
FOR EACH ROW
EXECUTE FUNCTION atletas_validar_classe_elegivel();
"""

TRIGGER_SQL_REVERSE = """
DROP TRIGGER IF EXISTS atletas_validar_classe_elegivel_trg ON atletas_inscricao;
DROP FUNCTION IF EXISTS atletas_validar_classe_elegivel();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("atletas", "0013_swap_auth_user_fk"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(ELIGIBILIDADE_SQL, ELIGIBILIDADE_SQL_REVERSE),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="ClasseElegivel",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("classe_origem", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="elegiveis_origem", to="atletas.classe", verbose_name="Classe de Origem")),
                        ("classe_destino", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="elegiveis_destino", to="atletas.classe", verbose_name="Classe de Destino")),
                    ],
                    options={
                        "verbose_name": "Classe Elegível",
                        "verbose_name_plural": "Classes Elegíveis",
                        "unique_together": {("classe_origem", "classe_destino")},
                    },
                ),
            ],
        ),
        migrations.RunSQL(TRIGGER_SQL, TRIGGER_SQL_REVERSE),
    ]
