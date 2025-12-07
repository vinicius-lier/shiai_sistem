from django.db import migrations


def populate_organizacao_slug(apps, schema_editor):
    Organizador = apps.get_model('atletas', 'Organizador')
    for organizacao in Organizador.objects.filter(slug__isnull=True):
        organizacao.save()


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0004_add_slug_organizador'),
    ]

    operations = [
        migrations.RunPython(populate_organizacao_slug, reverse_code=migrations.RunPython.noop),
    ]

