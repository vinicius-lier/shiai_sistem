from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0012_grupofaixa'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conferenciapagamento',
            name='conferido_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='conferencias_realizadas', to=settings.AUTH_USER_MODEL, verbose_name='Conferido por'),
        ),
        migrations.AlterField(
            model_name='historicosistema',
            name='usuario',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='historico_acoes', to=settings.AUTH_USER_MODEL, verbose_name='Usuário'),
        ),
        migrations.AlterField(
            model_name='ocorrencia',
            name='registrado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='ocorrencias_registradas', to=settings.AUTH_USER_MODEL, verbose_name='Registrado por'),
        ),
        migrations.AlterField(
            model_name='ocorrencia',
            name='responsavel_resolucao',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='ocorrencias_responsavel', to=settings.AUTH_USER_MODEL, verbose_name='Responsável pela Resolução'),
        ),
        migrations.AlterField(
            model_name='pagamento',
            name='validado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='pagamentos_validados', to=settings.AUTH_USER_MODEL, verbose_name='Validado por'),
        ),
        migrations.AlterField(
            model_name='pesagemhistorico',
            name='pesado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='pesagens_realizadas', to=settings.AUTH_USER_MODEL, verbose_name='Pesado por'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=models.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='usuariooperacional',
            name='criado_por',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='usuarios_criados', to=settings.AUTH_USER_MODEL, verbose_name='Criado Por'),
        ),
        migrations.AlterField(
            model_name='usuariooperacional',
            name='user',
            field=models.OneToOneField(on_delete=models.CASCADE, related_name='perfil_operacional', to=settings.AUTH_USER_MODEL, verbose_name='Usuário'),
        ),
    ]

