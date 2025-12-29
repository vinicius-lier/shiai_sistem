from django.core.management.base import BaseCommand
from decimal import Decimal

from atletas.models import Classe, Categoria


TABLES = {
    "M": {
        "SUB-9": [
            ("Super Ligeiro", 0, 23),
            ("Ligeiro", 23, 26),
            ("Meio Leve", 26, 29),
            ("Leve", 29, 32),
            ("Meio Médio", 32, 36),
            ("Médio", 36, 40),
            ("Meio Pesado", 40, 45),
            ("Pesado", 45, 50),
            ("Super Pesado", 50, None),
        ],
        "SUB-11": [
            ("Super Ligeiro", 0, 26),
            ("Ligeiro", 26, 28),
            ("Meio Leve", 28, 30),
            ("Leve", 30, 33),
            ("Meio Médio", 33, 36),
            ("Médio", 36, 40),
            ("Meio Pesado", 40, 45),
            ("Pesado", 45, 50),
            ("Super Pesado", 50, None),
        ],
        "SUB-13": [
            ("Super Ligeiro", 0, 28),
            ("Ligeiro", 28, 31),
            ("Meio Leve", 31, 34),
            ("Leve", 34, 38),
            ("Meio Médio", 38, 42),
            ("Médio", 42, 47),
            ("Meio Pesado", 47, 52),
            ("Pesado", 52, 60),
            ("Super Pesado", 60, None),
        ],
        "SUB-15": [
            ("Super Ligeiro", 0, 40),
            ("Ligeiro", 40, 45),
            ("Meio Leve", 45, 50),
            ("Leve", 50, 55),
            ("Meio Médio", 55, 60),
            ("Médio", 60, 66),
            ("Meio Pesado", 66, 73),
            ("Pesado", 73, 81),
            ("Super Pesado", 81, None),
        ],
        "SUB-18": [
            ("Super Ligeiro", 0, 50),
            ("Ligeiro", 50, 55),
            ("Meio Leve", 55, 60),
            ("Leve", 60, 66),
            ("Meio Médio", 66, 73),
            ("Médio", 73, 81),
            ("Meio Pesado", 81, 90),
            ("Pesado", 90, 100),
            ("Super Pesado", 100, None),
        ],
        "SÊNIOR / MASTER": [
            ("Super Ligeiro", 0, 60),
            ("Ligeiro", 60, 66),
            ("Meio Leve", 66, 73),
            ("Leve", 73, 81),
            ("Meio Médio", 81, 90),
            ("Médio", 90, 100),
            ("Meio Pesado", 100, None),
        ],
    },
    "F": {
        "SUB-9": [
            ("Super Ligeiro", 0, 23),
            ("Ligeiro", 23, 26),
            ("Meio Leve", 26, 29),
            ("Leve", 29, 32),
            ("Meio Médio", 32, 36),
            ("Médio", 36, 40),
            ("Meio Pesado", 40, 45),
            ("Pesado", 45, 50),
            ("Super Pesado", 50, None),
        ],
        "SUB-11": [
            ("Super Ligeiro", 0, 26),
            ("Ligeiro", 26, 28),
            ("Meio Leve", 28, 30),
            ("Leve", 30, 33),
            ("Meio Médio", 33, 36),
            ("Médio", 36, 40),
            ("Meio Pesado", 40, 45),
            ("Pesado", 45, 50),
            ("Super Pesado", 50, None),
        ],
        "SUB-13": [
            ("Super Ligeiro", 0, 28),
            ("Ligeiro", 28, 31),
            ("Meio Leve", 31, 34),
            ("Leve", 34, 38),
            ("Meio Médio", 38, 42),
            ("Médio", 42, 47),
            ("Meio Pesado", 47, 52),
            ("Pesado", 52, 60),
            ("Super Pesado", 60, None),
        ],
        "SUB-15": [
            ("Super Ligeiro", 0, 36),
            ("Ligeiro", 36, 40),
            ("Meio Leve", 40, 44),
            ("Leve", 44, 48),
            ("Meio Médio", 48, 52),
            ("Médio", 52, 57),
            ("Meio Pesado", 57, 63),
            ("Pesado", 63, 70),
            ("Super Pesado", 70, None),
        ],
        "SUB-18": [
            ("Super Ligeiro", 0, 40),
            ("Ligeiro", 40, 44),
            ("Meio Leve", 44, 48),
            ("Leve", 48, 52),
            ("Meio Médio", 52, 57),
            ("Médio", 57, 63),
            ("Meio Pesado", 63, 70),
            ("Pesado", 70, None),
            ("Super Pesado", 70, None),
        ],
        "SÊNIOR / MASTER": [
            ("Super Ligeiro", 0, 48),
            ("Ligeiro", 48, 52),
            ("Meio Leve", 52, 57),
            ("Leve", 57, 63),
            ("Meio Médio", 63, 70),
            ("Médio", 70, 78),
            ("Meio Pesado", 78, None),
        ],
    },
}


def _normalize_classe(nome: str) -> str:
    return nome.strip().upper().replace("SUB ", "SUB-")


class Command(BaseCommand):
    help = "Seed/atualiza categorias oficiais 2025 (masculino/feminino)."

    def handle(self, *args, **options):
        total = 0
        for sexo, classes in TABLES.items():
            for classe_nome, categorias in classes.items():
                classe_obj, _ = Classe.objects.get_or_create(nome=_normalize_classe(classe_nome), defaults={
                    "idade_min": 0,
                    "idade_max": 99,
                })
                for cat_nome, min_kg, max_kg in categorias:
                    limite_min = Decimal(str(min_kg))
                    limite_max = Decimal(str(max_kg)) if max_kg is not None else None
                    label = f"{classe_obj.nome} - {cat_nome}"
                    obj, created = Categoria.objects.update_or_create(
                        classe=classe_obj,
                        sexo=sexo,
                        categoria_nome=cat_nome,
                        defaults={
                            "limite_min": limite_min,
                            "limite_max": limite_max,
                            "label": label,
                        }
                    )
                    total += 1
        self.stdout.write(self.style.SUCCESS(f"Categorias atualizadas/criadas: {total}"))

