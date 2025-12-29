from django.db import migrations
from datetime import date
from decimal import Decimal


def calcular_classe_por_idade(idade):
    if idade is None:
        return None
    if idade <= 6:
        return "FESTIVAL"
    if 7 <= idade <= 8:
        return "SUB-9"
    if 9 <= idade <= 10:
        return "SUB-11"
    if 11 <= idade <= 12:
        return "SUB-13"
    if 13 <= idade <= 14:
        return "SUB-15"
    if 15 <= idade <= 17:
        return "SUB-18"
    if 18 <= idade <= 20:
        return "SUB-21"
    if 21 <= idade <= 29:
        return "SÊNIOR"
    return "VETERANOS"


def map_status(status_legado):
    """
    Mapeia status antigos para status_atual:
    - pendente_pesagem -> inscrito
    - ok -> aprovado
    - remanejado -> remanejado
    - desclassificado -> desclassificado
    - pendente/confirmado -> inscrito
    - aprovado (legado) -> aprovado
    - reprovado -> desclassificado
    Caso não reconheça, retorna 'pendente'.
    """
    if not status_legado:
        return "pendente"
    status_legado = status_legado.lower()
    if status_legado == "pendente_pesagem":
        return "inscrito"
    if status_legado == "ok":
        return "aprovado"
    if status_legado == "remanejado":
        return "remanejado"
    if status_legado == "desclassificado":
        return "desclassificado"
    if status_legado in ("pendente", "confirmado"):
        return "inscrito"
    if status_legado == "aprovado":
        return "aprovado"
    if status_legado == "reprovado":
        return "desclassificado"
    return "pendente"


def forwards(apps, schema_editor):
    Inscricao = apps.get_model('atletas', 'Inscricao')
    Classe = apps.get_model('atletas', 'Classe')
    Categoria = apps.get_model('atletas', 'Categoria')

    hoje = date.today()

    qs = Inscricao.objects.select_related('atleta')
    for ins in qs:
        atleta = ins.atleta

        # Classe
        classe_nome = None
        if getattr(atleta, 'data_nascimento', None):
            idade = hoje.year - atleta.data_nascimento.year - (
                (hoje.month, hoje.day) < (atleta.data_nascimento.month, atleta.data_nascimento.day)
            )
            classe_nome = calcular_classe_por_idade(idade)
        if not classe_nome:
            classe_nome = (ins.classe_escolhida or "").strip()

        classe_obj = None
        if classe_nome:
            classe_obj = Classe.objects.filter(nome__iexact=classe_nome).first()

        # Categoria
        categoria_nome = (
            ins.categoria_ajustada
            or ins.categoria_escolhida
            or ins.categoria_calculada
            or ""
        ).strip()
        categoria_obj = None
        if categoria_nome:
            if classe_obj:
                categoria_obj = Categoria.objects.filter(
                    categoria_nome=categoria_nome,
                    classe=classe_obj,
                    sexo=atleta.sexo
                ).first()
            if not categoria_obj:
                categoria_obj = Categoria.objects.filter(
                    categoria_nome=categoria_nome,
                    sexo=atleta.sexo
                ).first()

        # Peso
        peso_val = ins.peso if ins.peso is not None else ins.peso_informado
        if peso_val is not None:
            try:
                peso_val = Decimal(str(peso_val))
            except Exception:
                peso_val = None

        # Status
        status_atual = map_status(ins.status_inscricao)

        # Atribuir
        ins.classe_real = classe_obj
        ins.categoria_real = categoria_obj
        ins.peso_real = peso_val
        ins.status_atual = status_atual
        ins.save(update_fields=['classe_real', 'categoria_real', 'peso_real', 'status_atual'])


def backwards(apps, schema_editor):
    Inscricao = apps.get_model('atletas', 'Inscricao')
    Inscricao.objects.update(
        classe_real=None,
        categoria_real=None,
        peso_real=None,
        status_atual='pendente'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0010_inscricao_campos_normalizados'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]

