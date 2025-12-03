"""
Views para o fluxo completo de conferência de pagamentos
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from decimal import Decimal
import datetime
from .models import (
    Academia, Campeonato, Inscricao, ConferenciaPagamento,
    AcademiaCampeonato
)
from .academia_auth import operacional_required
from .utils_historico import registrar_historico


def calcular_valor_esperado_academia(academia, campeonato):
    """Calcula o valor total esperado de uma academia baseado nas inscrições"""
    inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    ).select_related('atleta')
    
    valor_federado = campeonato.valor_inscricao_federado or Decimal('0.00')
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or Decimal('0.00')
    
    valor_total = Decimal('0.00')
    for inscricao in inscricoes:
        if inscricao.atleta.federado:
            valor_total += valor_federado
        else:
            valor_total += valor_nao_federado
    
    return valor_total, inscricoes.count()


@operacional_required
def conferencia_pagamentos_lista(request):
    """Lista todas as academias com status de pagamento agrupadas"""
    # Buscar campeonato ativo ou selecionado
    campeonato_id = request.GET.get('campeonato_id')
    if campeonato_id:
        campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    else:
        campeonato = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato:
        messages.warning(request, 'Nenhum evento selecionado ou encontrado.')
        campeonatos = Campeonato.objects.all().order_by('-data_competicao', '-data_inicio')
        return render(request, 'atletas/administracao/conferencia_pagamentos_lista.html', {
            'campeonatos': campeonatos,
            'campeonato_selecionado': None,
            'academias': [],
        })
    
    # Buscar academias permitidas no campeonato
    academias_permitidas = AcademiaCampeonato.objects.filter(
        campeonato=campeonato,
        permitido=True
    ).select_related('academia')
    
    # Buscar academias que têm inscrições
    academias_com_inscricoes = Inscricao.objects.filter(
        campeonato=campeonato
    ).values_list('atleta__academia_id', flat=True).distinct()
    
    academias_dados = []
    for vinculo in academias_permitidas:
        academia = vinculo.academia
        if academia.id not in academias_com_inscricoes:
            continue
        
        # Calcular valor esperado e quantidade de atletas
        valor_esperado, qtd_atletas = calcular_valor_esperado_academia(academia, campeonato)
        
        # Buscar conferência (único modelo oficial)
        conferencia = ConferenciaPagamento.objects.filter(
            academia=academia,
            campeonato=campeonato
        ).first()
        
        # Determinar status (apenas de ConferenciaPagamento)
        if conferencia:
            status = conferencia.status
            valor_recebido = conferencia.valor_recebido
        else:
            status = 'PENDENTE'
            valor_recebido = None
        
        academias_dados.append({
            'academia': academia,
            'valor_esperado': valor_esperado,
            'qtd_atletas': qtd_atletas,
            'status': status,
            'valor_recebido': valor_recebido,
            'conferencia': conferencia,
        })
    
    # Ordenar por status (Pendente primeiro, depois Divergente, depois Confirmado)
    status_order = {'PENDENTE': 0, 'DIVERGENTE': 1, 'CONFIRMADO': 2}
    academias_dados.sort(key=lambda x: (status_order.get(x['status'], 99), x['academia'].nome))
    
    campeonatos = Campeonato.objects.all().order_by('-data_competicao', '-data_inicio')
    
    context = {
        'campeonatos': campeonatos,
        'campeonato_selecionado': campeonato,
        'academias': academias_dados,
    }
    
    return render(request, 'atletas/administracao/conferencia_pagamentos_lista.html', context)


@operacional_required
def conferencia_pagamentos_detalhe(request, academia_id, campeonato_id):
    """Tela de conferência detalhada por academia"""
    academia = get_object_or_404(Academia, id=academia_id)
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Buscar todas as inscrições da academia
    inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    ).select_related('atleta').order_by('atleta__nome')
    
    # Calcular valores
    valor_federado = campeonato.valor_inscricao_federado or Decimal('0.00')
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or Decimal('0.00')
    
    inscricoes_detalhadas = []
    valor_total_esperado = Decimal('0.00')
    
    for inscricao in inscricoes:
        valor_inscricao = valor_federado if inscricao.atleta.federado else valor_nao_federado
        valor_total_esperado += valor_inscricao
        
        inscricoes_detalhadas.append({
            'inscricao': inscricao,
            'atleta': inscricao.atleta,
            'valor_inscricao': valor_inscricao,
            'federado': inscricao.atleta.federado,
        })
    
    # Buscar conferência existente (único modelo oficial)
    conferencia = ConferenciaPagamento.objects.filter(
        academia=academia,
        campeonato=campeonato
    ).select_related('conferido_por').first()
    
    # Se encontrou conferência, recarregar do banco para garantir dados atualizados
    if conferencia:
        conferencia.refresh_from_db()
    
    # Buscar contato da academia (professor responsável)
    contato_whatsapp = academia.telefone or ''
    contato_nome = academia.responsavel or academia.nome
    
    context = {
        'academia': academia,
        'campeonato': campeonato,
        'inscricoes_detalhadas': inscricoes_detalhadas,
        'valor_total_esperado': valor_total_esperado,
        'qtd_atletas': len(inscricoes_detalhadas),
        'conferencia': conferencia,
        'contato_whatsapp': contato_whatsapp,
        'contato_nome': contato_nome,
        'valor_federado': valor_federado,
        'valor_nao_federado': valor_nao_federado,
    }
    
    return render(request, 'atletas/administracao/conferencia_pagamentos_detalhe.html', context)


@operacional_required
@require_http_methods(["POST"])
def conferencia_pagamentos_salvar(request, academia_id, campeonato_id):
    """Salva a conferência de pagamento"""
    academia = get_object_or_404(Academia, id=academia_id)
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    status_conferencia = request.POST.get('status', '').strip()
    valor_recebido = request.POST.get('valor_recebido', '').strip()
    observacoes = request.POST.get('observacoes', '').strip()
    
    if not status_conferencia:
        messages.error(request, 'Status da conferência é obrigatório.')
        return redirect('conferencia_pagamentos_detalhe', academia_id=academia_id, campeonato_id=campeonato_id)
    
    # Validar que o status é válido
    if status_conferencia not in ['PENDENTE', 'CONFIRMADO', 'DIVERGENTE', 'NAO_ENCONTRADO']:
        messages.error(request, 'Status inválido.')
        return redirect('conferencia_pagamentos_detalhe', academia_id=academia_id, campeonato_id=campeonato_id)
    
    # Calcular valor esperado
    valor_esperado, qtd_atletas = calcular_valor_esperado_academia(academia, campeonato)
    
    # Converter valor recebido
    try:
        valor_recebido_decimal = Decimal(valor_recebido.replace(',', '.')) if valor_recebido else None
    except:
        valor_recebido_decimal = None
    
    # Usar update_or_create para garantir que sempre atualiza corretamente
    conferencia, created = ConferenciaPagamento.objects.update_or_create(
        academia=academia,
        campeonato=campeonato,
        defaults={
            'status': status_conferencia,
            'valor_esperado': valor_esperado,
            'valor_recebido': valor_recebido_decimal,
            'observacoes': observacoes,
            'conferido_por': request.user,
            'data_conferencia': timezone.now(),
            'quantidade_atletas': qtd_atletas,
        }
    )
    
    # Recarregar do banco para garantir que está atualizado
    conferencia.refresh_from_db()
    
    # Atualizar status das inscrições baseado na conferência
    inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    )
    
    if status_conferencia == 'CONFIRMADO':
        # Confirmar todas as inscrições - usar 'aprovado' para garantir que apareçam na pesagem
        inscricoes.update(status_inscricao='aprovado')
        messages.success(request, f'Conferência salva com sucesso! Status: CONFIRMADO. {qtd_atletas} inscrição(ões) aprovada(s) e liberada(s) para pesagem.')
    elif status_conferencia == 'DIVERGENTE':
        # Manter como pendente se divergente - bloqueia pesagem
        inscricoes.update(status_inscricao='pendente')
        messages.warning(request, f'Conferência salva com sucesso! Status: DIVERGENTE. Inscrições permanecem pendentes e bloqueadas para pesagem até confirmação.')
    elif status_conferencia == 'NAO_ENCONTRADO':
        # Manter como pendente se não encontrado - bloqueia pesagem
        inscricoes.update(status_inscricao='pendente')
        messages.warning(request, f'Conferência salva com sucesso! Status: NÃO ENCONTRADO. Inscrições permanecem pendentes e bloqueadas para pesagem.')
    else:
        # Status PENDENTE - bloqueia pesagem
        inscricoes.update(status_inscricao='pendente')
        messages.info(request, f'Conferência salva com sucesso! Status: PENDENTE. Inscrições permanecem pendentes.')
    
    # Registrar no histórico
    registrar_historico(
        tipo_acao='CONFERENCIA_PAGAMENTO',
        descricao=f'Conferência de pagamento: {academia.nome} - Status: {status_conferencia} - Valor esperado: R$ {valor_esperado} - Valor recebido: R$ {valor_recebido_decimal or 0}',
        usuario=request.user,
        campeonato=campeonato,
        academia=academia,
        dados_extras={'status': status_conferencia, 'valor_esperado': str(valor_esperado), 'valor_recebido': str(valor_recebido_decimal) if valor_recebido_decimal else None},
        request=request
    )
    
    return redirect('conferencia_pagamentos_detalhe', academia_id=academia_id, campeonato_id=campeonato_id)


@operacional_required
def gerar_mensagem_whatsapp(request, academia_id, campeonato_id):
    """Gera mensagem automática para WhatsApp baseada no status"""
    academia = get_object_or_404(Academia, id=academia_id)
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Buscar conferência ou usar dados do formulário
    conferencia = ConferenciaPagamento.objects.filter(
        academia=academia,
        campeonato=campeonato
    ).first()
    
    # Se não houver conferência, usar dados do formulário ou calcular valores esperados
    if not conferencia:
        # Tentar pegar dados do formulário se disponível
        status_form = request.GET.get('status', 'PENDENTE')
        valor_recebido_form = request.GET.get('valor_recebido', '')
        valor_esperado, qtd_atletas = calcular_valor_esperado_academia(academia, campeonato)
        
        # Usar valores do formulário ou padrão
        valor_esperado_decimal = valor_esperado
        try:
            valor_recebido_decimal = Decimal(valor_recebido_form.replace(',', '.')) if valor_recebido_form else None
        except:
            valor_recebido_decimal = None
        
        # Determinar status para mensagem
        status_para_mensagem = status_form
    else:
        valor_esperado_decimal = conferencia.valor_esperado
        valor_recebido_decimal = conferencia.valor_recebido
        status_para_mensagem = conferencia.status
    
    contato_nome = academia.responsavel or 'Professor'
    contato_whatsapp = academia.telefone or ''
    
    # Gerar mensagem baseada no status
    if status_para_mensagem == 'CONFIRMADO':
        mensagem = (
            f"Olá {contato_nome}, o pagamento das inscrições da sua academia ({academia.nome}) "
            f"no evento {campeonato.nome} foi confirmado. Seus atletas já estão liberados no sistema."
        )
    elif status_para_mensagem == 'DIVERGENTE':
        valor_esperado = f"R$ {valor_esperado_decimal:.2f}".replace('.', ',')
        valor_recebido = f"R$ {valor_recebido_decimal:.2f}".replace('.', ',') if valor_recebido_decimal else "R$ 0,00"
        
        mensagem = (
            f"Olá {contato_nome}, o valor recebido não bate com o total das inscrições "
            f"(Esperado: {valor_esperado} / Recebido: {valor_recebido}). "
            f"Verifique se algum atleta deve ser removido ou adicionado e reenviar o valor correto, por favor."
        )
    else:  # PENDENTE
        valor_esperado = f"R$ {valor_esperado_decimal:.2f}".replace('.', ',')
        mensagem = (
            f"Olá {contato_nome}, não localizei o pagamento referente às inscrições do evento {campeonato.nome}. "
            f"O valor esperado é {valor_esperado}. Por favor, revise o envio e me confirme novamente."
        )
    
    # URL do WhatsApp
    import urllib.parse
    whatsapp_limpo = contato_whatsapp.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    mensagem_encoded = urllib.parse.quote(mensagem)
    whatsapp_url = f"https://wa.me/{whatsapp_limpo}?text={mensagem_encoded}"
    
    return JsonResponse({
        'success': True,
        'mensagem': mensagem,
        'whatsapp_url': whatsapp_url,
        'contato_whatsapp': contato_whatsapp,
    })

