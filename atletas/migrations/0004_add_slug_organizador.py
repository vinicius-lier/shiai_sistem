from django.db import migrations, models
from django.utils.text import slugify


def gerar_slugs(apps, schema_editor):
    Organizador = apps.get_model('atletas', 'Organizador')
    for org in Organizador.objects.all():
        if org.slug:
            continue
        base = slugify(org.nome)[:60] or 'organizacao'
        slug = base
        contador = 1
        while Organizador.objects.filter(slug=slug).exclude(pk=org.pk).exists():
            contador += 1
            slug = f"{base[:50]}-{contador}"
        org.slug = slug
        org.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizador',
            name='slug',
            field=models.SlugField(blank=True, help_text='Identificador curto usado na URL (ex: "liga-paulista"). Se vazio, será gerado automaticamente a partir do nome.', max_length=80, null=True, unique=True, verbose_name='Slug da Organização'),
        ),
        migrations.RunPython(gerar_slugs, reverse_code=migrations.RunPython.noop),
    ]


