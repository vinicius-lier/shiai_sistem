from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0004_add_slug_organizador'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='organizador',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=models.SET_NULL, related_name='organizadores_dono', to=settings.AUTH_USER_MODEL, verbose_name='Dono (superuser)'),
        ),
        migrations.AlterField(
            model_name='organizador',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, verbose_name='E-mail'),
        ),
    ]

