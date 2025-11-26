from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.utils import OperationalError

from atletas.models import Atleta, Chave, Luta, Academia, AcademiaPontuacao


class Command(BaseCommand):
    help = (
        "Apaga completamente todos os dados de atletas, chaves e pontuações. "
        "Este comando remove: todas as lutas, todas as chaves, todos os atletas, "
        "todas as pontuações de academias e reseta os pontos das academias para 0."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Confirma que você realmente deseja apagar todos os dados',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Exibe informações detalhadas durante a execução',
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        
        if not options['confirmar']:
            # Mostrar resumo do que será apagado
            total_lutas = Luta.objects.count()
            total_chaves = Chave.objects.count()
            total_atletas = Atleta.objects.count()
            total_pontuacoes = AcademiaPontuacao.objects.count()
            total_academias = Academia.objects.count()
            
            separador = "=" * 60
            self.stdout.write(
                self.style.WARNING(
                    f"\n{separador}\n"
                    f"ATENÇÃO: Este comando irá apagar TODOS os dados!\n"
                    f"{separador}\n"
                )
            )
            
            if total_lutas > 0 or total_chaves > 0 or total_atletas > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\nDados que serão apagados:\n"
                        f"  - {total_lutas} lutas\n"
                        f"  - {total_chaves} chaves\n"
                        f"  - {total_atletas} atletas\n"
                        f"  - {total_pontuacoes} registros de pontuação\n"
                        f"  - Pontos de {total_academias} academias serão resetados\n"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\nNenhum dado encontrado para apagar.\n")
                )
            
            self.stdout.write(
                self.style.WARNING(
                    "\nPara confirmar, execute novamente com a opção --confirmar\n"
                    "Exemplo: python manage.py apagar_dados_atletas_chaves_pontuacoes --confirmar\n"
                )
            )
            return

        try:
            with transaction.atomic():
                # Contar registros antes de apagar
                total_lutas = Luta.objects.count()
                total_chaves = Chave.objects.count()
                total_atletas = Atleta.objects.count()
                total_pontuacoes = AcademiaPontuacao.objects.count()
                total_academias = Academia.objects.count()

                if verbose:
                    self.stdout.write("\nIniciando processo de exclusão...\n")

                # Verificar se há dados para apagar
                if total_lutas == 0 and total_chaves == 0 and total_atletas == 0:
                    self.stdout.write(
                        self.style.SUCCESS("\nNenhum dado encontrado para apagar. Banco de dados já está limpo.\n")
                    )
                    return

                # 1. Apagar todas as lutas primeiro (devido às foreign keys)
                if total_lutas > 0:
                    if verbose:
                        self.stdout.write(f"[1/5] Apagando {total_lutas} lutas...")
                    Luta.objects.all().delete()
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"    ✓ {total_lutas} lutas apagadas"))
                elif verbose:
                    self.stdout.write("[1/5] Nenhuma luta encontrada")

                # 2. Apagar todas as chaves (isso também remove as relações ManyToMany)
                if total_chaves > 0:
                    if verbose:
                        self.stdout.write(f"[2/5] Apagando {total_chaves} chaves...")
                    Chave.objects.all().delete()
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"    ✓ {total_chaves} chaves apagadas"))
                elif verbose:
                    self.stdout.write("[2/5] Nenhuma chave encontrada")

                # 3. Apagar todos os atletas
                if total_atletas > 0:
                    if verbose:
                        self.stdout.write(f"[3/5] Apagando {total_atletas} atletas...")
                    Atleta.objects.all().delete()
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"    ✓ {total_atletas} atletas apagados"))
                elif verbose:
                    self.stdout.write("[3/5] Nenhum atleta encontrado")

                # 4. Apagar todas as pontuações de academias
                if total_pontuacoes > 0:
                    if verbose:
                        self.stdout.write(f"[4/5] Apagando {total_pontuacoes} registros de pontuação...")
                    AcademiaPontuacao.objects.all().delete()
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f"    ✓ {total_pontuacoes} pontuações apagadas"))
                elif verbose:
                    self.stdout.write("[4/5] Nenhuma pontuação encontrada")

                # 5. Resetar pontos de todas as academias para 0
                if total_academias > 0:
                    academias_com_pontos = Academia.objects.exclude(pontos=0).count()
                    if academias_com_pontos > 0:
                        if verbose:
                            self.stdout.write(f"[5/5] Resetando pontos de {total_academias} academias...")
                        Academia.objects.all().update(pontos=0)
                        if verbose:
                            self.stdout.write(self.style.SUCCESS(f"    ✓ Pontos de {total_academias} academias resetados"))
                    elif verbose:
                        self.stdout.write(f"[5/5] {total_academias} academias encontradas, mas nenhuma tinha pontos")

            # Resumo final
            separador = "=" * 60
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n{separador}\n"
                    f"✓ Operação concluída com sucesso!\n"
                    f"{separador}\n"
                    f"  • {total_lutas} lutas apagadas\n"
                    f"  • {total_chaves} chaves apagadas\n"
                    f"  • {total_atletas} atletas apagados\n"
                    f"  • {total_pontuacoes} pontuações apagadas\n"
                    f"  • {total_academias} academias tiveram pontos resetados\n"
                )
            )

        except OperationalError as e:
            self.stdout.write(
                self.style.ERROR(
                    f"\nErro de banco de dados: {str(e)}\n"
                    "Verifique se o banco de dados está acessível e tente novamente."
                )
            )
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"\nErro inesperado durante a operação: {str(e)}\n"
                    "A transação foi revertida. Nenhum dado foi alterado."
                )
            )
            raise

