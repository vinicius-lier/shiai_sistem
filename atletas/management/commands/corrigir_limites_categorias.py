"""Comando para corrigir limites de categorias de todos os atletas"""
from django.core.management.base import BaseCommand
from atletas.models import Atleta, Categoria


class Command(BaseCommand):
    help = 'Corrige os limites de categoria de todos os atletas baseado na categoria atual'

    def handle(self, *args, **options):
        atletas = Atleta.objects.all()
        corrigidos = 0
        erros = []
        
        for atleta in atletas:
            # Determinar qual categoria usar (ajustada ou original)
            categoria_nome = atleta.categoria_ajustada if atleta.categoria_ajustada else atleta.categoria_nome
            
            # Buscar categoria no banco
            categoria = Categoria.objects.filter(
                classe=atleta.classe,
                sexo=atleta.sexo,
                categoria_nome=categoria_nome
            ).first()
            
            if categoria:
                # Calcular limite correto
                if categoria.limite_max < 999.0:
                    limite_correto = f"{categoria.limite_min} a {categoria.limite_max} kg"
                else:
                    limite_correto = f"{categoria.limite_min} kg ou mais"
                
                # Verificar se precisa atualizar
                if atleta.categoria_limite != limite_correto:
                    atleta.categoria_limite = limite_correto
                    atleta.save()
                    corrigidos += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Corrigido: {atleta.nome} - {categoria_nome}: {limite_correto}'
                        )
                    )
            else:
                erros.append(f'{atleta.nome} - Categoria "{categoria_nome}" não encontrada')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Total corrigido: {corrigidos} atletas'))
        if erros:
            self.stdout.write(self.style.WARNING(f'\n⚠️  Erros: {len(erros)}'))
            for erro in erros:
                self.stdout.write(self.style.ERROR(f'  - {erro}'))



