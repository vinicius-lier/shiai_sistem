from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse
<<<<<<< HEAD
from .models import Academia, Categoria, Atleta, Chave, Luta, AdminLog, Inscricao, Campeonato
=======
from .models import Academia, Categoria, Atleta, Chave, Luta, AdminLog
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17


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
<<<<<<< HEAD
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
            'fields': ('federado', 'numero_zempo')
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
=======
    list_display = ('nome', 'idade', 'sexo', 'classe', 'categoria_nome', 'academia', 'status', 'peso_oficial')
    list_filter = ('classe', 'sexo', 'status', 'academia')
    search_fields = ('nome', 'academia__nome')
    readonly_fields = ('idade',)
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17


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


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'acao', 'usuario_ip')
    list_filter = ('data_hora', 'acao')
    search_fields = ('acao', 'usuario_ip')
    readonly_fields = ('data_hora', 'acao', 'usuario_ip')
    
    def has_add_permission(self, request):
        return False


class JudoAdminSite(admin.AdminSite):
    site_header = "Administração - Sistema de Judô"
    site_title = "Admin Judô"
    index_title = "Painel Administrativo"

admin_site = JudoAdminSite(name='judocomp_admin')