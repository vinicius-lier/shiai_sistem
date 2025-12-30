from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.landing_publica, name='landing_publica'),
    path('login/', views.selecionar_tipo_login, name='selecionar_tipo_login'),
    path('login/operacional/', views.login_operacional, name='login_operacional'),
    path('logout/', views.logout_geral, name='logout_geral'),
    path('painel/organizacoes/', views.painel_organizacoes, name='painel_organizacoes'),

    # Fluxo Academia (fora do tenant operacional)
    path('academia/login/', views.academia_login, name='academia_login'),
    path('academia/logout/', views.academia_logout, name='academia_logout'),
    path('academia/', views.academia_painel, name='academia_painel'),
    path('academia/eventos/', views.academia_painel, name='academia_eventos'),
    path('academia/evento/<int:campeonato_id>/', views.academia_evento, name='academia_evento'),
    path('academia/atletas/', views.academia_lista_atletas, name='academia_lista_atletas'),
    path('academia/atletas/evento/<int:campeonato_id>/', views.academia_lista_atletas, name='academia_lista_atletas_evento'),
    path('academia/inscrever/<int:campeonato_id>/', views.academia_inscrever_atletas, name='academia_inscrever_atletas'),
    path('academia/evento/<int:campeonato_id>/inscrever/', views.academia_inscrever_atletas, name='academia_evento_inscrever'),
    path('academia/atleta/novo/', views.academia_cadastrar_atleta, name='academia_cadastrar_atleta'),
    path('academia/atleta/novo/evento/<int:campeonato_id>/', views.academia_cadastrar_atleta, name='academia_cadastrar_atleta_evento'),
    path('academia/evento/<int:campeonato_id>/novo-atleta/', views.academia_cadastrar_atleta, name='academia_evento_novo_atleta'),
    path('academia/evento/<int:campeonato_id>/inscricoes/', views.academia_lista_atletas, name='academia_evento_inscricoes'),
    path('academia/chaves/<int:campeonato_id>/', views.academia_ver_chaves, name='academia_ver_chaves'),
    path('academia/evento/<int:campeonato_id>/chaves/', views.academia_ver_chaves, name='academia_evento_chaves'),
    path('academia/chave/<int:campeonato_id>/<int:chave_id>/', views.academia_detalhe_chave, name='academia_detalhe_chave'),
    path('academia/regulamento/<int:campeonato_id>/', views.academia_baixar_regulamento, name='academia_baixar_regulamento'),
    path('academia/tabela-categorias/', views.tabela_categorias_peso, name='tabela_categorias_peso'),
    path('media/<path:path>', views.servir_media, name='servir_media'),

    # Rotas multi-tenant (operacional)
    path('<slug:organizacao_slug>/', include('atletas.urls_org')),
]
