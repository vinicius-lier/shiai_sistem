import json
from pathlib import Path
from django.core.management.base import BaseCommand
from atletas.models import Categoria


class Command(BaseCommand):
    help = 'Popula o banco de dados com as categorias oficiais de Judô'

    def handle(self, *args, **options):
        # Caminho do arquivo JSON
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        json_path = base_dir / 'categorias_oficiais_judo.json'
        
        if not json_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Arquivo {json_path} não encontrado!')
            )
            return
        
        # Ler o JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            categorias_data = json.load(f)
        
        criadas = 0
        atualizadas = 0
        
        # Processar cada categoria
        for cat_data in categorias_data:
            classe = cat_data['classe']
            categoria_nome = cat_data['categoria']
            limite_min = float(cat_data['limite_min'])
            limite_max = float(cat_data['limite_max']) if cat_data.get('limite_max') is not None else 999.0
            
            # Criar para Masculino e Feminino (sexo = "M/F" significa ambos)
            for sexo in ['M', 'F']:
                label = f"{classe} - {sexo} - {categoria_nome}"
                
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
                else:
                    atualizadas += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Processo concluído!\n'
                f'Categorias criadas: {criadas}\n'
                f'Categorias atualizadas: {atualizadas}\n'
                f'Total de categorias no sistema: {Categoria.objects.count()}'
            )
        )

