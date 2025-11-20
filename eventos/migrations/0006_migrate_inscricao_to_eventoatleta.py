# Generated migration to migrate data from Inscricao to EventoAtleta
from django.db import migrations


def migrate_inscricao_to_eventoatleta(apps, schema_editor):
    """Migra dados de Inscricao para EventoAtleta"""
    Inscricao = apps.get_model('eventos', 'Inscricao')
    EventoAtleta = apps.get_model('eventos', 'EventoAtleta')
    Categoria = apps.get_model('atletas', 'Categoria')
    
    # Migrar todos os registros de Inscricao para EventoAtleta
    for inscricao in Inscricao.objects.all():
        # Buscar categoria se categoria_ajustada existir
        categoria = None
        if inscricao.categoria_ajustada:
            categoria = Categoria.objects.filter(
                categoria_nome=inscricao.categoria_ajustada,
                classe=inscricao.atleta.classe,
                sexo=inscricao.atleta.sexo
            ).first()
        
        # Criar EventoAtleta
        evento_atleta = EventoAtleta.objects.create(
            evento=inscricao.evento,
            atleta=inscricao.atleta,
            academia=inscricao.academia,
            inscrito_por=inscricao.inscrito_por,
            data_inscricao=inscricao.data_inscricao,
            observacao=inscricao.observacao,
            peso_oficial=inscricao.peso_oficial,
            categoria=categoria,
            categoria_ajustada=inscricao.categoria_ajustada,
            status_pesagem=inscricao.status_pesagem,
            valor_inscricao=inscricao.valor_inscricao or 0,
        )
        
        # Mapear status antigo para novo
        if inscricao.status == 'Pesado':
            evento_atleta.status = 'OK'
        elif inscricao.status == 'Remanejado':
            evento_atleta.status = 'REMANEJADO'
            evento_atleta.remanejado = True
        elif inscricao.status == 'Desclassificado':
            evento_atleta.status = 'DESCLASSIFICADO'
            evento_atleta.desclassificado = True
        else:
            evento_atleta.status = 'PENDENTE'
        
        evento_atleta.save()


def reverse_migrate(apps, schema_editor):
    """Reverter migração (não implementado - dados já migrados)"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('eventos', '0005_eventoatleta_delete_inscricao'),
        ('atletas', '0010_atleta_federado_atleta_zempo'),
    ]

    operations = [
        migrations.RunPython(migrate_inscricao_to_eventoatleta, reverse_migrate),
        migrations.DeleteModel(
            name='Inscricao',
        ),
    ]

