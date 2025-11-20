from django.urls import path
from . import views
from . import views_pesagem
from . import views_chaves
from . import views_academia

app_name = 'eventos'

urlpatterns = [
    # Login/Logout de Academia (independente)
    path('academia/login/', views_academia.academia_login, name='academia_login'),
    path('academia/logout/', views_academia.academia_logout, name='academia_logout'),
    path('academia/trocar-senha/', views_academia.academia_trocar_senha, name='academia_trocar_senha'),
    path('academia/painel/', views_academia.academia_painel, name='academia_painel'),
    
    # Painel Operacional
    path('operacional/eventos/', views.lista_eventos, name='lista_eventos'),
    path('operacional/eventos/criar/', views.criar_evento, name='criar_evento'),
    path('operacional/eventos/<int:evento_id>/editar/', views.editar_evento, name='editar_evento'),
    path('operacional/eventos/<int:evento_id>/configurar/', views.configurar_evento, name='configurar_evento'),
    path('operacional/eventos/<int:evento_id>/inscritos/', views.ver_inscritos, name='ver_inscritos'),
    path('operacional/eventos/<int:evento_id>/inscritos/<int:evento_atleta_id>/remover/', views.remover_inscrito, name='remover_inscrito'),
    
    # Pesagem de Eventos
    path('operacional/eventos/<int:evento_id>/pesagem/', views_pesagem.pesagem_evento, name='pesagem_evento'),
    path('operacional/eventos/<int:evento_id>/pesagem/<int:evento_atleta_id>/registrar/', views_pesagem.registrar_peso_evento, name='registrar_peso_evento'),
    path('operacional/eventos/<int:evento_id>/pesagem/<int:evento_atleta_id>/confirmar/', views_pesagem.confirmar_acao_pesagem, name='confirmar_acao_pesagem'),
    path('operacional/eventos/<int:evento_id>/pesagem/encerrar/', views_pesagem.encerrar_pesagem, name='encerrar_pesagem'),
    
    # Chaves de Eventos
    path('operacional/eventos/<int:evento_id>/chaves/', views_chaves.listar_categorias_evento, name='listar_categorias'),
    path('operacional/eventos/<int:evento_id>/chaves/categoria/<int:categoria_id>/gerar/', views_chaves.selecionar_tipo_chave, name='selecionar_tipo_chave'),
    path('operacional/eventos/<int:evento_id>/chaves/listar/', views_chaves.listar_chaves_evento, name='listar_chaves_evento'),
    path('operacional/eventos/<int:evento_id>/chaves/<int:chave_id>/', views_chaves.detalhe_chave_evento, name='detalhe_chave_evento'),
    path('operacional/eventos/<int:evento_id>/chaves/<int:chave_id>/finalizar/', views_chaves.finalizar_chave_evento, name='finalizar_chave_evento'),
    
    # Painel do Professor (Academia) - Compatibilidade com sistema antigo
    path('academia/eventos/', views.eventos_disponiveis, name='eventos_disponiveis'),
    path('academia/eventos/<int:evento_id>/inscrever/', views.inscrever_atletas, name='inscrever_atletas'),
    path('academia/eventos/<int:evento_id>/novo-atleta/', views.cadastrar_atleta_rapido, name='cadastrar_atleta_rapido'),
    path('academia/eventos/<int:evento_id>/meus-inscritos/', views.meus_inscritos, name='meus_inscritos'),
]

