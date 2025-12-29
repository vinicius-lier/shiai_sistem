from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0011_popular_campos_normalizados'),
    ]

    operations = [
        migrations.CreateModel(
            name='GrupoFaixa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=60)),
                ('faixa_ordem_min', models.PositiveSmallIntegerField()),
                ('faixa_ordem_max', models.PositiveSmallIntegerField()),
            ],
        ),
    ]

