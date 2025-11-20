# Generated migration to adjust Evento fields

from django.db import migrations, models
from django.utils import timezone


def preencher_datas_eventos(apps, schema_editor):
    """Preenche datas faltantes com data padrão"""
    Evento = apps.get_model('eventos', 'Evento')
    
    # Preencher eventos sem data_evento
    eventos_sem_data = Evento.objects.filter(data_evento__isnull=True)
    data_padrao = timezone.now().date()
    eventos_sem_data.update(data_evento=data_padrao)
    
    # Preencher eventos sem data_limite_inscricao
    eventos_sem_limite = Evento.objects.filter(data_limite_inscricao__isnull=True)
    eventos_sem_limite.update(data_limite_inscricao=data_padrao)


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0009_adicionar_campos_evento'),
    ]

    operations = [
        # 1. Preencher datas faltantes
        migrations.RunPython(preencher_datas_eventos, migrations.RunPython.noop),
        
        # 2. Ajustar related_name de EventoParametro
        migrations.AlterField(
            model_name='eventoparametro',
            name='evento',
            field=models.OneToOneField(
                on_delete=models.CASCADE,
                related_name='parametros_config',
                to='eventos.evento'
            ),
        ),
        
        # 4. Tornar data_evento e data_limite_inscricao obrigatórios (após preencher)
        migrations.AlterField(
            model_name='evento',
            name='data_evento',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='evento',
            name='data_limite_inscricao',
            field=models.DateField(verbose_name='Prazo de Inscrição'),
        ),
    ]

