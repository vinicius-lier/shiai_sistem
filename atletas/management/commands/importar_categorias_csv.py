import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand

from atletas.models import Classe, Categoria


IDADE_POR_CLASSE = {
    "FESTIVAL": (4, 6),
    "SUB-9": (7, 8),
    "SUB-10": (9, 9),
    "SUB-11": (10, 10),
    "SUB-13": (11, 12),
    "SUB-15": (13, 14),
    "SUB-18": (15, 17),
    "SÊNIOR": (18, 29),
    "VETERANOS": (30, 99),
}


def _normalize_classe(nome: str) -> str:
    if not nome:
        return ""
    up = nome.strip().upper().replace("SUB ", "SUB-")
    if up in {"VETERANO", "VETERANOS", "MASTER", "MASTERS"}:
        return "VETERANOS"
    if up in {"SENIOR", "SÊNIOR"}:
        return "SÊNIOR"
    return up


def _normalize_sexo(valor: str) -> str:
    if not valor:
        return ""
    up = valor.strip().upper()
    if up in {"M", "MASCULINO"}:
        return "M"
    if up in {"F", "FEMININO"}:
        return "F"
    return up[:1]


def _to_decimal(valor: str) -> Decimal:
    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


class Command(BaseCommand):
    help = "Importa categorias de judô a partir do CSV categorias_oficiais_judo.csv."

    def handle(self, *args, **options):
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        csv_path = base_dir / "categorias_oficiais_judo.csv"

        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f"Arquivo não encontrado: {csv_path}"))
            return

        criadas = 0
        atualizadas = 0
        classes_criadas = 0

        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                classe_nome = _normalize_classe(row.get("classe", ""))
                sexo = _normalize_sexo(row.get("sexo", ""))
                categoria_nome = row.get("nome_categoria", "").strip()
                label = row.get("label_completo", "").strip()
                limite_min = _to_decimal(row.get("limite_minimo_kg", "0"))
                limite_max_raw = _to_decimal(row.get("limite_maximo_kg", "0"))
                limite_max = None if limite_max_raw >= Decimal("999") else limite_max_raw

                if not classe_nome or not sexo or not categoria_nome:
                    continue

                idade_min, idade_max = IDADE_POR_CLASSE.get(classe_nome, (0, 99))
                classe_obj, created = Classe.objects.get_or_create(
                    nome=classe_nome,
                    defaults={"idade_min": idade_min, "idade_max": idade_max},
                )
                if created:
                    classes_criadas += 1

                obj, created = Categoria.objects.update_or_create(
                    classe=classe_obj,
                    sexo=sexo,
                    categoria_nome=categoria_nome,
                    defaults={
                        "limite_min": limite_min,
                        "limite_max": limite_max,
                        "label": label or f"{classe_nome} - {categoria_nome}",
                    },
                )
                if created:
                    criadas += 1
                else:
                    atualizadas += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Importação concluída.\n"
                f"Classes criadas: {classes_criadas}\n"
                f"Categorias criadas: {criadas}\n"
                f"Categorias atualizadas: {atualizadas}"
            )
        )
