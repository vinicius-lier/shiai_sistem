from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.http import JsonResponse


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