# Generated migration to make evento required in Chave and Luta

from django.db import migrations, models
import django.db.models.deletion


def preencher_evento_chaves(apps, schema_editor):
    """Preenche evento das chaves sem evento usando evento mais recente ou cria um padrão"""
    Chave = apps.get_model('atletas', 'Chave')
    Evento = apps.get_model('eventos', 'Evento')
    Luta = apps.get_model('atletas', 'Luta')
    
    # Buscar chaves sem evento
    chaves_sem_evento = Chave.objects.filter(evento__isnull=True)
    
    if chaves_sem_evento.exists():
        # Tentar usar evento mais recente
        evento_padrao = Evento.objects.order_by('-data_evento').first()
        
        if evento_padrao:
            # Vincular todas as chaves sem evento ao evento mais recente
            chaves_sem_evento.update(evento=evento_padrao)
        else:
            # Se não há evento, criar um padrão temporário
            evento_padrao = Evento.objects.create(
                nome='Evento Migração (Chaves Antigas)',
                descricao='Evento criado automaticamente para migração de chaves antigas',
                ativo=True,
                status='ENCERRADO'
            )
            chaves_sem_evento.update(evento=evento_padrao)


def preencher_evento_lutas(apps, schema_editor):
    """Preenche evento das lutas com evento da chave"""
    Luta = apps.get_model('atletas', 'Luta')
    
    # Preencher evento das lutas com evento da chave
    for luta in Luta.objects.filter(evento__isnull=True):
        if luta.chave and luta.chave.evento:
            luta.evento = luta.chave.evento
            luta.save()


class Migration(migrations.Migration):

    dependencies = [
        ('atletas', '0011_chave_evento'),
        ('eventos', '0009_adicionar_campos_evento'),
    ]

    operations = [
        # 1. Preencher evento das chaves existentes que estão sem evento
        migrations.RunPython(preencher_evento_chaves, migrations.RunPython.noop),
        
        # 2. Adicionar campo evento em Luta (nullable temporariamente)
        migrations.AddField(
            model_name='luta',
            name='evento',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='lutas',
                to='eventos.evento',
                verbose_name='Evento'
            ),
        ),
        
        # 3. Preencher evento das lutas existentes
        migrations.RunPython(preencher_evento_lutas, migrations.RunPython.noop),
        
        # 4. Tornar evento obrigatório em Chave (remover null=True, blank=True)
        migrations.AlterField(
            model_name='chave',
            name='evento',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='chaves',
                to='eventos.evento',
                verbose_name='Evento'
            ),
        ),
        
        # 4. Tornar evento obrigatório em Luta (remover null=True, blank=True)
        migrations.AlterField(
            model_name='luta',
            name='evento',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='lutas',
                to='eventos.evento',
                verbose_name='Evento'
            ),
        ),
        
        # 5. Adicionar índices para performance
        migrations.AddIndex(
            model_name='luta',
            index=models.Index(fields=['evento', 'chave'], name='atletas_lut_evento_c_idx'),
        ),
        migrations.AddIndex(
            model_name='luta',
            index=models.Index(fields=['evento', 'round'], name='atletas_lut_evento_r_idx'),
        ),
    ]

