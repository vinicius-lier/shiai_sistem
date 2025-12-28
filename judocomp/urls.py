"""
URL configuration for judocomp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from atletas import views as atletas_views
from atletas import views_org_selector


urlpatterns = [
    # Admin padrão Django
    path('admin/', admin.site.urls),

    # Landing page pública e login global (sem organização)
    path('', atletas_views.landing_publica, name='landing_publica'),
    path('login/', atletas_views.login_operacional, name='login'),
    path('logout/', atletas_views.logout_geral, name='logout'),

    # Seletor de organização (superuser)
    path('selecionar-organizacao/', views_org_selector.selecionar_organizacao, name='selecionar_organizacao'),

    # Painel de organizações (apenas superuser)
    path('painel/organizacoes/', atletas_views.painel_organizacoes, name='painel_organizacoes'),

    # Tabela pública de categorias de peso
    path('tabela-categorias/', atletas_views.tabela_categorias_peso, name='tabela_categorias_peso'),

    # Fluxo de academia (mantido fora do multi-tenant de organização)
    path('academia/login/', atletas_views.academia_login, name='academia_login'),
    path('academia/logout/', atletas_views.academia_logout, name='academia_logout'),
    path('academia/', atletas_views.academia_painel, name='academia_painel'),
    path('academia/evento/<int:campeonato_id>/', atletas_views.academia_evento, name='academia_evento'),
    path('academia/evento/<int:campeonato_id>/inscricoes/', atletas_views.academia_inscrever_atletas, name='academia_inscrever_atletas'),
    path('academia/evento/<int:campeonato_id>/chaves/', atletas_views.academia_ver_chaves, name='academia_ver_chaves'),
    path('academia/evento/<int:campeonato_id>/chaves/<int:chave_id>/', atletas_views.academia_detalhe_chave, name='academia_detalhe_chave'),
    path('academia/evento/<int:campeonato_id>/regulamento/', atletas_views.academia_baixar_regulamento, name='academia_baixar_regulamento'),
    path('academia/evento/<int:campeonato_id>/atletas/', atletas_views.academia_lista_atletas, name='academia_lista_atletas_evento'),
    path('academia/atletas/', atletas_views.academia_lista_atletas, name='academia_lista_atletas'),
    path('academia/atletas/cadastrar/', atletas_views.academia_cadastrar_atleta, name='academia_cadastrar_atleta'),
    path('academia/atletas/cadastrar/<int:campeonato_id>/', atletas_views.academia_cadastrar_atleta, name='academia_cadastrar_atleta_evento'),

    # Rotas multi-tenant: tudo operacional dentro de <organizacao_slug>/
    path('<slug:organizacao_slug>/', include('atletas.urls_org')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Servir MEDIA sempre (inclusive produção Render)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Manter staticfiles patterns SOMENTE se DEBUG=True
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
