from django.contrib import admin
from .models import Evento, EventoParametro, EventoAtleta


@admin.register(Evento)
class EventoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'data_evento', 'local', 'ativo', 'total_inscritos', 'inscricoes_abertas']
    list_filter = ['ativo', 'data_evento']
    search_fields = ['nome', 'local']
    date_hierarchy = 'data_evento'


@admin.register(EventoParametro)
class EventoParametroAdmin(admin.ModelAdmin):
    list_display = ['evento', 'idade_min', 'idade_max', 'usar_pesagem', 'permitir_festival']
    list_filter = ['usar_pesagem', 'permitir_festival']


@admin.register(EventoAtleta)
class EventoAtletaAdmin(admin.ModelAdmin):
    list_display = ['atleta', 'evento', 'academia', 'status', 'data_inscricao', 'peso_oficial', 'categoria', 'pontos_evento']
    list_filter = ['evento', 'academia', 'status', 'status_pesagem', 'remanejado', 'desclassificado']
    search_fields = ['atleta__nome', 'evento__nome', 'academia__nome']
    date_hierarchy = 'data_inscricao'
    readonly_fields = ('data_inscricao',)
