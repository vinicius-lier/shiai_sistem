from django.db import migrations, models
import django.db.models.deletion
import json


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0006_merge_0003_0005'),
    ]

    operations = [
        migrations.AddField(
            model_name='inscricao',
            name='categoria_calculada',
            field=models.CharField(blank=True, max_length=100, verbose_name='Categoria Calculada'),
        ),
        migrations.AddField(
            model_name='inscricao',
            name='peso_informado',
            field=models.FloatField(blank=True, null=True, verbose_name='Peso Informado (kg)'),
        ),
        migrations.AlterField(
            model_name='inscricao',
            name='status_inscricao',
            field=models.CharField(choices=[('pendente_pesagem', 'Pendente de Pesagem'), ('ok', 'OK'), ('remanejado', 'Remanejado'), ('desclassificado', 'Desclassificado'), ('pendente', 'Pendente'), ('confirmado', 'Confirmado'), ('aprovado', 'Aprovado'), ('reprovado', 'Reprovado')], default='pendente_pesagem', max_length=20, verbose_name='Status da Inscrição'),
        ),
        migrations.CreateModel(
            name='OcorrenciaAtleta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('REMANEJAMENTO', 'Remanejamento'), ('DESCLASSIFICACAO', 'Desclassificação')], max_length=30, verbose_name='Tipo')),
                ('motivo', models.CharField(blank=True, max_length=255, verbose_name='Motivo')),
                ('detalhes_json', models.JSONField(blank=True, default=dict, verbose_name='Detalhes')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('atleta', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ocorrencias_pesagem', to='atletas.atleta', verbose_name='Atleta')),
                ('campeonato', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ocorrencias_pesagem', to='atletas.campeonato', verbose_name='Campeonato')),
            ],
            options={
                'verbose_name': 'Ocorrência de Atleta',
                'verbose_name_plural': 'Ocorrências de Atletas',
                'ordering': ['-created_at'],
            },
        ),
    ]

