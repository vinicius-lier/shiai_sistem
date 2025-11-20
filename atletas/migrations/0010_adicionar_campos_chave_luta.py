# Generated manually to add new fields to Chave and Luta models

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0011_chave_evento'),
    ]

    operations = [
        # Adicionar campos ao modelo Chave
        migrations.AddField(
            model_name='chave',
            name='tipo_chave',
            field=models.CharField(blank=True, choices=[('MELHOR_DE_3', 'Melhor de 3 (2 atletas)'), ('CASADA_3', 'Lutas casadas para 3 atletas (A x B → Perdedor x C → Final)'), ('RODIZIO', 'Rodízio (3 a 5 atletas)'), ('ELIMINATORIA_SIMPLES', 'Eliminatória Simples'), ('ELIMINATORIA_REPESCAGEM', 'Eliminatória com Repescagem (modelo CBJ)'), ('OLIMPICA', 'Chave Olímpica (IJF)'), ('LIGA', 'Chave Liga (rodízio + semifinais)'), ('GRUPOS', 'Chave em Grupos (pools)')], max_length=30, null=True, verbose_name='Tipo de Chave'),
        ),
        migrations.AddField(
            model_name='chave',
            name='finalizada',
            field=models.BooleanField(default=False, verbose_name='Chave Finalizada'),
        ),
        migrations.AddField(
            model_name='chave',
            name='criada_em',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='chave',
            name='atualizada_em',
            field=models.DateTimeField(auto_now=True),
        ),
        # Adicionar campos ao modelo Luta
        migrations.AddField(
            model_name='luta',
            name='perdedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.CASCADE, related_name='lutas_perdidas', to='atletas.atleta'),
        ),
        migrations.AddField(
            model_name='luta',
            name='proxima_luta_repescagem',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='lutas_repescagem_anteriores', to='atletas.luta'),
        ),
        migrations.AddField(
            model_name='luta',
            name='tipo_luta',
            field=models.CharField(choices=[('NORMAL', 'Luta Normal'), ('REPESCAGEM', 'Repescagem'), ('BRONZE', 'Disputa de Bronze'), ('FINAL', 'Final')], default='NORMAL', max_length=20),
        ),
        migrations.AddField(
            model_name='luta',
            name='wo_atleta_a',
            field=models.BooleanField(default=False, verbose_name='WO Atleta A'),
        ),
        migrations.AddField(
            model_name='luta',
            name='wo_atleta_b',
            field=models.BooleanField(default=False, verbose_name='WO Atleta B'),
        ),
        migrations.AddField(
            model_name='luta',
            name='observacoes',
            field=models.TextField(blank=True, verbose_name='Observações'),
        ),
        # Atualizar TIPO_VITORIA_CHOICES para incluir WO e DESCLASSIFICADO
        migrations.AlterField(
            model_name='luta',
            name='tipo_vitoria',
            field=models.CharField(blank=True, choices=[('IPPON', 'Ippon'), ('WAZARI', 'Wazari'), ('WAZARI_WAZARI', 'Wazari-Wazari'), ('YUKO', 'Yuko'), ('WO', 'W.O. (Walkover)'), ('DESCLASSIFICADO', 'Desclassificado')], max_length=20),
        ),
        # Alterar campo proxima_luta de IntegerField para ForeignKey
        # Primeiro remover o campo antigo (IntegerField)
        migrations.RemoveField(
            model_name='luta',
            name='proxima_luta',
        ),
        # Depois adicionar o novo campo (ForeignKey)
        migrations.AddField(
            model_name='luta',
            name='proxima_luta',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='lutas_anteriores', to='atletas.luta'),
        ),
    ]

