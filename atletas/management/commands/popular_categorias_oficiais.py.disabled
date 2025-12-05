from django.core.management.base import BaseCommand
from atletas.models import Categoria


class Command(BaseCommand):
    help = 'Popula o banco de dados com as categorias oficiais de Judô baseadas nas tabelas fornecidas'

    def handle(self, *args, **options):
        # Dados das tabelas fornecidas
        
        # CATEGORIAS MASCULINAS
        categorias_masculinas = [
            # SUB-9
            {'classe': 'SUB 9', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 23.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Leve', 'limite_min': 23.0, 'limite_max': 26.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Meio Leve', 'limite_min': 26.0, 'limite_max': 29.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Leve', 'limite_min': 29.0, 'limite_max': 32.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Meio Médio', 'limite_min': 32.0, 'limite_max': 36.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Médio', 'limite_min': 36.0, 'limite_max': 40.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Meio Pesado', 'limite_min': 40.0, 'limite_max': 45.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Pesado', 'limite_min': 45.0, 'limite_max': 50.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Super Pesado', 'limite_min': 50.0, 'limite_max': 999.0},
            
            # SUB-11
            {'classe': 'SUB 11', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 26.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Leve', 'limite_min': 26.0, 'limite_max': 28.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Meio Leve', 'limite_min': 28.0, 'limite_max': 30.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Leve', 'limite_min': 30.0, 'limite_max': 33.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Meio Médio', 'limite_min': 33.0, 'limite_max': 36.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Médio', 'limite_min': 36.0, 'limite_max': 40.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Meio Pesado', 'limite_min': 40.0, 'limite_max': 45.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Pesado', 'limite_min': 45.0, 'limite_max': 50.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Super Pesado', 'limite_min': 50.0, 'limite_max': 999.0},
            
            # SUB-13
            {'classe': 'SUB 13', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 28.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Leve', 'limite_min': 28.0, 'limite_max': 31.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Meio Leve', 'limite_min': 31.0, 'limite_max': 34.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Leve', 'limite_min': 34.0, 'limite_max': 38.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Meio Médio', 'limite_min': 38.0, 'limite_max': 42.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Médio', 'limite_min': 42.0, 'limite_max': 47.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Meio Pesado', 'limite_min': 47.0, 'limite_max': 52.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Pesado', 'limite_min': 52.0, 'limite_max': 60.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Super Pesado', 'limite_min': 60.0, 'limite_max': 999.0},
            
            # SUB-15 (Masculino - pesos diferentes do feminino)
            {'classe': 'SUB 15', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 40.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Leve', 'limite_min': 40.0, 'limite_max': 45.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Meio Leve', 'limite_min': 45.0, 'limite_max': 50.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Leve', 'limite_min': 50.0, 'limite_max': 55.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Meio Médio', 'limite_min': 55.0, 'limite_max': 60.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Médio', 'limite_min': 60.0, 'limite_max': 66.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Meio Pesado', 'limite_min': 66.0, 'limite_max': 73.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Pesado', 'limite_min': 73.0, 'limite_max': 81.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Super Pesado', 'limite_min': 81.0, 'limite_max': 999.0},
            
            # SUB-18 (Masculino - pesos diferentes do feminino)
            {'classe': 'SUB 18', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 50.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Leve', 'limite_min': 50.0, 'limite_max': 55.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Meio Leve', 'limite_min': 55.0, 'limite_max': 60.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Leve', 'limite_min': 60.0, 'limite_max': 66.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Meio Médio', 'limite_min': 66.0, 'limite_max': 73.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Médio', 'limite_min': 73.0, 'limite_max': 81.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Meio Pesado', 'limite_min': 81.0, 'limite_max': 90.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Pesado', 'limite_min': 90.0, 'limite_max': 999.0},
            
            # SÊNIOR (Masculino - pesos diferentes do feminino)
            {'classe': 'SÊNIOR', 'categoria_nome': 'Leve', 'limite_min': 0.0, 'limite_max': 60.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Meio Leve', 'limite_min': 60.0, 'limite_max': 66.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Leve', 'limite_min': 66.0, 'limite_max': 73.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Meio Médio', 'limite_min': 73.0, 'limite_max': 81.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Médio', 'limite_min': 81.0, 'limite_max': 90.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Meio Pesado', 'limite_min': 90.0, 'limite_max': 100.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Pesado', 'limite_min': 100.0, 'limite_max': 999.0},
            
            # VETERANOS (Masculino - mesmos limites de peso que SÊNIOR)
            {'classe': 'VETERANOS', 'categoria_nome': 'Leve', 'limite_min': 0.0, 'limite_max': 60.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Meio Leve', 'limite_min': 60.0, 'limite_max': 66.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Leve', 'limite_min': 66.0, 'limite_max': 73.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Meio Médio', 'limite_min': 73.0, 'limite_max': 81.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Médio', 'limite_min': 81.0, 'limite_max': 90.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Meio Pesado', 'limite_min': 90.0, 'limite_max': 100.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Pesado', 'limite_min': 100.0, 'limite_max': 999.0},
        ]
        
        # CATEGORIAS FEMININAS
        categorias_femininas = [
            # SUB-9
            {'classe': 'SUB 9', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 23.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Leve', 'limite_min': 23.0, 'limite_max': 26.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Meio Leve', 'limite_min': 26.0, 'limite_max': 29.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Leve', 'limite_min': 29.0, 'limite_max': 32.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Meio Médio', 'limite_min': 32.0, 'limite_max': 36.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Médio', 'limite_min': 36.0, 'limite_max': 40.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Meio Pesado', 'limite_min': 40.0, 'limite_max': 45.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Pesado', 'limite_min': 45.0, 'limite_max': 50.0},
            {'classe': 'SUB 9', 'categoria_nome': 'Super Pesado', 'limite_min': 50.0, 'limite_max': 999.0},
            
            # SUB-11
            {'classe': 'SUB 11', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 26.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Leve', 'limite_min': 26.0, 'limite_max': 28.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Meio Leve', 'limite_min': 28.0, 'limite_max': 30.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Leve', 'limite_min': 30.0, 'limite_max': 33.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Meio Médio', 'limite_min': 33.0, 'limite_max': 36.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Médio', 'limite_min': 36.0, 'limite_max': 40.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Meio Pesado', 'limite_min': 40.0, 'limite_max': 45.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Pesado', 'limite_min': 45.0, 'limite_max': 50.0},
            {'classe': 'SUB 11', 'categoria_nome': 'Super Pesado', 'limite_min': 50.0, 'limite_max': 999.0},
            
            # SUB-13
            {'classe': 'SUB 13', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 28.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Leve', 'limite_min': 28.0, 'limite_max': 31.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Meio Leve', 'limite_min': 31.0, 'limite_max': 34.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Leve', 'limite_min': 34.0, 'limite_max': 38.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Meio Médio', 'limite_min': 38.0, 'limite_max': 42.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Médio', 'limite_min': 42.0, 'limite_max': 47.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Meio Pesado', 'limite_min': 47.0, 'limite_max': 52.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Pesado', 'limite_min': 52.0, 'limite_max': 60.0},
            {'classe': 'SUB 13', 'categoria_nome': 'Super Pesado', 'limite_min': 60.0, 'limite_max': 999.0},
            
            # SUB-15 (Feminino - pesos diferentes do masculino)
            {'classe': 'SUB 15', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 36.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Leve', 'limite_min': 36.0, 'limite_max': 40.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Meio Leve', 'limite_min': 40.0, 'limite_max': 44.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Leve', 'limite_min': 44.0, 'limite_max': 48.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Meio Médio', 'limite_min': 48.0, 'limite_max': 52.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Médio', 'limite_min': 52.0, 'limite_max': 57.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Meio Pesado', 'limite_min': 57.0, 'limite_max': 63.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Pesado', 'limite_min': 63.0, 'limite_max': 70.0},
            {'classe': 'SUB 15', 'categoria_nome': 'Super Pesado', 'limite_min': 70.0, 'limite_max': 999.0},
            
            # SUB-18 (Feminino - pesos diferentes do masculino)
            {'classe': 'SUB 18', 'categoria_nome': 'Super Leve', 'limite_min': 0.0, 'limite_max': 40.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Leve', 'limite_min': 40.0, 'limite_max': 44.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Meio Leve', 'limite_min': 44.0, 'limite_max': 48.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Leve', 'limite_min': 48.0, 'limite_max': 52.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Meio Médio', 'limite_min': 52.0, 'limite_max': 57.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Médio', 'limite_min': 57.0, 'limite_max': 63.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Meio Pesado', 'limite_min': 63.0, 'limite_max': 70.0},
            {'classe': 'SUB 18', 'categoria_nome': 'Pesado', 'limite_min': 70.0, 'limite_max': 999.0},
            
            # SÊNIOR (Feminino - pesos diferentes do masculino)
            {'classe': 'SÊNIOR', 'categoria_nome': 'Leve', 'limite_min': 0.0, 'limite_max': 48.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Meio Leve', 'limite_min': 48.0, 'limite_max': 52.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Leve', 'limite_min': 52.0, 'limite_max': 57.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Meio Médio', 'limite_min': 57.0, 'limite_max': 63.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Médio', 'limite_min': 63.0, 'limite_max': 70.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Meio Pesado', 'limite_min': 70.0, 'limite_max': 78.0},
            {'classe': 'SÊNIOR', 'categoria_nome': 'Pesado', 'limite_min': 78.0, 'limite_max': 999.0},
            
            # VETERANOS (Feminino - mesmos limites de peso que SÊNIOR feminino)
            {'classe': 'VETERANOS', 'categoria_nome': 'Leve', 'limite_min': 0.0, 'limite_max': 48.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Meio Leve', 'limite_min': 48.0, 'limite_max': 52.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Leve', 'limite_min': 52.0, 'limite_max': 57.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Meio Médio', 'limite_min': 57.0, 'limite_max': 63.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Médio', 'limite_min': 63.0, 'limite_max': 70.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Meio Pesado', 'limite_min': 70.0, 'limite_max': 78.0},
            {'classe': 'VETERANOS', 'categoria_nome': 'Pesado', 'limite_min': 78.0, 'limite_max': 999.0},
        ]
        
        criadas = 0
        atualizadas = 0
        
        # Processar categorias masculinas
        for cat_data in categorias_masculinas:
            label = f"{cat_data['classe']} - {cat_data['categoria_nome']}"
            
            # Usar limite_min e limite_max como parte da chave única para evitar conflito com categorias de mesmo nome
            categoria, created = Categoria.objects.update_or_create(
                classe=cat_data['classe'],
                sexo='M',
                categoria_nome=cat_data['categoria_nome'],
                limite_min=cat_data['limite_min'],
                limite_max=cat_data['limite_max'],
                defaults={
                    'label': label
                }
            )
            
            if created:
                criadas += 1
            else:
                atualizadas += 1
        
        # Processar categorias femininas
        for cat_data in categorias_femininas:
            label = f"{cat_data['classe']} - {cat_data['categoria_nome']}"
            
            # Usar limite_min e limite_max como parte da chave única para evitar conflito com categorias de mesmo nome
            categoria, created = Categoria.objects.update_or_create(
                classe=cat_data['classe'],
                sexo='F',
                categoria_nome=cat_data['categoria_nome'],
                limite_min=cat_data['limite_min'],
                limite_max=cat_data['limite_max'],
                defaults={
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

