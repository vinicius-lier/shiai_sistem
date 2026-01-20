"""
Comando para popular categorias de peso conforme regulamento especifico.
Executa: python manage.py popular_categorias_regulamento
"""
from decimal import Decimal
import re
from django.core.management.base import BaseCommand

from atletas.models import Categoria, Classe


CLASS_DATA = {
    "SUB-9": ("SUB 9", 7, 8),
    "SUB-11": ("SUB 11", 10, 10),
    "SUB-13": ("SUB 13", 11, 12),
    "SUB-15": ("SUB 15", 13, 14),
    "SUB-18": ("SUB 18", 15, 17),
    "SENIOR": ("SENIOR", 18, 29),
    "VETERANOS": ("VETERANOS", 30, 99),
}


def _ensure_classe(classe_key: str) -> Classe:
    nome, idade_min, idade_max = CLASS_DATA[classe_key]
    classe, _ = Classe.objects.get_or_create(
        nome=nome,
        defaults={"idade_min": idade_min, "idade_max": idade_max},
    )
    return classe


class Command(BaseCommand):
    help = "Popula categorias de peso conforme regulamento especifico"

    def parse_peso(self, peso_str: str):
        """
        Parseia strings como:
        - "Ate 23 kg" -> (0, 23)
        - "+23 a 26 kg" -> (23, 26)
        - "+50 kg" -> (50, None)
        """
        peso = peso_str.strip().lower().replace("até", "ate")

        match = re.match(r"ate\s+(\d+(?:\.\d+)?)\s*kg", peso)
        if match:
            return (Decimal("0"), Decimal(match.group(1)))

        match = re.match(r"\+(\d+(?:\.\d+)?)\s+a\s+(\d+(?:\.\d+)?)\s*kg", peso)
        if match:
            return (Decimal(match.group(1)), Decimal(match.group(2)))

        match = re.match(r"\+(\d+(?:\.\d+)?)\s*kg", peso)
        if match:
            return (Decimal(match.group(1)), None)

        raise ValueError(f"Formato de peso nao reconhecido: {peso_str}")

    def handle(self, *args, **options):
        categorias = [
            # SUB-9 - Masculino
            ("SUB-9", "M", "Ate 23 kg"),
            ("SUB-9", "M", "+23 a 26 kg"),
            ("SUB-9", "M", "+26 a 29 kg"),
            ("SUB-9", "M", "+29 a 32 kg"),
            ("SUB-9", "M", "+32 a 36 kg"),
            ("SUB-9", "M", "+36 a 40 kg"),
            ("SUB-9", "M", "+40 a 45 kg"),
            ("SUB-9", "M", "+45 a 50 kg"),
            ("SUB-9", "M", "+50 kg"),
            # SUB-9 - Feminino
            ("SUB-9", "F", "Ate 23 kg"),
            ("SUB-9", "F", "+23 a 26 kg"),
            ("SUB-9", "F", "+26 a 29 kg"),
            ("SUB-9", "F", "+29 a 32 kg"),
            ("SUB-9", "F", "+32 a 36 kg"),
            ("SUB-9", "F", "+36 a 40 kg"),
            ("SUB-9", "F", "+40 a 45 kg"),
            ("SUB-9", "F", "+45 a 50 kg"),
            ("SUB-9", "F", "+50 kg"),
            # SUB-11 - Masculino
            ("SUB-11", "M", "Ate 26 kg"),
            ("SUB-11", "M", "+26 a 28 kg"),
            ("SUB-11", "M", "+28 a 30 kg"),
            ("SUB-11", "M", "+30 a 33 kg"),
            ("SUB-11", "M", "+33 a 36 kg"),
            ("SUB-11", "M", "+36 a 40 kg"),
            ("SUB-11", "M", "+40 a 45 kg"),
            ("SUB-11", "M", "+45 a 50 kg"),
            ("SUB-11", "M", "+50 kg"),
            # SUB-11 - Feminino
            ("SUB-11", "F", "Ate 26 kg"),
            ("SUB-11", "F", "+26 a 28 kg"),
            ("SUB-11", "F", "+28 a 30 kg"),
            ("SUB-11", "F", "+30 a 33 kg"),
            ("SUB-11", "F", "+33 a 36 kg"),
            ("SUB-11", "F", "+36 a 40 kg"),
            ("SUB-11", "F", "+40 a 45 kg"),
            ("SUB-11", "F", "+45 a 50 kg"),
            ("SUB-11", "F", "+50 kg"),
            # SUB-13 - Masculino
            ("SUB-13", "M", "Ate 28 kg"),
            ("SUB-13", "M", "+28 a 31 kg"),
            ("SUB-13", "M", "+31 a 34 kg"),
            ("SUB-13", "M", "+34 a 38 kg"),
            ("SUB-13", "M", "+38 a 42 kg"),
            ("SUB-13", "M", "+42 a 47 kg"),
            ("SUB-13", "M", "+47 a 52 kg"),
            ("SUB-13", "M", "+52 a 60 kg"),
            ("SUB-13", "M", "+60 kg"),
            # SUB-13 - Feminino
            ("SUB-13", "F", "Ate 28 kg"),
            ("SUB-13", "F", "+28 a 31 kg"),
            ("SUB-13", "F", "+31 a 34 kg"),
            ("SUB-13", "F", "+34 a 38 kg"),
            ("SUB-13", "F", "+38 a 42 kg"),
            ("SUB-13", "F", "+42 a 47 kg"),
            ("SUB-13", "F", "+47 a 52 kg"),
            ("SUB-13", "F", "+52 a 60 kg"),
            ("SUB-13", "F", "+60 kg"),
            # SUB-15 - Masculino
            ("SUB-15", "M", "Ate 40 kg"),
            ("SUB-15", "M", "+40 a 45 kg"),
            ("SUB-15", "M", "+45 a 50 kg"),
            ("SUB-15", "M", "+50 a 55 kg"),
            ("SUB-15", "M", "+55 a 60 kg"),
            ("SUB-15", "M", "+60 a 66 kg"),
            ("SUB-15", "M", "+66 a 73 kg"),
            ("SUB-15", "M", "+73 a 81 kg"),
            ("SUB-15", "M", "+81 kg"),
            # SUB-15 - Feminino
            ("SUB-15", "F", "Ate 36 kg"),
            ("SUB-15", "F", "+36 a 40 kg"),
            ("SUB-15", "F", "+40 a 44 kg"),
            ("SUB-15", "F", "+44 a 48 kg"),
            ("SUB-15", "F", "+48 a 52 kg"),
            ("SUB-15", "F", "+52 a 57 kg"),
            ("SUB-15", "F", "+57 a 63 kg"),
            ("SUB-15", "F", "+63 a 70 kg"),
            ("SUB-15", "F", "+70 kg"),
            # SUB-18 - Masculino
            ("SUB-18", "M", "Ate 50 kg"),
            ("SUB-18", "M", "+50 a 55 kg"),
            ("SUB-18", "M", "+55 a 60 kg"),
            ("SUB-18", "M", "+60 a 66 kg"),
            ("SUB-18", "M", "+66 a 73 kg"),
            ("SUB-18", "M", "+73 a 81 kg"),
            ("SUB-18", "M", "+81 a 90 kg"),
            ("SUB-18", "M", "+90 a 100 kg"),
            ("SUB-18", "M", "+100 kg"),
            # SUB-18 - Feminino
            ("SUB-18", "F", "Ate 40 kg"),
            ("SUB-18", "F", "+40 a 44 kg"),
            ("SUB-18", "F", "+44 a 48 kg"),
            ("SUB-18", "F", "+48 a 52 kg"),
            ("SUB-18", "F", "+52 a 57 kg"),
            ("SUB-18", "F", "+57 a 63 kg"),
            ("SUB-18", "F", "+63 a 70 kg"),
            ("SUB-18", "F", "+70 kg"),
            # SENIOR - Masculino
            ("SENIOR", "M", "Ate 60 kg"),
            ("SENIOR", "M", "+60 a 66 kg"),
            ("SENIOR", "M", "+66 a 73 kg"),
            ("SENIOR", "M", "+73 a 81 kg"),
            ("SENIOR", "M", "+81 a 90 kg"),
            ("SENIOR", "M", "+90 a 100 kg"),
            ("SENIOR", "M", "+100 kg"),
            # SENIOR - Feminino
            ("SENIOR", "F", "Ate 48 kg"),
            ("SENIOR", "F", "+48 a 52 kg"),
            ("SENIOR", "F", "+52 a 57 kg"),
            ("SENIOR", "F", "+57 a 63 kg"),
            ("SENIOR", "F", "+63 a 70 kg"),
            ("SENIOR", "F", "+70 a 78 kg"),
            ("SENIOR", "F", "+78 kg"),
            # VETERANOS - Masculino
            ("VETERANOS", "M", "Ate 60 kg"),
            ("VETERANOS", "M", "+60 a 66 kg"),
            ("VETERANOS", "M", "+66 a 73 kg"),
            ("VETERANOS", "M", "+73 a 81 kg"),
            ("VETERANOS", "M", "+81 a 90 kg"),
            ("VETERANOS", "M", "+90 a 100 kg"),
            ("VETERANOS", "M", "+100 kg"),
            # VETERANOS - Feminino
            ("VETERANOS", "F", "Ate 48 kg"),
            ("VETERANOS", "F", "+48 a 52 kg"),
            ("VETERANOS", "F", "+52 a 57 kg"),
            ("VETERANOS", "F", "+57 a 63 kg"),
            ("VETERANOS", "F", "+63 a 70 kg"),
            ("VETERANOS", "F", "+70 a 78 kg"),
            ("VETERANOS", "F", "+78 kg"),
        ]

        criadas = 0
        atualizadas = 0
        erros = 0

        for classe_key, sexo, peso_str in categorias:
            try:
                classe = _ensure_classe(classe_key)
                limite_min, limite_max = self.parse_peso(peso_str)

                if limite_min == 0:
                    categoria_nome = f"Ate {limite_max}kg"
                elif limite_max is None:
                    categoria_nome = f"+{limite_min}kg"
                else:
                    categoria_nome = f"+{limite_min} a {limite_max}kg"

                sexo_display = "Masculino" if sexo == "M" else "Feminino"
                label = f"{classe.nome} - {sexo_display} - {categoria_nome}"

                _, created = Categoria.objects.update_or_create(
                    classe=classe,
                    sexo=sexo,
                    categoria_nome=categoria_nome,
                    defaults={
                        "limite_min": limite_min,
                        "limite_max": limite_max,
                        "label": label,
                    },
                )
                if created:
                    criadas += 1
                else:
                    atualizadas += 1
            except Exception as exc:
                erros += 1
                self.stdout.write(self.style.ERROR(f"Erro: {exc}"))

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Concluido. Criadas: {criadas}, Atualizadas: {atualizadas}, Erros: {erros}"
            )
        )
