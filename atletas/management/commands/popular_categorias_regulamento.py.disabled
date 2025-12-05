"""
Comando para popular categorias de peso conforme regulamento específico.
Executa no Render: python manage.py popular_categorias_regulamento
"""
from decimal import Decimal
import re
from django.core.management.base import BaseCommand
from atletas.models import Categoria, Classe


class Command(BaseCommand):
    help = 'Popula categorias de peso conforme regulamento específico'

    def parse_peso(self, peso_str):
        """
        Parseia strings como:
        - "Até 23 kg" -> (0, 23)
        - "+23 a 26 kg" -> (23, 26)
        - "+50 kg" -> (50, None)
        """
        peso_str = peso_str.strip().lower()
        
        # "Até X kg"
        match = re.match(r'até\s+(\d+(?:\.\d+)?)\s*kg', peso_str)
        if match:
            return (Decimal('0'), Decimal(match.group(1)))
        
        # "+X a Y kg"
        match = re.match(r'\+(\d+(?:\.\d+)?)\s+a\s+(\d+(?:\.\d+)?)\s*kg', peso_str)
        if match:
            return (Decimal(match.group(1)), Decimal(match.group(2)))
        
        # "+X kg" (sem limite máximo)
        match = re.match(r'\+(\d+(?:\.\d+)?)\s*kg', peso_str)
        if match:
            return (Decimal(match.group(1)), None)
        
        raise ValueError(f"Formato de peso não reconhecido: {peso_str}")

    def get_classe(self, nome_classe):
        """
        Mapeia nomes de classes para objetos Classe.
        Tenta diferentes variações do nome.
        """
        # Mapeamento de nomes
        mapeamento = {
            'SUB-9': ['SUB 9', 'SUB-9', 'SUB9'],
            'SUB-11': ['SUB 11', 'SUB-11', 'SUB11'],
            'SUB-13': ['SUB 13', 'SUB-13', 'SUB13'],
            'SUB-15': ['SUB 15', 'SUB-15', 'SUB15'],
            'SUB-18': ['SUB 18', 'SUB-18', 'SUB18'],
            'SÊNIOR/VET': ['SÊNIOR', 'SENIOR', 'VETERANOS', 'SÊNIOR/VET'],
        }
        
        # Buscar variações
        variacoes = mapeamento.get(nome_classe, [nome_classe])
        variacoes.append(nome_classe)  # Adicionar o nome original
        
        for variacao in variacoes:
            try:
                return Classe.objects.get(nome__iexact=variacao)
            except Classe.DoesNotExist:
                continue
        
        raise Classe.DoesNotExist(f"Classe '{nome_classe}' não encontrada. Variações tentadas: {variacoes}")

    def handle(self, *args, **options):
        categorias = [
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

        criadas = 0
        atualizadas = 0
        erros = 0

        for nome_classe, sexo, peso_str in categorias:
            try:
                # Buscar classe
                classe = self.get_classe(nome_classe)
                
                # Parsear peso
                limite_min, limite_max = self.parse_peso(peso_str)
                
                # Criar nome da categoria baseado no peso
                if limite_min == 0:
                    categoria_nome = f"Até {limite_max}kg"
                elif limite_max is None:
                    categoria_nome = f"+{limite_min}kg"
                else:
                    categoria_nome = f"+{limite_min} a {limite_max}kg"
                
                # Criar label
                if limite_max is None:
                    label = f"{classe.nome} - {sexo} - {categoria_nome}"
                else:
                    label = f"{classe.nome} - {sexo} - {categoria_nome}"
                
                # Criar ou atualizar categoria
                categoria, created = Categoria.objects.update_or_create(
                    classe=classe,
                    sexo=sexo,
                    categoria_nome=categoria_nome,
                    defaults={
                        'limite_min': limite_min,
                        'limite_max': limite_max,
                        'label': label
                    }
                )
                
                if created:
                    criadas += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Criada: {label}')
                    )
                else:
                    atualizadas += 1
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Atualizada: {label}')
                    )
                    
            except Classe.DoesNotExist as e:
                erros += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro: {e}')
                )
            except ValueError as e:
                erros += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro ao parsear peso "{peso_str}": {e}')
                )
            except Exception as e:
                erros += 1
                self.stdout.write(
                    self.style.ERROR(f'❌ Erro inesperado: {e}')
                )

        # Resumo
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Concluído! Criadas: {criadas}, Atualizadas: {atualizadas}, Erros: {erros}'
            )
        )

