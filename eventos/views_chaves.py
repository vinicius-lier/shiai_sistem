"""
Views para geração e gerenciamento de chaves de eventos.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Q
from atletas.decorators import operacional_required
from atletas.models import Chave, Luta, Categoria
from atletas.services.chave_services import (
    validar_pesagem_completa,
    obter_atletas_categoria,
    determinar_tipo_chave_automatico,
    gerar_chave_melhor_de_3,
    gerar_chave_casada_3,
    gerar_chave_simples_tres_atletas,  # ✅ NOVO
    gerar_rodizio,
    gerar_eliminatoria_simples,
    gerar_eliminatoria_com_repescagem,
    gerar_chave_olimpica,
    gerar_chave_liga,
    gerar_chave_por_grupos
)
from .models import Evento, EventoAtleta


@operacional_required
def listar_categorias_evento(request, evento_id):
    """
    Lista todas as categorias com atletas inscritos no evento.
    Permite selecionar categoria para gerar chave.
    """
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Verificar se evento está expirado (para mostrar banner)
    evento_expirado = evento.is_expired
    
    # Buscar todas as categorias únicas que têm atletas inscritos
    evento_atletas = evento.evento_atletas.filter(
        categoria_final__isnull=False,
        status__in=['OK']
    ).select_related('categoria_final', 'atleta')
    
    # Agrupar por categoria
    categorias_dict = {}
    for evento_atleta in evento_atletas:
        categoria = evento_atleta.categoria_final
        if not categoria:
            continue
        
        key = f"{categoria.classe}_{categoria.sexo}_{categoria.categoria_nome}"
        if key not in categorias_dict:
            categorias_dict[key] = {
                'categoria': categoria,
                'total_atletas': 0,
                'atletas_pesados': 0,
                'chave_existe': False
            }
        
        categorias_dict[key]['total_atletas'] += 1
        if evento_atleta.peso_oficial:
            categorias_dict[key]['atletas_pesados'] += 1
    
    # Verificar se já existe chave para cada categoria
    for key, info in categorias_dict.items():
        chave_existe = Chave.objects.filter(
            evento=evento,
            classe=info['categoria'].classe,
            sexo=info['categoria'].sexo,
            categoria=info['categoria'].categoria_nome
        ).exists()
        info['chave_existe'] = chave_existe
    
    categorias_list = list(categorias_dict.values())
    
    return render(request, 'eventos/chaves/listar_categorias.html', {
        'evento': evento,
        'categorias': categorias_list,
        'evento_expirado': evento_expirado  # ✅ NOVO
    })


@operacional_required
def selecionar_tipo_chave(request, evento_id, categoria_id):
    """
    Tela de seleção do tipo de chave antes de gerar.
    Exibe pergunta obrigatória com todas as opções.
    """
    evento = get_object_or_404(Evento, id=evento_id)
    
    # ✅ BLOQUEIO: Não permitir gerar chaves após o evento
    if evento.is_expired:
        messages.error(request, "Chaves não podem ser modificadas após a data do evento.")
        return redirect('eventos:listar_chaves_evento', evento_id=evento.id)
    
    categoria = get_object_or_404(Categoria, id=categoria_id)
    
    # Validar pesagem completa
    valido, mensagem = validar_pesagem_completa(evento, categoria)
    if not valido:
        messages.error(request, mensagem)
        return redirect('eventos:listar_categorias', evento_id=evento.id)
    
    # Obter atletas da categoria
    atletas = obter_atletas_categoria(evento, categoria)
    num_atletas = len(atletas)
    
    if num_atletas < 2:
        messages.warning(request, f'É necessário pelo menos 2 atletas para gerar uma chave. Categoria tem {num_atletas} atleta(s).')
        return redirect('eventos:listar_categorias', evento_id=evento.id)
    
    # Verificar se já existe chave
    chave_existente = Chave.objects.filter(
        evento=evento,
        classe=categoria.classe,
        sexo=categoria.sexo,
        categoria=categoria.categoria_nome
    ).first()
    
    # Determinar tipo automático sugerido
    tipo_automatico = determinar_tipo_chave_automatico(num_atletas)
    
    if request.method == 'POST':
        tipo_chave = request.POST.get('tipo_chave')
        
        if not tipo_chave:
            messages.error(request, 'Selecione um tipo de chave.')
            return render(request, 'eventos/chaves/selecionar_tipo_chave.html', {
                'evento': evento,
                'categoria': categoria,
                'atletas': atletas,
                'num_atletas': num_atletas,
                'tipo_automatico': tipo_automatico,
                'chave_existente': chave_existente
            })
        
        # Gerar chave
        return gerar_chave_por_tipo(request, evento, categoria, atletas, tipo_chave, chave_existente)
    
    return render(request, 'eventos/chaves/selecionar_tipo_chave.html', {
        'evento': evento,
        'categoria': categoria,
        'atletas': atletas,
        'num_atletas': num_atletas,
        'tipo_automatico': tipo_automatico,
        'chave_existente': chave_existente
    })


@transaction.atomic
def gerar_chave_por_tipo(request, evento, categoria, atletas_list, tipo_chave, chave_existente=None):
    """
    Gera a chave baseado no tipo selecionado.
    Se chave_existente, recalcula (idempotente).
    """
    from atletas.services.luta_services import recalcular_chave
    
    # Criar ou obter chave existente
    if chave_existente:
        chave = chave_existente
        # Limpar lutas antigas para recalcular
        chave.lutas.all().delete()
        chave.atletas.clear()
    else:
        chave = Chave.objects.create(
            evento=evento,
            classe=categoria.classe,
            sexo=categoria.sexo,
            categoria=categoria.categoria_nome,
            tipo_chave=tipo_chave,
            estrutura={}
        )
    
    # Adicionar atletas
    chave.atletas.set(atletas_list)
    
    # Gerar chave baseado no tipo
    try:
        if tipo_chave == 'MELHOR_DE_3':
            gerar_chave_melhor_de_3(chave, atletas_list)
        elif tipo_chave == 'CASADA_3':
            gerar_chave_casada_3(chave, atletas_list)
        elif tipo_chave == 'SIMPLES_3':  # ✅ NOVO
            gerar_chave_simples_tres_atletas(chave, atletas_list)
        elif tipo_chave == 'RODIZIO':
            gerar_rodizio(chave, atletas_list)
        elif tipo_chave == 'ELIMINATORIA_SIMPLES':
            gerar_eliminatoria_simples(chave, atletas_list)
        elif tipo_chave == 'ELIMINATORIA_REPESCAGEM':
            gerar_eliminatoria_com_repescagem(chave, atletas_list)
        elif tipo_chave == 'OLIMPICA':
            gerar_chave_olimpica(chave, atletas_list)
        elif tipo_chave == 'LIGA':
            gerar_chave_liga(chave, atletas_list)
        elif tipo_chave == 'GRUPOS':
            gerar_chave_por_grupos(chave, atletas_list)
        else:
            messages.error(request, f'Tipo de chave "{tipo_chave}" não reconhecido.')
            return redirect('eventos:listar_categorias', evento_id=evento.id)
        
        tipo_display = chave.get_tipo_chave_display() if chave.tipo_chave else 'Não definido'
        messages.success(request, f'Chave gerada com sucesso! Tipo: {tipo_display}')
        return redirect('eventos:detalhe_chave_evento', evento_id=evento.id, chave_id=chave.id)
        
    except ValueError as e:
        messages.error(request, f'Erro ao gerar chave: {str(e)}')
        return redirect('eventos:listar_categorias', evento_id=evento.id)


@operacional_required
def detalhe_chave_evento(request, evento_id, chave_id):
    """
    Visualiza detalhes de uma chave do evento.
    """
    from atletas.services.luta_services import obter_resultados_chave
    from atletas.models import Atleta
    
    evento = get_object_or_404(Evento, id=evento_id)
    chave = get_object_or_404(Chave, id=chave_id, evento=evento)
    
    lutas = chave.lutas.all().order_by('round', 'id')
    
    # ✅ ADICIONAR: Obter resultados da chave
    resultados_ids = obter_resultados_chave(chave)
    resultados = []
    for resultado_id in resultados_ids:
        try:
            atleta = Atleta.objects.get(id=resultado_id)
            resultados.append(atleta)
        except Atleta.DoesNotExist:
            pass
    
    # ✅ NOVO: Verificar se todas as lutas estão concluídas (para mostrar botão Finalizar)
    todas_lutas_concluidas = all(luta.concluida for luta in lutas)
    
    # ✅ NOVO: Para chave SIMPLES_3, verificar se a luta 2 (final) está concluída
    pode_finalizar = todas_lutas_concluidas
    if chave.tipo_chave == 'SIMPLES_3':
        luta2 = lutas.filter(round=2).first()
        if luta2:
            pode_finalizar = luta2.concluida and luta2.atleta_b is not None
    
    return render(request, 'eventos/chaves/detalhe_chave.html', {
        'evento': evento,
        'chave': chave,
        'lutas': lutas,
        'resultados': resultados,
        'pode_finalizar': pode_finalizar  # ✅ NOVO
    })


@operacional_required
def listar_chaves_evento(request, evento_id):
    """
    Lista todas as chaves geradas para um evento.
    """
    evento = get_object_or_404(Evento, id=evento_id)
    chaves = evento.chaves.all().order_by('classe', 'sexo', 'categoria')
    
    return render(request, 'eventos/chaves/listar_chaves.html', {
        'evento': evento,
        'chaves': chaves
    })


@operacional_required
def finalizar_chave_evento(request, evento_id, chave_id):
    """
    Finaliza uma chave e calcula pontos para ranking.
    """
    from atletas.services.luta_services import finalizar_chave
    
    evento = get_object_or_404(Evento, id=evento_id)
    chave = get_object_or_404(Chave, id=chave_id, evento=evento)
    
    # ✅ BLOQUEIO: Não permitir finalizar chave após o evento
    if evento.is_expired:
        messages.error(request, "Chaves não podem ser modificadas após a data do evento.")
        return redirect('eventos:detalhe_chave_evento', evento_id=evento.id, chave_id=chave.id)
    
    if chave.finalizada:
        messages.warning(request, 'Esta chave já foi finalizada.')
    else:
        finalizar_chave(chave)
        messages.success(request, 'Chave finalizada! Pontos calculados e ranking atualizado.')
    
    return redirect('eventos:detalhe_chave_evento', evento_id=evento.id, chave_id=chave.id)

