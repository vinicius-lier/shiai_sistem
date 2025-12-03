from django.urls import path
from . import views

urlpatterns = [
    # Landing page
    path('', views.landing_page, name='landing'),
    # Seleção de tipo de login
    path('login/', views.selecionar_tipo_login, name='selecionar_tipo_login'),
    
    # Dashboard operacional
    path('dashboard/', views.index, name='index'),
    
    # Academias
    path('academias/', views.lista_academias, name='lista_academias'),
    path('academias/cadastrar/', views.cadastrar_academia, name='cadastrar_academia'),
    path('academias/<int:academia_id>/', views.detalhe_academia, name='detalhe_academia'),
    path('academias/<int:academia_id>/editar/', views.editar_academia, name='editar_academia'),
    path('academias/<int:academia_id>/deletar/', views.deletar_academia, name='deletar_academia'),
    
    # Categorias
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/cadastrar/', views.cadastrar_categoria, name='cadastrar_categoria'),
    
    # Atletas
    path('atletas/', views.lista_atletas, name='lista_atletas'),
    path('atletas/cadastrar/', views.cadastrar_atleta, name='cadastrar_atleta'),
    path('atletas/<int:atleta_id>/editar/', views.editar_atleta, name='editar_atleta'),
    path('atletas/festival/', views.cadastrar_festival, name='cadastrar_festival'),
    path('atletas/importar/', views.importar_atletas, name='importar_atletas'),
    path('atletas/categorias-ajax/', views.get_categorias_ajax, name='get_categorias_ajax'),
    path('categorias-por-sexo/', views.get_categorias_por_sexo, name='get_categorias_por_sexo'),
    
    # Pesagem
    path('pesagem/', views.pesagem, name='pesagem'),
    path('pesagem/mobile/', views.pesagem_mobile_view, name='pesagem_mobile'),
    path('pesagem/inscricao/<int:inscricao_id>/registrar/', views.registrar_peso, name='registrar_peso'),
    path('pesagem/inscricao/<int:inscricao_id>/confirmar-remanejamento/', views.confirmar_remanejamento, name='confirmar_remanejamento'),
    path('pesagem/<int:atleta_id>/rebaixar/', views.rebaixar_categoria, name='rebaixar_categoria'),
    
    # Chaves
    path('chaves/', views.lista_chaves, name='lista_chaves'),
    path('chaves/gerar/', views.gerar_chave_view, name='gerar_chave_view'),
    path('chaves/gerar-todas/', views.gerar_todas_chaves, name='gerar_todas_chaves'),
    path('chaves/gerar-manual/', views.gerar_chave_manual, name='gerar_chave_manual'),
    path('chaves/<int:chave_id>/', views.detalhe_chave, name='detalhe_chave'),
    path('chaves/<int:chave_id>/imprimir/', views.imprimir_chave, name='imprimir_chave'),
    path('chave/mobile/<int:chave_id>/', views.chave_mobile_view, name='chave_mobile'),
    
    # Lutas
    path('lutas/<int:luta_id>/registrar-vencedor/', views.registrar_vencedor, name='registrar_vencedor'),
    path('luta/mobile/<int:luta_id>/', views.luta_mobile_view, name='luta_mobile'),
    
    # Pontuação e Ranking
    path('ranking/global/', views.ranking_global, name='ranking_global'),
    path('ranking/', views.ranking_academias, name='ranking_academias'),
    path('ranking/calcular/', views.calcular_pontuacao, name='calcular_pontuacao'),
    path('api/ranking/academias/', views.api_ranking_academias, name='api_ranking_academias'),
    
    # Perfil de Atleta
    path('atletas/<int:atleta_id>/perfil/', views.perfil_atleta, name='perfil_atleta'),
    
    # Inscrições e Métricas do Evento
    path('inscricoes/', views.inscrever_atletas, name='inscrever_atletas'),
    path('metricas/', views.metricas_evento, name='metricas_evento'),
    
    # Relatórios (mantidos para compatibilidade, mas consolidados em Métricas)
    path('relatorios/dashboard/', views.dashboard, name='dashboard'),
    path('relatorios/atletas-inscritos/', views.relatorio_atletas_inscritos, name='relatorio_atletas_inscritos'),
    path('relatorios/pesagem-final/', views.relatorio_pesagem_final, name='relatorio_pesagem_final'),
    path('relatorios/chaves/', views.relatorio_chaves, name='relatorio_chaves'),
    path('relatorios/resultados-categoria/', views.relatorio_resultados_categoria, name='relatorio_resultados_categoria'),
    # Admin / API
    path('api/admin/reset/', views.ResetCompeticaoAPIView.as_view(), name='reset_campeonato'),
    
    # Campeonatos
    path('campeonatos/', views.lista_campeonatos, name='lista_campeonatos'),
    path('campeonatos/cadastrar/', views.cadastrar_campeonato, name='cadastrar_campeonato'),
    path('campeonatos/<int:campeonato_id>/editar/', views.editar_campeonato, name='editar_campeonato'),
    path('campeonatos/<int:campeonato_id>/ativar/', views.definir_campeonato_ativo, name='definir_campeonato_ativo'),
    path('campeonatos/<int:campeonato_id>/academias/', views.gerenciar_academias_campeonato, name='gerenciar_academias_campeonato'),
    path('campeonatos/<int:campeonato_id>/senhas/', views.gerenciar_senhas_campeonato, name='gerenciar_senhas_campeonato'),
    path('login/operacional/', views.login_operacional, name='login_operacional'),
    path('logout/', views.logout_geral, name='logout_geral'),
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
    
    # Módulo de Administração da Competição
    path('administracao/', views.administracao_painel, name='administracao_painel'),
    path('administracao/conferencia-inscricoes/', views.administracao_conferencia_inscricoes, name='administracao_conferencia_inscricoes'),
    path('administracao/confirmar-inscricoes/', views.administracao_confirmar_inscricoes, name='administracao_confirmar_inscricoes'),
    path('administracao/financeiro/', views.administracao_financeiro, name='administracao_financeiro'),
    path('administracao/financeiro/despesas/', views.administracao_despesas, name='administracao_despesas'),
    path('administracao/equipe/', views.administracao_equipe, name='administracao_equipe'),
    path('administracao/equipe/pessoas-lista/', views.administracao_equipe_pessoas_lista, name='administracao_equipe_pessoas_lista'),
    path('administracao/equipe/gerenciar/', views.administracao_equipe_gerenciar, name='administracao_equipe_gerenciar'),
    path('administracao/equipe/gerenciar/<int:campeonato_id>/', views.administracao_equipe_gerenciar, name='administracao_equipe_gerenciar'),
    path('administracao/insumos/', views.administracao_insumos, name='administracao_insumos'),
    path('administracao/patrocinios/', views.administracao_patrocinios, name='administracao_patrocinios'),
    path('administracao/relatorios/', views.administracao_relatorios, name='administracao_relatorios'),
    path('administracao/banco-operacional/<str:tipo>/', views.administracao_cadastros_operacionais, name='administracao_cadastros_operacionais'),
    path('administracao/usuarios-operacionais/', views.gerenciar_usuarios_operacionais, name='gerenciar_usuarios_operacionais'),
    path('alterar-senha-obrigatorio/', views.alterar_senha_obrigatorio, name='alterar_senha_obrigatorio'),
    
    # Ajuda e Manuais
    path('ajuda/', views.ajuda_manual, name='ajuda_manual'),
    path('ajuda/manual/<str:tipo>/', views.ajuda_manual_web, name='ajuda_manual_web'),
    path('ajuda/documentacao-tecnica/', views.ajuda_documentacao_tecnica, name='ajuda_documentacao_tecnica'),
    
    # Pagamentos (unificado em Conferência de Pagamentos)
    path('academia/evento/<int:campeonato_id>/enviar-comprovante/', views.academia_enviar_comprovante, name='academia_enviar_comprovante'),
    
    # Views deprecadas (mantidas para compatibilidade - redirecionam para conferência de pagamentos)
    path('administracao/validacao-pagamentos/', views.validacao_pagamentos, name='validacao_pagamentos'),
    path('administracao/validar-pagamento/<int:pagamento_id>/', views.validar_pagamento, name='validar_pagamento'),
    path('administracao/rejeitar-pagamento/<int:pagamento_id>/', views.rejeitar_pagamento, name='rejeitar_pagamento'),
    
    # Conferência de Pagamentos (fluxo principal unificado)
    path('administracao/conferencia-pagamentos/', views.conferencia_pagamentos_lista, name='conferencia_pagamentos_lista'),
    path('administracao/conferencia-pagamentos/<int:academia_id>/<int:campeonato_id>/', views.conferencia_pagamentos_detalhe, name='conferencia_pagamentos_detalhe'),
    path('administracao/conferencia-pagamentos/<int:academia_id>/<int:campeonato_id>/salvar/', views.conferencia_pagamentos_salvar, name='conferencia_pagamentos_salvar'),
    path('administracao/conferencia-pagamentos/<int:academia_id>/<int:campeonato_id>/mensagem-whatsapp/', views.gerar_mensagem_whatsapp, name='gerar_mensagem_whatsapp'),
    
    # Ocorrências
    path('administracao/ocorrencias/', views.ocorrencias_lista, name='ocorrencias_lista'),
    path('administracao/ocorrencias/criar/', views.ocorrencias_criar, name='ocorrencias_criar'),
    path('administracao/ocorrencias/<int:ocorrencia_id>/', views.ocorrencias_detalhe, name='ocorrencias_detalhe'),
    path('administracao/ocorrencias/historico/', views.ocorrencias_historico, name='ocorrencias_historico'),
]
