from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0008_inscricao_bloqueado_chave_alter_academia_organizador_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inscricao',
            name='peso',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True, verbose_name='Peso Oficial (kg)'),
        ),
        migrations.AlterField(
            model_name='inscricao',
            name='peso_informado',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=6, null=True, verbose_name='Peso Informado (kg)'),
        ),
        migrations.AlterField(
            model_name='pesagemhistorico',
            name='peso_registrado',
            field=models.DecimalField(decimal_places=1, max_digits=6, verbose_name='Peso Registrado (kg)'),
        ),
    ]

