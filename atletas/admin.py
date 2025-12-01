from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
from .models import Academia, Categoria, Atleta, Chave, Luta, AdminLog, Inscricao, Campeonato, EquipeTecnicaCampeonato, PessoaEquipeTecnica, PesagemHistorico


@admin.register(Academia)
class AcademiaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cidade', 'estado', 'pontos')
    list_filter = ('estado',)
    search_fields = ('nome', 'cidade')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('label', 'classe', 'sexo', 'limite_min', 'limite_max')
    list_filter = ('classe', 'sexo')
    search_fields = ('label', 'categoria_nome')


@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'idade', 'sexo', 'data_nascimento', 'academia', 'status_ativo', 'tem_documento_display')
    list_filter = ('sexo', 'status_ativo', 'federado', 'academia')
    search_fields = ('nome', 'academia__nome', 'numero_zempo')
    readonly_fields = ('idade', 'data_cadastro', 'data_atualizacao', 'documento_preview')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'data_nascimento', 'sexo', 'academia', 'classe_inicial')
        }),
        ('Documento', {
            'fields': ('documento_oficial', 'documento_preview')
        }),
        ('Informações Adicionais', {
            'fields': ('federado', 'numero_zempo', 'faixa')
        }),
        ('Equipe Técnica', {
            'fields': ('pode_ser_equipe_tecnica', 'funcao_equipe_tecnica', 'telefone', 'chave_pix'),
            'description': 'Marque se esta pessoa pode fazer parte da equipe técnica em eventos. Chave PIX é obrigatória para pagamento.'
        }),
        ('Status', {
            'fields': ('status_ativo',)
        }),
        ('Auditoria', {
            'fields': ('data_cadastro', 'data_atualizacao', 'idade'),
            'classes': ('collapse',)
        }),
    )
    
    def tem_documento_display(self, obj):
        if obj.tem_documento():
            return format_html('<span style="color: green;">✓ Documento</span>')
        return format_html('<span style="color: red;">✗ Sem documento</span>')
    tem_documento_display.short_description = 'Documento'
    
    def documento_preview(self, obj):
        if obj.documento_oficial:
            url = obj.documento_oficial.url
            return format_html('<a href="{}" target="_blank">Ver documento</a>', url)
        return "Nenhum documento"
    documento_preview.short_description = 'Visualizar'


@admin.register(Inscricao)
class InscricaoAdmin(admin.ModelAdmin):
    list_display = ('atleta', 'campeonato', 'classe_escolhida', 'categoria_escolhida', 'status_inscricao', 'peso', 'data_inscricao')
    list_filter = ('campeonato', 'classe_escolhida', 'status_inscricao', 'remanejado')
    search_fields = ('atleta__nome', 'campeonato__nome')
    readonly_fields = ('data_inscricao', 'data_pesagem')
    date_hierarchy = 'data_inscricao'


@admin.register(Campeonato)
class CampeonatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'data_competicao', 'data_limite_inscricao', 'ativo', 'get_total_inscricoes')
    list_filter = ('ativo',)
    search_fields = ('nome',)
    
    def get_total_inscricoes(self, obj):
        return obj.inscricoes.count()
    get_total_inscricoes.short_description = 'Total de Inscrições'


@admin.register(Chave)
class ChaveAdmin(admin.ModelAdmin):
    list_display = ('classe', 'sexo', 'categoria', 'get_num_atletas')
    list_filter = ('classe', 'sexo')
    filter_horizontal = ('atletas',)
    
    def get_num_atletas(self, obj):
        return obj.atletas.count()
    get_num_atletas.short_description = 'Nº Atletas'


@admin.register(Luta)
class LutaAdmin(admin.ModelAdmin):
    list_display = ('chave', 'round', 'atleta_a', 'atleta_b', 'vencedor', 'concluida', 'tipo_vitoria', 'pontos_vencedor')
    list_filter = ('chave', 'round', 'concluida', 'tipo_vitoria')
    search_fields = ('atleta_a__nome', 'atleta_b__nome', 'vencedor__nome')


@admin.register(PessoaEquipeTecnica)
class PessoaEquipeTecnicaAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'telefone', 'chave_pix', 'e_atleta_display', 'ativo', 'data_cadastro')
    list_filter = ('ativo', 'atleta', 'data_cadastro')
    search_fields = ('nome', 'atleta__nome', 'telefone', 'chave_pix')
    readonly_fields = ('data_cadastro', 'nome_completo', 'e_atleta_display')
    date_hierarchy = 'data_cadastro'
    
    def e_atleta_display(self, obj):
        return 'Sim' if obj.e_atleta else 'Não'
    e_atleta_display.short_description = 'É Atleta'


@admin.register(EquipeTecnicaCampeonato)
class EquipeTecnicaCampeonatoAdmin(admin.ModelAdmin):
    list_display = ('pessoa', 'campeonato', 'funcao', 'funcao_customizada', 'ativo', 'data_vinculacao')
    list_filter = ('campeonato', 'funcao', 'ativo', 'data_vinculacao')
    search_fields = ('pessoa__nome', 'pessoa__atleta__nome', 'campeonato__nome', 'funcao_customizada')
    readonly_fields = ('data_vinculacao',)
    date_hierarchy = 'data_vinculacao'


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'acao', 'usuario_ip')
    list_filter = ('data_hora', 'acao')
    search_fields = ('acao', 'usuario_ip')
    readonly_fields = ('data_hora', 'acao', 'usuario_ip')
    
    def has_add_permission(self, request):
        return False


@admin.register(PesagemHistorico)
class PesagemHistoricoAdmin(admin.ModelAdmin):
    list_display = ('inscricao', 'campeonato', 'peso_registrado', 'pesado_por', 'data_hora')
    list_filter = ('campeonato', 'data_hora', 'pesado_por')
    search_fields = ('inscricao__atleta__nome', 'campeonato__nome', 'observacoes')
    readonly_fields = ('data_hora',)
    date_hierarchy = 'data_hora'
    ordering = ['-data_hora']


class JudoAdminSite(admin.AdminSite):
    site_header = "Administração - Sistema de Judô"
    site_title = "Admin Judô"
    index_title = "Painel Administrativo"

admin_site = JudoAdminSite(name='judocomp_admin')