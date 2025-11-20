"""
Views para login independente de academias.
Sistema de autenticação separado do sistema de usuários Django.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.http import require_http_methods
from atletas.models import Academia
from .models import Evento, EventoAtleta
from datetime import date


@require_http_methods(["GET", "POST"])
def academia_login(request):
    """Login independente para academias"""
    # ✅ NOVO: Se já está logado, redirecionar para o painel
    if request.session.get('academia_id'):
        return redirect('eventos:academia_painel')
    
    if request.method == 'POST':
        usuario = request.POST.get('usuario', '').strip()
        senha = request.POST.get('senha', '').strip()
        
        if not usuario or not senha:
            messages.error(request, 'Preencha usuário e senha.')
            return render(request, 'eventos/academia/login.html')
        
        # ✅ CORRIGIDO: Buscar academia por usuario_acesso (case-insensitive)
        try:
            academia = Academia.objects.get(usuario_acesso__iexact=usuario)
        except Academia.DoesNotExist:
            messages.error(request, 'Usuário ou senha incorretos.')
            return render(request, 'eventos/academia/login.html')
        except Academia.MultipleObjectsReturned:
            # Se houver múltiplas academias com mesmo usuário, pegar a primeira
            academia = Academia.objects.filter(usuario_acesso__iexact=usuario).first()
        
        # ✅ CORRIGIDO: Verificar senha (hash) - lógica simplificada
        senha_valida = False
        
        if not academia.senha_acesso:
            # Se não tem senha_acesso, verificar senha_externa (legado)
            if academia.senha_externa == senha:
                # Migrar para senha_acesso (hash)
                academia.senha_acesso = make_password(senha)
                academia.save()
                senha_valida = True
        else:
            # Verificar senha hash
            senha_valida = check_password(senha, academia.senha_acesso)
        
        if not senha_valida:
            messages.error(request, 'Usuário ou senha incorretos.')
            return render(request, 'eventos/academia/login.html')
        
        # ✅ NOVO: Login bem-sucedido - salvar na sessão e forçar salvamento
        request.session['academia_id'] = academia.id
        request.session['academia_nome'] = academia.nome
        request.session['academia_autenticada'] = True
        request.session.save()  # Forçar salvamento imediato
        
        messages.success(request, f'Bem-vindo, {academia.nome}!')
        return redirect('eventos:academia_painel')
    
    # GET - mostrar formulário de login
    return render(request, 'eventos/academia/login.html')


def academia_logout(request):
    """Logout de academia"""
    request.session.pop('academia_id', None)
    request.session.pop('academia_nome', None)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('eventos:academia_login')


def academia_painel(request):
    """Painel principal da academia após login"""
    academia_id = request.session.get('academia_id')
    
    # ✅ NOVO: Verificação mais robusta
    if not academia_id:
        messages.error(request, 'Você precisa fazer login para acessar o painel.')
        return redirect('eventos:academia_login')
    
    try:
        academia = Academia.objects.get(id=academia_id)
    except Academia.DoesNotExist:
        # Academia não existe mais, limpar sessão
        request.session.pop('academia_id', None)
        request.session.pop('academia_nome', None)
        messages.error(request, 'Academia não encontrada. Faça login novamente.')
        return redirect('eventos:academia_login')
    
    # Buscar eventos disponíveis para inscrição
    hoje = date.today()
    eventos_disponiveis = Evento.objects.filter(
        ativo=True,
        status='INSCRICOES',
        data_limite_inscricao__gte=hoje
    ).order_by('data_evento')
    
    # ✅ NOVO: Filtrar eventos expirados (não mostrar para inscrição)
    eventos_disponiveis = [e for e in eventos_disponiveis if not e.is_expired]
    
    # Estatísticas da academia
    total_atletas = academia.atletas.count()
    
    # Buscar inscrições recentes
    inscricoes_recentes = EventoAtleta.objects.filter(
        academia=academia
    ).select_related('evento', 'atleta').order_by('-data_inscricao')[:10]
    
    # Ranking anual (somar pontos de todos os eventos)
    from django.db.models import Sum
    pontos_anuais = EventoAtleta.objects.filter(
        academia=academia
    ).aggregate(total=Sum('pontos'))['total'] or 0
    
    # Contar medalhas no ano
    from atletas.models import Chave
    from atletas.services.luta_services import obter_resultados_chave
    
    ouro = prata = bronze = 0
    for chave in Chave.objects.filter(evento__ativo=True):
        resultados = obter_resultados_chave(chave)
        for pos, atleta_id in enumerate(resultados[:3], 1):
            if EventoAtleta.objects.filter(
                evento=chave.evento,
                atleta_id=atleta_id,
                academia=academia
            ).exists():
                if pos == 1:
                    ouro += 1
                elif pos == 2:
                    prata += 1
                elif pos == 3:
                    bronze += 1
    
    context = {
        'academia': academia,
        'eventos_disponiveis': eventos_disponiveis,
        'total_atletas': total_atletas,
        'inscricoes_recentes': inscricoes_recentes,
        'pontos_anuais': pontos_anuais,
        'ouro': ouro,
        'prata': prata,
        'bronze': bronze,
    }
    
    return render(request, 'eventos/academia/painel.html', context)


@require_http_methods(["GET", "POST"])
def academia_trocar_senha(request):
    """
    Tela para trocar senha no primeiro acesso.
    Obrigatória se senha_acesso não estiver configurada.
    """
    academia_id = request.session.get('academia_id')
    
    if not academia_id:
        return redirect('eventos:academia_login')
    
    academia = get_object_or_404(Academia, id=academia_id)
    
    if request.method == 'POST':
        senha_atual = request.POST.get('senha_atual', '').strip()
        senha_nova = request.POST.get('senha_nova', '').strip()
        senha_nova_confirmar = request.POST.get('senha_nova_confirmar', '').strip()
        
        # Validar campos
        if not senha_nova:
            messages.error(request, 'A nova senha é obrigatória.')
            return render(request, 'eventos/academia/trocar_senha.html', {'academia': academia})
        
        if senha_nova != senha_nova_confirmar:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'eventos/academia/trocar_senha.html', {'academia': academia})
        
        if len(senha_nova) < 6:
            messages.error(request, 'A senha deve ter pelo menos 6 caracteres.')
            return render(request, 'eventos/academia/trocar_senha.html', {'academia': academia})
        
        # Se já tem senha_acesso, verificar senha atual
        if academia.senha_acesso:
            if not check_password(senha_atual, academia.senha_acesso):
                messages.error(request, 'Senha atual incorreta.')
                return render(request, 'eventos/academia/trocar_senha.html', {'academia': academia})
        # Se não tem senha_acesso, verificar senha_externa (legado)
        elif academia.senha_externa:
            if senha_atual != academia.senha_externa:
                messages.error(request, 'Senha atual incorreta.')
                return render(request, 'eventos/academia/trocar_senha.html', {'academia': academia})
        
        # Atualizar senha
        academia.senha_acesso = make_password(senha_nova)
        academia.save()
        
        # Marcar que a senha foi trocada
        request.session['senha_trocada'] = True
        
        messages.success(request, 'Senha alterada com sucesso!')
        return redirect('eventos:academia_painel')
    
    # GET - mostrar formulário
    return render(request, 'eventos/academia/trocar_senha.html', {
        'academia': academia,
        'primeiro_acesso': not academia.senha_acesso
    })

