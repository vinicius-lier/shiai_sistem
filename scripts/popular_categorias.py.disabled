from atletas.models import Categoria, Classe
from decimal import Decimal
import re

def parse_peso(peso_str):
    """Converte string de peso (ex: 'Até 23 kg', '+23 a 26 kg') em limite_min e limite_max"""
    peso_str = peso_str.strip().replace('kg', '').strip()
    
    if peso_str.startswith('Até'):
        # "Até 23" -> limite_min=0, limite_max=23
        max_val = float(re.search(r'[\d.]+', peso_str).group())
        return Decimal('0'), Decimal(str(max_val))
    elif peso_str.startswith('+') and 'a' in peso_str:
        # "+23 a 26" -> limite_min=23, limite_max=26
        numbers = re.findall(r'[\d.]+', peso_str)
        if len(numbers) >= 2:
            return Decimal(numbers[0]), Decimal(numbers[1])
        elif len(numbers) == 1:
            return Decimal(numbers[0]), None
    elif peso_str.startswith('+'):
        # "+50" -> limite_min=50, limite_max=None
        min_val = float(re.search(r'[\d.]+', peso_str).group())
        return Decimal(str(min_val)), None
    
    return None, None

def run():
    # Mapeamento de classes com idade_min e idade_max
    classes_map = {
        "SUB-9": ("SUB 9", 7, 8),
        "SUB-11": ("SUB 11", 9, 10),
        "SUB-13": ("SUB 13", 11, 12),
        "SUB-15": ("SUB 15", 13, 14),
        "SUB-18": ("SUB 18", 15, 17),
        "SÊNIOR/VET": ("SÊNIOR", 21, 29),  # Usar SÊNIOR para SÊNIOR/VET
    }
    
    categorias_data = [
        # MASCULINO – SUB-9
        ("SUB-9", "M", "Até 23 kg"),
        ("SUB-9", "M", "+23 a 26 kg"),
        ("SUB-9", "M", "+26 a 29 kg"),
        ("SUB-9", "M", "+29 a 32 kg"),
        ("SUB-9", "M", "+32 a 36 kg"),
        ("SUB-9", "M", "+36 a 40 kg"),
        ("SUB-9", "M", "+40 a 45 kg"),
        ("SUB-9", "M", "+45 a 50 kg"),
        ("SUB-9", "M", "+50 kg"),

        # MASCULINO – SUB-11
        ("SUB-11", "M", "Até 26 kg"),
        ("SUB-11", "M", "+26 a 28 kg"),
        ("SUB-11", "M", "+28 a 30 kg"),
        ("SUB-11", "M", "+30 a 33 kg"),
        ("SUB-11", "M", "+33 a 36 kg"),
        ("SUB-11", "M", "+36 a 40 kg"),
        ("SUB-11", "M", "+40 a 45 kg"),
        ("SUB-11", "M", "+45 a 50 kg"),
        ("SUB-11", "M", "+50 kg"),

        # MASCULINO – SUB-13
        ("SUB-13", "M", "Até 28 kg"),
        ("SUB-13", "M", "+28 a 31 kg"),
        ("SUB-13", "M", "+31 a 34 kg"),
        ("SUB-13", "M", "+34 a 38 kg"),
        ("SUB-13", "M", "+38 a 42 kg"),
        ("SUB-13", "M", "+42 a 47 kg"),
        ("SUB-13", "M", "+47 a 52 kg"),
        ("SUB-13", "M", "+52 a 60 kg"),
        ("SUB-13", "M", "+60 kg"),

        # MASCULINO – SUB-15
        ("SUB-15", "M", "Até 40 kg"),
        ("SUB-15", "M", "+40 a 45 kg"),
        ("SUB-15", "M", "+45 a 50 kg"),
        ("SUB-15", "M", "+50 a 55 kg"),
        ("SUB-15", "M", "+55 a 60 kg"),
        ("SUB-15", "M", "+60 a 66 kg"),
        ("SUB-15", "M", "+66 a 73 kg"),
        ("SUB-15", "M", "+73 a 81 kg"),
        ("SUB-15", "M", "+81 kg"),

        # MASCULINO – SUB-18
        ("SUB-18", "M", "Até 50 kg"),
        ("SUB-18", "M", "+50 a 55 kg"),
        ("SUB-18", "M", "+55 a 60 kg"),
        ("SUB-18", "M", "+60 a 66 kg"),
        ("SUB-18", "M", "+66 a 73 kg"),
        ("SUB-18", "M", "+73 a 81 kg"),
        ("SUB-18", "M", "+81 a 90 kg"),
        ("SUB-18", "M", "+90 a 100 kg"),
        ("SUB-18", "M", "+100 kg"),

        # MASCULINO – SÊNIOR/VET
        ("SÊNIOR/VET", "M", "Até 60 kg"),
        ("SÊNIOR/VET", "M", "+60 a 66 kg"),
        ("SÊNIOR/VET", "M", "+66 a 73 kg"),
        ("SÊNIOR/VET", "M", "+73 a 81 kg"),
        ("SÊNIOR/VET", "M", "+81 a 90 kg"),
        ("SÊNIOR/VET", "M", "+90 a 100 kg"),
        ("SÊNIOR/VET", "M", "+100 kg"),

        # FEMININO – SUB-9
        ("SUB-9", "F", "Até 23 kg"),
        ("SUB-9", "F", "+23 a 26 kg"),
        ("SUB-9", "F", "+26 a 29 kg"),
        ("SUB-9", "F", "+29 a 32 kg"),
        ("SUB-9", "F", "+32 a 36 kg"),
        ("SUB-9", "F", "+36 a 40 kg"),
        ("SUB-9", "F", "+40 a 45 kg"),
        ("SUB-9", "F", "+45 a 50 kg"),
        ("SUB-9", "F", "+50 kg"),

        # FEMININO – SUB-11
        ("SUB-11", "F", "Até 26 kg"),
        ("SUB-11", "F", "+26 a 28 kg"),
        ("SUB-11", "F", "+28 a 30 kg"),
        ("SUB-11", "F", "+30 a 33 kg"),
        ("SUB-11", "F", "+33 a 36 kg"),
        ("SUB-11", "F", "+36 a 40 kg"),
        ("SUB-11", "F", "+40 a 45 kg"),
        ("SUB-11", "F", "+45 a 50 kg"),
        ("SUB-11", "F", "+50 kg"),

        # FEMININO – SUB-13
        ("SUB-13", "F", "Até 28 kg"),
        ("SUB-13", "F", "+28 a 31 kg"),
        ("SUB-13", "F", "+31 a 34 kg"),
        ("SUB-13", "F", "+34 a 38 kg"),
        ("SUB-13", "F", "+38 a 42 kg"),
        ("SUB-13", "F", "+42 a 47 kg"),
        ("SUB-13", "F", "+47 a 52 kg"),
        ("SUB-13", "F", "+52 a 60 kg"),
        ("SUB-13", "F", "+60 kg"),

        # FEMININO – SUB-15
        ("SUB-15", "F", "Até 36 kg"),
        ("SUB-15", "F", "+36 a 40 kg"),
        ("SUB-15", "F", "+40 a 44 kg"),
        ("SUB-15", "F", "+44 a 48 kg"),
        ("SUB-15", "F", "+48 a 52 kg"),
        ("SUB-15", "F", "+52 a 57 kg"),
        ("SUB-15", "F", "+57 a 63 kg"),
        ("SUB-15", "F", "+63 a 70 kg"),
        ("SUB-15", "F", "+70 kg"),

        # FEMININO – SUB-18
        ("SUB-18", "F", "Até 40 kg"),
        ("SUB-18", "F", "+40 a 44 kg"),
        ("SUB-18", "F", "+44 a 48 kg"),
        ("SUB-18", "F", "+48 a 52 kg"),
        ("SUB-18", "F", "+52 a 57 kg"),
        ("SUB-18", "F", "+57 a 63 kg"),
        ("SUB-18", "F", "+63 a 70 kg"),
        ("SUB-18", "F", "+70 kg"),

        # FEMININO – SÊNIOR/VET
        ("SÊNIOR/VET", "F", "Até 48 kg"),
        ("SÊNIOR/VET", "F", "+48 a 52 kg"),
        ("SÊNIOR/VET", "F", "+52 a 57 kg"),
        ("SÊNIOR/VET", "F", "+57 a 63 kg"),
        ("SÊNIOR/VET", "F", "+63 a 70 kg"),
        ("SÊNIOR/VET", "F", "+70 a 78 kg"),
        ("SÊNIOR/VET", "F", "+78 kg"),
    ]

    objs = []
    for classe_key, sexo, peso_str in categorias_data:
        # Mapear nome da classe (SUB-9 -> SUB 9, etc.)
        classe_nome, idade_min, idade_max = classes_map[classe_key]
        
        # Buscar ou criar a classe com idade_min e idade_max
        classe, _ = Classe.objects.get_or_create(
            nome=classe_nome,
            defaults={
                'idade_min': idade_min,
                'idade_max': idade_max
            }
        )
        
        # Parse do peso
        limite_min, limite_max = parse_peso(peso_str)
        if limite_min is None:
            print(f"⚠️ Erro ao parsear peso: {peso_str}")
            continue
        
        # Gerar categoria_nome e label
        categoria_nome = peso_str.replace('kg', '').strip()
        sexo_display = "Masculino" if sexo == "M" else "Feminino"
        label = f"{classe_nome} - {sexo_display} - {peso_str}"
        
        objs.append(Categoria(
            classe=classe,
            sexo=sexo,
            categoria_nome=categoria_nome,
            limite_min=limite_min,
            limite_max=limite_max,
            label=label
        ))
    
    Categoria.objects.bulk_create(objs, ignore_conflicts=True)
    print(f"✅ {len(objs)} categorias populadas com sucesso!")

if __name__ == "__main__":
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'judocomp.settings')
    django.setup()
    run()
