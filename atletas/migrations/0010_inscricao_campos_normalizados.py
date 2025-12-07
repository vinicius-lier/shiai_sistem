from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0009_decimal_peso_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='inscricao',
            name='classe_real',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inscricoes_classe_real', to='atletas.classe', verbose_name='Classe Real'),
        ),
        migrations.AddField(
            model_name='inscricao',
            name='categoria_real',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inscricoes_categoria_real', to='atletas.categoria', verbose_name='Categoria Real'),
        ),
        migrations.AddField(
            model_name='inscricao',
            name='peso_real',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Peso Real (kg)'),
        ),
        migrations.AddField(
            model_name='inscricao',
            name='status_atual',
            field=models.CharField(choices=[('pendente', 'Pendente'), ('inscrito', 'Inscrito'), ('aprovado', 'Aprovado'), ('remanejado', 'Remanejado'), ('desclassificado', 'Desclassificado')], db_index=True, default='pendente', max_length=20, verbose_name='Status Atual'),
        ),
    ]

