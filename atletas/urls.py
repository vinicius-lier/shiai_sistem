from django.urls import path
from . import views

urlpatterns = [
    # Página inicial
    path('', views.index, name='index'),
    
    # Academias
    path('academias/', views.lista_academias, name='lista_academias'),
    path('academias/cadastrar/', views.cadastrar_academia, name='cadastrar_academia'),
    
    # Categorias
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/cadastrar/', views.cadastrar_categoria, name='cadastrar_categoria'),
    
    # Atletas
    path('atletas/', views.lista_atletas, name='lista_atletas'),
    path('atletas/cadastrar/', views.cadastrar_atleta, name='cadastrar_atleta'),
    path('atletas/festival/', views.cadastrar_festival, name='cadastrar_festival'),
    path('atletas/importar/', views.importar_atletas, name='importar_atletas'),
    path('atletas/categorias-ajax/', views.get_categorias_ajax, name='get_categorias_ajax'),
    path('categorias-por-sexo/', views.get_categorias_por_sexo, name='get_categorias_por_sexo'),
    
    # Pesagem
    path('pesagem/', views.pesagem, name='pesagem'),
    path('pesagem/mobile/', views.pesagem_mobile_view, name='pesagem_mobile'),
    path('pesagem/<int:atleta_id>/registrar/', views.registrar_peso, name='registrar_peso'),
    path('pesagem/<int:atleta_id>/confirmar-remanejamento/', views.confirmar_remanejamento, name='confirmar_remanejamento'),
    path('pesagem/<int:atleta_id>/rebaixar/', views.rebaixar_categoria, name='rebaixar_categoria'),
    
    # Chaves
    path('chaves/', views.lista_chaves, name='lista_chaves'),
    path('chaves/gerar/', views.gerar_chave_view, name='gerar_chave_view'),
    path('chaves/gerar-manual/', views.gerar_chave_manual, name='gerar_chave_manual'),
    path('chaves/<int:chave_id>/', views.detalhe_chave, name='detalhe_chave'),
    path('chave/mobile/<int:chave_id>/', views.chave_mobile_view, name='chave_mobile'),
    
    # Lutas
    path('lutas/<int:luta_id>/registrar-vencedor/', views.registrar_vencedor, name='registrar_vencedor'),
    path('luta/mobile/<int:luta_id>/', views.luta_mobile_view, name='luta_mobile'),
    
    # Pontuação e Ranking
    path('ranking/', views.ranking_academias, name='ranking_academias'),
    path('ranking/calcular/', views.calcular_pontuacao, name='calcular_pontuacao'),
    path('api/ranking/academias/', views.api_ranking_academias, name='api_ranking_academias'),
    
    # Relatórios
    path('relatorios/dashboard/', views.dashboard, name='dashboard'),
    path('relatorios/atletas-inscritos/', views.relatorio_atletas_inscritos, name='relatorio_atletas_inscritos'),
    path('relatorios/pesagem-final/', views.relatorio_pesagem_final, name='relatorio_pesagem_final'),
    path('relatorios/chaves/', views.relatorio_chaves, name='relatorio_chaves'),
    path('relatorios/resultados-categoria/', views.relatorio_resultados_categoria, name='relatorio_resultados_categoria'),
    # Admin / API
    path('api/admin/reset/', views.ResetCompeticaoAPIView.as_view(), name='reset_campeonato'),
]
