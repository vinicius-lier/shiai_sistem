# Importações das views de ajuda
from atletas.views_ajuda import ajuda_manual, ajuda_manual_web, ajuda_documentacao_tecnica

# Importar todas as views principais de um arquivo separado
# Por enquanto, vamos criar stubs para que o sistema rode
# TODO: Restaurar views completas de backup ou recriar

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import (
    Academia, Atleta, Chave, Luta, Inscricao, Campeonato, 
    Categoria, AcademiaPontuacao, Despesa, CadastroOperacional,
    UsuarioOperacional, AcademiaCampeonatoSenha, FormaPagamento, Pagamento
)
from .academia_auth import academia_required, operacional_required, pode_resetar_required, pode_criar_usuarios_required
from .utils import gerar_chave, get_resultados_chave, calcular_pontuacao_academias
from datetime import datetime, timedelta, date
import json

# ========== LOGIN E AUTENTICAÇÃO ==========

def selecionar_tipo_login(request):
    """Página inicial - seleção de tipo de login"""
    return render(request, 'atletas/academia/selecionar_login.html')

def login_operacional(request):
    """Login operacional - exige usuário e senha do Django"""
    if request.session.get('academia_id'):
        return redirect('academia_painel')
    
    if request.user.is_authenticated:
        try:
            perfil = request.user.perfil_operacional
            is_expirado = hasattr(perfil, 'esta_expirado') and perfil.esta_expirado
            if not perfil.ativo or is_expirado:
                django_logout(request)
                if is_expirado:
                    messages.error(request, f'Seu acesso expirou em {perfil.data_expiracao.strftime("%d/%m/%Y")}.')
                else:
                    messages.error(request, 'Seu acesso foi desativado.')
                return render(request, 'atletas/login_operacional.html')
        except UsuarioOperacional.DoesNotExist:
            pass
        return redirect('index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not username or not password:
            messages.error(request, 'Por favor, preencha usuário e senha.')
            return render(request, 'atletas/login_operacional.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            try:
                perfil = user.perfil_operacional
                if not perfil.ativo:
                    messages.error(request, 'Seu acesso foi desativado.')
                    return render(request, 'atletas/login_operacional.html')
                is_expirado = hasattr(perfil, 'esta_expirado') and perfil.esta_expirado
                if is_expirado:
                    messages.error(request, f'Seu acesso expirou em {perfil.data_expiracao.strftime("%d/%m/%Y")}.')
                    return render(request, 'atletas/login_operacional.html')
            except UsuarioOperacional.DoesNotExist:
                UsuarioOperacional.objects.create(
                    user=user,
                    pode_resetar_campeonato=False,
                    pode_criar_usuarios=False,
                    data_expiracao=timezone.now() + timedelta(days=30),
                    ativo=True
                )
                messages.info(request, 'Perfil operacional criado. Acesso válido por 30 dias.')
            
            django_login(request, user)
            messages.success(request, f'Bem-vindo, {user.username}!')
            return redirect('index')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
            return render(request, 'atletas/login_operacional.html')
    
    return render(request, 'atletas/login_operacional.html')

def logout_geral(request):
    """Realiza o logout tanto da sessão de academia quanto da sessão operacional"""
    if 'academia_id' in request.session:
        del request.session['academia_id']
    if 'academia_nome' in request.session:
        del request.session['academia_nome']
    
    if request.user.is_authenticated:
        django_logout(request)
    
    if 'operacional_logado' in request.session:
        del request.session['operacional_logado']
    
    request.session.flush()
    request.session.delete()
    
    response = redirect('selecionar_tipo_login')
    response.delete_cookie('sessionid')
    response.delete_cookie('csrftoken')
    
    messages.success(request, 'Logout realizado com sucesso.')
    return response

def academia_login(request):
    """Login da academia - APENAS credenciais temporárias por evento"""
    if request.method == 'POST':
        login = request.POST.get('login', '').strip().upper()  # Converter para maiúsculas
        senha = request.POST.get('senha', '').strip()
        
        if not login or not senha:
            messages.error(request, 'Por favor, preencha login e senha.')
            return render(request, 'atletas/academia/login.html')
        
        # Buscar credencial temporária pelo login gerado
        # Primeiro tenta buscar no campeonato ativo, depois em qualquer campeonato
        credencial = None
        campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
        
        if campeonato_ativo:
            # Tentar buscar no campeonato ativo primeiro
            try:
                credencial = AcademiaCampeonatoSenha.objects.select_related('academia', 'campeonato').get(
                    login__iexact=login,
                    campeonato=campeonato_ativo
                )
            except AcademiaCampeonatoSenha.DoesNotExist:
                pass
            except AcademiaCampeonatoSenha.MultipleObjectsReturned:
                # Se houver múltiplas, pegar a mais recente do campeonato ativo
                credencial = AcademiaCampeonatoSenha.objects.select_related('academia', 'campeonato').filter(
                    login__iexact=login,
                    campeonato=campeonato_ativo
                ).order_by('-data_criacao').first()
        
        # Se não encontrou no campeonato ativo, buscar em qualquer campeonato
        if not credencial:
            try:
                credencial = AcademiaCampeonatoSenha.objects.select_related('academia', 'campeonato').filter(
                    login__iexact=login
                ).order_by('-data_criacao').first()  # Pegar a mais recente
            except Exception as e:
                messages.error(request, f'Erro ao buscar credenciais: {str(e)}')
                return render(request, 'atletas/academia/login.html')
        
        if not credencial:
            messages.error(request, f'Login "{login}" não encontrado. Verifique se o login está correto.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar se está expirado
        if credencial.esta_expirado:
            messages.error(request, 'O acesso temporário da sua academia expirou. Para acessar novos eventos, aguarde o envio de novo convite.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar senha
        if not credencial.verificar_senha(senha):
            messages.error(request, 'Senha incorreta. Verifique se digitou corretamente.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar se academia está ativa
        if not credencial.academia.ativo_login:
            messages.error(request, 'Academia inativa. Entre em contato com o organizador.')
            return render(request, 'atletas/academia/login.html')
        
        # Verificar se o campeonato está ativo
        if not credencial.campeonato.ativo:
            messages.warning(request, f'O campeonato "{credencial.campeonato.nome}" não está ativo no momento.')
            # Mesmo assim permite o login para visualizar dados
        
        # Login válido - criar sessão
        request.session['academia_id'] = credencial.academia.id
        request.session['academia_nome'] = credencial.academia.nome
        request.session['campeonato_id_ativo'] = credencial.campeonato.id
        request.session['campeonato_nome_ativo'] = credencial.campeonato.nome
        request.session['credencial_id'] = credencial.id
        
        # Marcar como enviado se ainda não foi
        if not credencial.enviado_whatsapp:
            credencial.enviado_whatsapp = True
            credencial.data_envio_whatsapp = timezone.now()
            credencial.save()
        
        messages.success(request, f'Bem-vindo, {credencial.academia.nome}!')
        return redirect('academia_painel')
    
    return render(request, 'atletas/academia/login.html')

def academia_logout(request):
    """Logout da academia"""
    if 'academia_id' in request.session:
        del request.session['academia_id']
    if 'academia_nome' in request.session:
        del request.session['academia_nome']
    if 'campeonato_id_ativo' in request.session:
        del request.session['campeonato_id_ativo']
    if 'campeonato_nome_ativo' in request.session:
        del request.session['campeonato_nome_ativo']
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('selecionar_tipo_login')

# ========== DASHBOARD E PÁGINAS PRINCIPAIS ==========

@operacional_required
def index(request):
    """Página inicial - Dashboard"""
    if request.session.get('academia_id'):
        return redirect('academia_painel')
    
    if not request.user.is_authenticated:
        return redirect('login_operacional')
    
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    # Estatísticas básicas
    total_atletas = Atleta.objects.count()
    total_academias = Academia.objects.count()
    total_inscricoes = Inscricao.objects.filter(campeonato=campeonato_ativo).count() if campeonato_ativo else 0
    total_chaves = Chave.objects.filter(campeonato=campeonato_ativo).count() if campeonato_ativo else 0
    
    # Ranking top 5
    top_academias = AcademiaPontuacao.objects.filter(
        campeonato=campeonato_ativo
    ).order_by('-pontos_totais')[:5] if campeonato_ativo else []
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'total_atletas': total_atletas,
        'total_academias': total_academias,
        'total_inscricoes': total_inscricoes,
        'total_chaves': total_chaves,
        'top_academias': top_academias,
    }
    
    return render(request, 'atletas/index.html', context)

# ========== STUBS PARA VIEWS NECESSÁRIAS ==========
# Estas views precisam ser implementadas completamente
# Por enquanto, retornam mensagens de erro ou redirecionam

def lista_academias(request):
    return render(request, 'atletas/lista_academias.html', {'academias': Academia.objects.all()})

@operacional_required
def cadastrar_academia(request):
    """Cadastrar nova academia - SEM campos de login/senha"""
    if request.method == 'POST':
        try:
            academia = Academia.objects.create(
                nome=request.POST.get('nome', '').strip(),
                cidade=request.POST.get('cidade', '').strip(),
                estado=request.POST.get('estado', '').strip().upper(),
                telefone=request.POST.get('telefone', '').strip(),
                responsavel=request.POST.get('responsavel', '').strip(),
                endereco=request.POST.get('endereco', '').strip(),
                bonus_percentual=request.POST.get('bonus_percentual') or None,
                bonus_fixo=request.POST.get('bonus_fixo') or None,
            )
            
            # Upload de foto
            if 'foto_perfil' in request.FILES:
                academia.foto_perfil = request.FILES['foto_perfil']
                academia.save()
            
            messages.success(request, f'Academia "{academia.nome}" cadastrada com sucesso!')
            return redirect('lista_academias')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar academia: {str(e)}')
    
    return render(request, 'atletas/cadastrar_academia.html')

def detalhe_academia(request, academia_id):
    academia = get_object_or_404(Academia, id=academia_id)
    return render(request, 'atletas/detalhe_academia.html', {'academia': academia})

@operacional_required
def editar_academia(request, academia_id):
    """Editar academia - SEM campos de login/senha"""
    academia = get_object_or_404(Academia, id=academia_id)
    
    if request.method == 'POST':
        try:
            academia.nome = request.POST.get('nome', '').strip()
            academia.cidade = request.POST.get('cidade', '').strip()
            academia.estado = request.POST.get('estado', '').strip().upper()
            academia.telefone = request.POST.get('telefone', '').strip()
            academia.responsavel = request.POST.get('responsavel', '').strip()
            academia.endereco = request.POST.get('endereco', '').strip()
            
            if request.POST.get('bonus_percentual'):
                academia.bonus_percentual = request.POST.get('bonus_percentual')
            else:
                academia.bonus_percentual = None
                
            if request.POST.get('bonus_fixo'):
                academia.bonus_fixo = request.POST.get('bonus_fixo')
            else:
                academia.bonus_fixo = None
            
            # Upload de foto (se nova foto foi enviada)
            if 'foto_perfil' in request.FILES:
                academia.foto_perfil = request.FILES['foto_perfil']
            
            academia.save()
            messages.success(request, f'Academia "{academia.nome}" atualizada com sucesso!')
            return redirect('lista_academias')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar academia: {str(e)}')
    
    return render(request, 'atletas/editar_academia.html', {'academia': academia})

def lista_categorias(request):
    return render(request, 'atletas/lista_categorias.html', {'categorias': Categoria.objects.all()})

def cadastrar_categoria(request):
    return render(request, 'atletas/cadastrar_categoria.html')

def lista_atletas(request):
    return render(request, 'atletas/lista_atletas.html', {'atletas': Atleta.objects.all()})

@operacional_required
def cadastrar_atleta(request):
    """Cadastrar novo atleta"""
    if request.method == 'POST':
        try:
            nome = request.POST.get('nome', '').strip()
            data_nascimento = request.POST.get('data_nascimento')
            sexo = request.POST.get('sexo')
            academia_id = request.POST.get('academia')
            federado = request.POST.get('federado') == 'on'
            faixa = request.POST.get('faixa', '').strip() or None
            numero_zempo = request.POST.get('numero_zempo', '').strip() or None
            
            if not nome or not data_nascimento or not sexo or not academia_id:
                messages.error(request, 'Preencha todos os campos obrigatórios.')
            else:
                academia = get_object_or_404(Academia, id=academia_id)
                
                atleta = Atleta.objects.create(
                    nome=nome,
                    data_nascimento=data_nascimento,
                    sexo=sexo,
                    academia=academia,
                    federado=federado,
                    faixa=faixa,
                    numero_zempo=numero_zempo,
                )
                
                # Upload de foto
                if 'foto_perfil' in request.FILES:
                    atleta.foto_perfil = request.FILES['foto_perfil']
                
                # Upload de documento oficial
                if 'documento_oficial' in request.FILES:
                    atleta.documento_oficial = request.FILES['documento_oficial']
                
                atleta.save()
                
                messages.success(request, f'Atleta "{atleta.nome}" cadastrado com sucesso!')
                return redirect('lista_atletas')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar atleta: {str(e)}')
    
    # GET: Buscar academias para o select
    academias = Academia.objects.filter(ativo_login=True).order_by('nome')
    return render(request, 'atletas/cadastrar_atleta.html', {'academias': academias})

@operacional_required
def editar_atleta(request, atleta_id):
    """Editar atleta existente"""
    atleta = get_object_or_404(Atleta, id=atleta_id)
    
    if request.method == 'POST':
        try:
            atleta.nome = request.POST.get('nome', '').strip()
            atleta.data_nascimento = request.POST.get('data_nascimento')
            atleta.sexo = request.POST.get('sexo')
            academia_id = request.POST.get('academia')
            atleta.federado = request.POST.get('federado') == 'on'
            atleta.faixa = request.POST.get('faixa', '').strip() or None
            atleta.numero_zempo = request.POST.get('numero_zempo', '').strip() or None
            
            if academia_id:
                atleta.academia = get_object_or_404(Academia, id=academia_id)
            
            # Upload de foto
            if 'foto_perfil' in request.FILES:
                atleta.foto_perfil = request.FILES['foto_perfil']
            
            # Upload de documento oficial
            if 'documento_oficial' in request.FILES:
                atleta.documento_oficial = request.FILES['documento_oficial']
            
            atleta.save()
            messages.success(request, f'Atleta "{atleta.nome}" atualizado com sucesso!')
            return redirect('lista_atletas')
        except Exception as e:
            messages.error(request, f'Erro ao atualizar atleta: {str(e)}')
    
    # GET: Buscar academias para o select
        academias = Academia.objects.filter(ativo_login=True).order_by('nome')
    return render(request, 'atletas/editar_atleta.html', {
        'atleta': atleta,
        'academias': academias
    })

def cadastrar_festival(request):
    return render(request, 'atletas/cadastrar_festival.html')

def importar_atletas(request):
    return render(request, 'atletas/importar_atletas.html')

def get_categorias_ajax(request):
    return JsonResponse({'categorias': []})

def get_categorias_por_sexo(request):
    return JsonResponse({'categorias': []})

@operacional_required
def pesagem(request):
    """Página de pesagem - lista inscrições do campeonato ativo"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/pesagem.html', {
            'atletas': [],
            'campeonato_ativo': None,
            'classes': [],
            'categorias': [],
        })
    
    # Buscar inscrições aprovadas do campeonato ativo
    inscricoes = Inscricao.objects.filter(
        campeonato=campeonato_ativo,
        status_inscricao='aprovado'
    ).select_related('atleta', 'atleta__academia').order_by('atleta__nome')
    
    # Aplicar filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    if classe_filtro:
        inscricoes = inscricoes.filter(classe_escolhida=classe_filtro)
    if sexo_filtro:
        inscricoes = inscricoes.filter(atleta__sexo=sexo_filtro)
    if categoria_filtro:
        inscricoes = inscricoes.filter(categoria_escolhida=categoria_filtro)
    
    # Preparar dados para o template
    atletas = []
    for inscricao in inscricoes:
        atleta = inscricao.atleta
        
        # Buscar categoria para obter limite
        limite_categoria = '-'
        categoria_nome = inscricao.categoria_ajustada or inscricao.categoria_escolhida or ''
        if categoria_nome:
            try:
                categoria = Categoria.objects.filter(categoria_nome=categoria_nome).first()
                if categoria:
                    limite_categoria = f"{categoria.limite_min:.1f} - {categoria.limite_max:.1f} kg"
            except:
                pass
        
        # Criar objeto com atributos necessários
        atleta_pesagem = type('AtletaPesagem', (), {
            'id': atleta.id,
            'inscricao_id': inscricao.id,
            'nome': atleta.nome,
            'academia': atleta.academia,
            'sexo': atleta.sexo,
            'classe': inscricao.classe_escolhida or atleta.get_classe_atual(),
            'categoria_nome': inscricao.categoria_escolhida or '',
            'categoria_ajustada': inscricao.categoria_ajustada or '',
            'peso_oficial': inscricao.peso,
            'remanejado': inscricao.remanejado,
            'status': 'OK' if inscricao.peso else 'Pendente',
            'get_sexo_display': lambda: atleta.get_sexo_display(),
            'get_limite_categoria': lambda: limite_categoria,
        })()
        
        atletas.append(atleta_pesagem)
    
    # Obter classes e categorias disponíveis
    classes = sorted(set([insc.classe_escolhida for insc in Inscricao.objects.filter(campeonato=campeonato_ativo, status_inscricao='aprovado').exclude(classe_escolhida='').values_list('classe_escolhida', flat=True)]))
    categorias = sorted(set([insc.categoria_escolhida for insc in Inscricao.objects.filter(campeonato=campeonato_ativo, status_inscricao='aprovado').exclude(categoria_escolhida='').values_list('categoria_escolhida', flat=True)]))
    
    context = {
        'atletas': atletas,
        'campeonato_ativo': campeonato_ativo,
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/pesagem.html', context)

def pesagem_mobile_view(request):
    return render(request, 'atletas/pesagem_mobile.html')

def registrar_peso(request, inscricao_id):
    return JsonResponse({'success': False})

def confirmar_remanejamento(request, inscricao_id):
    return JsonResponse({'success': False})

def rebaixar_categoria(request, atleta_id):
    return JsonResponse({'success': False})

@operacional_required
def lista_chaves(request):
    """Lista todas as chaves do campeonato ativo"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/lista_chaves.html', {
            'chaves': [],
            'campeonato_ativo': None,
            'total_chaves': 0,
            'classes': [],
            'categorias': [],
        })
    
    # Buscar chaves do campeonato ativo
    chaves_query = Chave.objects.filter(campeonato=campeonato_ativo).select_related('campeonato').order_by('classe', 'sexo', 'categoria')
    
    # Aplicar filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    if classe_filtro:
        chaves_query = chaves_query.filter(classe=classe_filtro)
    if sexo_filtro:
        chaves_query = chaves_query.filter(sexo=sexo_filtro)
    if categoria_filtro:
        chaves_query = chaves_query.filter(categoria=categoria_filtro)
    
    chaves = list(chaves_query)
    
    # Obter classes, sexos e categorias disponíveis
    classes = sorted(set([ch.classe for ch in Chave.objects.filter(campeonato=campeonato_ativo).exclude(classe='').values_list('classe', flat=True)]))
    categorias = sorted(set([ch.categoria for ch in Chave.objects.filter(campeonato=campeonato_ativo).exclude(categoria='').values_list('categoria', flat=True)]))
    
    context = {
        'chaves': chaves,
        'campeonato_ativo': campeonato_ativo,
        'total_chaves': len(chaves),
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/lista_chaves.html', context)

def gerar_chave_view(request):
    return render(request, 'atletas/gerar_chave.html')

def gerar_chave_manual(request):
    return render(request, 'atletas/gerar_chave_manual.html')

def detalhe_chave(request, chave_id):
    chave = get_object_or_404(Chave, id=chave_id)
    return render(request, 'atletas/detalhe_chave.html', {'chave': chave})

def imprimir_chave(request, chave_id):
    return render(request, 'atletas/imprimir_chave.html', {'chave': get_object_or_404(Chave, id=chave_id)})

def chave_mobile_view(request, chave_id):
    return render(request, 'atletas/chave_mobile.html', {'chave': get_object_or_404(Chave, id=chave_id)})

def registrar_vencedor(request, luta_id):
    return JsonResponse({'success': False})

def luta_mobile_view(request, luta_id):
    return render(request, 'atletas/luta_mobile.html', {'luta': get_object_or_404(Luta, id=luta_id)})

@operacional_required
def ranking_global(request):
    """Ranking global de atletas e academias"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/ranking_global.html', {
            'campeonato_ativo': None,
            'ranking_atletas_completo': [],
            'top3_academias': [],
            'total_academias': 0,
            'classes_disponiveis': [],
            'categorias_disponiveis': [],
        })
    
    # Aplicar filtros
    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    # Calcular pontuação das academias primeiro
    calcular_pontuacao_academias(campeonato_ativo.id)
    
    # Buscar pontuações de academias
    pontuacoes = AcademiaPontuacao.objects.filter(
        campeonato=campeonato_ativo
    ).select_related('academia').order_by('-pontos_totais', '-ouro', '-prata', '-bronze')
    
    top3_academias = []
    for pontuacao in pontuacoes[:3]:
        top3_academias.append({
            'academia': pontuacao.academia,
            'ouro': pontuacao.ouro,
            'prata': pontuacao.prata,
            'bronze': pontuacao.bronze,
            'pontos_totais': pontuacao.pontos_totais,
        })
    
    # Buscar resultados de todas as chaves para calcular ranking de atletas
    chaves = Chave.objects.filter(campeonato=campeonato_ativo)
    
    # Contar medalhas por atleta
    medalhas_por_atleta = {}
    
    for chave in chaves:
        resultados = get_resultados_chave(chave)
        if not resultados:
            continue
        
        # 1º lugar = ouro, 2º lugar = prata, 3º lugar = bronze
        for idx, atleta_id in enumerate(resultados[:3], 1):
            if not atleta_id:
                continue
            
            if atleta_id not in medalhas_por_atleta:
                try:
                    atleta = Atleta.objects.get(id=atleta_id)
                    medalhas_por_atleta[atleta_id] = {
                        'atleta': atleta,
                        'ouro': 0,
                        'prata': 0,
                        'bronze': 0,
                        'total_medalhas': 0,
                    }
                except Atleta.DoesNotExist:
                    continue
            
            if idx == 1:
                medalhas_por_atleta[atleta_id]['ouro'] += 1
            elif idx == 2:
                medalhas_por_atleta[atleta_id]['prata'] += 1
            elif idx == 3:
                medalhas_por_atleta[atleta_id]['bronze'] += 1
            
            medalhas_por_atleta[atleta_id]['total_medalhas'] = (
                medalhas_por_atleta[atleta_id]['ouro'] +
                medalhas_por_atleta[atleta_id]['prata'] +
                medalhas_por_atleta[atleta_id]['bronze']
            )
    
    # Ordenar por total de medalhas (ouro > prata > bronze)
    ranking_atletas_completo = sorted(
        medalhas_por_atleta.values(),
        key=lambda x: (x['total_medalhas'], x['ouro'], x['prata'], x['bronze']),
        reverse=True
    )
    
    # Obter classes e categorias disponíveis
    classes_disponiveis = sorted(set([ch.classe for ch in chaves.exclude(classe='').values_list('classe', flat=True)]))
    categorias_disponiveis = sorted(set([ch.categoria for ch in chaves.exclude(categoria='').values_list('categoria', flat=True)]))
    
    context = {
        'campeonato_ativo': campeonato_ativo,
        'ranking_atletas_completo': ranking_atletas_completo,
        'top3_academias': top3_academias,
        'total_academias': pontuacoes.count(),
        'classes_disponiveis': classes_disponiveis,
        'categorias_disponiveis': categorias_disponiveis,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/ranking_global.html', context)

@operacional_required
def ranking_academias(request):
    """Ranking de academias - calcula pontuação baseada em resultados"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if not campeonato_ativo:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
        return render(request, 'atletas/ranking_academias.html', {
            'campeonato_ativo': None,
            'ranking_academias': [],
            'top3_academias': [],
            'total_academias': 0,
        })
    
    # Calcular pontuação das academias
    calcular_pontuacao_academias(campeonato_ativo.id)
    
    # Buscar pontuações do campeonato
    pontuacoes = AcademiaPontuacao.objects.filter(
        campeonato=campeonato_ativo
    ).select_related('academia').order_by('-pontos_totais', '-ouro', '-prata', '-bronze')
    
    # Preparar dados para o template
    ranking_academias_list = []
    for pontuacao in pontuacoes:
        ranking_academias_list.append({
            'academia': pontuacao.academia,
            'ouro': pontuacao.ouro,
            'prata': pontuacao.prata,
            'bronze': pontuacao.bronze,
            'quarto': pontuacao.quarto,
            'quinto': pontuacao.quinto,
            'festival': pontuacao.festival,
            'remanejamento': pontuacao.remanejamento,
            'pontos_totais': pontuacao.pontos_totais,
        })
    
    # Top 3 academias
    top3_academias = ranking_academias_list[:3]
    
    context = {
        'campeonato': campeonato_ativo,
        'academias_ranking': ranking_academias_list,
        'top3': top3_academias,
        'total_academias': len(ranking_academias_list),
    }
    
    return render(request, 'atletas/ranking_academias.html', context)

@operacional_required
def calcular_pontuacao(request):
    """Recalcular pontuação das academias e redirecionar para ranking"""
    campeonato_ativo = Campeonato.objects.filter(ativo=True).first()
    
    if campeonato_ativo:
        calcular_pontuacao_academias(campeonato_ativo.id)
        messages.success(request, 'Pontuação recalculada com sucesso!')
    else:
        messages.warning(request, 'Nenhum campeonato ativo encontrado.')
    
    return redirect('ranking_academias')

def api_ranking_academias(request):
    return JsonResponse({'academias': []})

def perfil_atleta(request, atleta_id):
    return render(request, 'atletas/perfil_atleta.html', {'atleta': get_object_or_404(Atleta, id=atleta_id)})

def inscrever_atletas(request):
    return render(request, 'atletas/inscrever_atletas.html')

def metricas_evento(request):
    return render(request, 'atletas/metricas_evento.html')

def dashboard(request):
    return render(request, 'atletas/dashboard.html')

def relatorio_atletas_inscritos(request):
    return render(request, 'atletas/relatorio_atletas_inscritos.html')

def relatorio_pesagem_final(request):
    return render(request, 'atletas/relatorio_pesagem_final.html')

def relatorio_chaves(request):
    return render(request, 'atletas/relatorio_chaves.html')

def relatorio_resultados_categoria(request):
    return render(request, 'atletas/relatorio_resultados_categoria.html')

class ResetCompeticaoAPIView(APIView):
    @pode_resetar_required
    def post(self, request, *args, **kwargs):
        return Response({"detail": "Funcionalidade em desenvolvimento"}, status=status.HTTP_501_NOT_IMPLEMENTED)

@operacional_required
def lista_campeonatos(request):
    """Lista campeonatos e exibe credenciais geradas se houver"""
    campeonatos = Campeonato.objects.all()
    
    # Verificar se há credenciais na sessão (após criar campeonato)
    credenciais_campeonato = request.session.pop('credenciais_campeonato', None)
    
    context = {
        'campeonatos': campeonatos,
    }
    
    if credenciais_campeonato:
        context['academias_credenciais_campeonato'] = credenciais_campeonato['credenciais']
        context['campeonato_criado'] = {
            'id': credenciais_campeonato['campeonato_id'],
            'nome': credenciais_campeonato['campeonato_nome']
        }
    
    return render(request, 'atletas/lista_campeonatos.html', context)

@operacional_required
def cadastrar_campeonato(request):
    """Cadastrar novo campeonato"""
    from .forms import CampeonatoForm
    
    formas_pagamento = FormaPagamento.objects.filter(ativo=True).order_by('tipo', 'nome')
    
    if request.method == "POST":
        form = CampeonatoForm(request.POST, request.FILES)
        if form.is_valid():
            campeonato = form.save()
            
            # Se marcou como ativo, desativar outros
            if campeonato.ativo:
                Campeonato.objects.exclude(id=campeonato.id).update(ativo=False)
            
            # Gerar senhas para academias
            from datetime import timedelta
            academias_ativas = Academia.objects.filter(ativo_login=True)
            
            for academia in academias_ativas:
                # Gerar login e senha
                import random
                import string
                login = f"ACADEMIA_{academia.id:03d}"
                senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Calcular data de expiração (5 dias após término do campeonato)
                data_expiracao = None
                if campeonato.data_competicao:
                    data_expiracao = timezone.make_aware(
                        datetime.combine(campeonato.data_competicao, datetime.min.time())
                    ) + timedelta(days=5)
                
                # Criar ou atualizar senha
                senha_obj, created = AcademiaCampeonatoSenha.objects.get_or_create(
                    academia=academia,
                    campeonato=campeonato,
                    defaults={
                        'login': login,
                        'senha_plana': senha_plana,
                        'data_expiracao': data_expiracao,
                    }
                )
                
                if not created:
                    senha_obj.login = login
                    senha_obj.senha_plana = senha_plana
                    senha_obj.data_expiracao = data_expiracao
                    senha_obj.save()
                
                senha_obj.definir_senha(senha_plana)
                senha_obj.save()
            
            messages.success(request, "Campeonato cadastrado com sucesso!")
            return redirect('lista_campeonatos')
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = CampeonatoForm()
    
    return render(request, 'atletas/cadastrar_campeonato.html', {
        'form': form,
        'formas_pagamento': formas_pagamento
    })
    """Cadastrar campeonato e gerar credenciais temporárias para todas as academias"""
    if request.method == 'POST':
        try:
            from decimal import Decimal
            import random
            import string
            
            # Criar campeonato
            campeonato = Campeonato.objects.create(
                nome=request.POST.get('nome', '').strip(),
                data_inicio=request.POST.get('data_inicio') or None,
                data_competicao=request.POST.get('data_competicao') or None,
                data_limite_inscricao=request.POST.get('data_limite_inscricao') or None,
                ativo=request.POST.get('ativo') == 'on',
                regulamento=request.POST.get('regulamento', '').strip(),
                valor_inscricao_federado=request.POST.get('valor_inscricao_federado') or None,
                valor_inscricao_nao_federado=request.POST.get('valor_inscricao_nao_federado') or None,
            )
            
            # Se outro campeonato estava ativo, desativar
            if campeonato.ativo:
                Campeonato.objects.exclude(id=campeonato.id).update(ativo=False)
            
            # Gerar credenciais temporárias para todas as academias
            academias = Academia.objects.filter(ativo_login=True)
            credenciais_geradas = []
            
            for academia in academias:
                # Gerar login único: ACADEMIA_XXX (onde XXX é o ID da academia)
                login = f"ACADEMIA_{academia.id:03d}"
                
                # Gerar senha aleatória de 8 caracteres
                senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Calcular data de expiração: 5 dias após término do campeonato
                data_expiracao = None
                if campeonato.data_competicao:
                    data_expiracao = campeonato.data_competicao + timedelta(days=5)
                
                # Criar ou atualizar credencial
                credencial, created = AcademiaCampeonatoSenha.objects.get_or_create(
                    academia=academia,
                    campeonato=campeonato,
                    defaults={
                        'login': login,
                        'senha_plana': senha_plana,
                        'data_expiracao': data_expiracao,
                    }
                )
                
                # Sempre atualizar login, senha e expiração (mesmo se já existir)
                credencial.login = login
                credencial.senha_plana = senha_plana
                credencial.data_expiracao = data_expiracao
                
                # Definir senha (criptografa) - IMPORTANTE: fazer ANTES do save
                credencial.definir_senha(senha_plana)
                credencial.save()
                
                credenciais_geradas.append({
                    'academia': academia,
                    'login': login,
                    'senha': senha_plana,
                    'telefone': academia.telefone,
                    'responsavel': academia.responsavel,
                })
            
            # Armazenar credenciais na sessão para exibição
            request.session['credenciais_campeonato'] = {
                'campeonato_id': campeonato.id,
                'campeonato_nome': campeonato.nome,
                'credenciais': credenciais_geradas
            }
            
            messages.success(request, f'Campeonato "{campeonato.nome}" criado com sucesso! Credenciais temporárias geradas para {len(credenciais_geradas)} academias.')
            return redirect('lista_campeonatos')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar campeonato: {str(e)}')
    
    return render(request, 'atletas/cadastrar_campeonato.html', {
        'formas_pagamento': formas_pagamento
    })

@operacional_required
def editar_campeonato(request, campeonato_id):
    """Editar campeonato"""
    from .forms import CampeonatoForm
    
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    if request.method == "POST":
        form = CampeonatoForm(request.POST, request.FILES, instance=campeonato)
        if form.is_valid():
            campeonato = form.save()
            
            # Se marcou como ativo, desativar outros
            if campeonato.ativo:
                Campeonato.objects.exclude(id=campeonato.id).update(ativo=False)
            
            messages.success(request, "Alterações salvas com sucesso.")
            return redirect('lista_campeonatos')
        else:
            messages.error(request, "Por favor, corrija os erros abaixo.")
    else:
        form = CampeonatoForm(instance=campeonato)
    
    return render(request, 'atletas/editar_campeonato.html', {
        'form': form,
        'campeonato': campeonato
    })

@operacional_required
def definir_campeonato_ativo(request, campeonato_id):
    """Ativar um campeonato (desativa os outros automaticamente)"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Desativar todos os outros campeonatos
    Campeonato.objects.exclude(id=campeonato.id).update(ativo=False)
    
    # Ativar o campeonato selecionado
    campeonato.ativo = True
    campeonato.save()
    
    messages.success(request, f'Campeonato "{campeonato.nome}" ativado com sucesso!')
    return redirect('lista_campeonatos')

@operacional_required
def gerenciar_senhas_campeonato(request, campeonato_id):
    """Gerenciar senhas temporárias do campeonato"""
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Buscar todas as credenciais do campeonato
    credenciais = AcademiaCampeonatoSenha.objects.filter(
        campeonato=campeonato
    ).select_related('academia').order_by('academia__nome')
    
    academias_com_senhas = []
    for credencial in credenciais:
        academias_com_senhas.append({
            'academia': credencial.academia,
            'login': credencial.login,
            'senha_plana': credencial.senha_plana,
            'telefone': credencial.academia.telefone,
            'responsavel': credencial.academia.responsavel,
            'enviado_whatsapp': credencial.enviado_whatsapp,
            'data_envio': credencial.data_envio_whatsapp,
            'data_expiracao': credencial.data_expiracao,
            'esta_expirado': credencial.esta_expirado,
            'credencial_id': credencial.id,
        })
    
    # Se não há credenciais, gerar para todas as academias
    if not academias_com_senhas:
        import random
        import string
        academias = Academia.objects.filter(ativo_login=True)
        
        for academia in academias:
            login = f"ACADEMIA_{academia.id:03d}"
            senha_plana = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            data_expiracao = None
            if campeonato.data_competicao:
                data_expiracao = campeonato.data_competicao + timedelta(days=5)
            
            credencial = AcademiaCampeonatoSenha(
                academia=academia,
                campeonato=campeonato,
                login=login,
                senha_plana=senha_plana,
                data_expiracao=data_expiracao,
            )
            # Definir senha (criptografa) - IMPORTANTE: fazer ANTES do save
            credencial.definir_senha(senha_plana)
            credencial.save()
            
            academias_com_senhas.append({
                'academia': academia,
                'login': login,
                'senha_plana': senha_plana,
                'telefone': academia.telefone,
                'responsavel': academia.responsavel,
                'enviado_whatsapp': False,
                'data_envio': None,
                'data_expiracao': data_expiracao,
                'esta_expirado': False,
                'credencial_id': credencial.id,
            })
    
    # Processar POST (marcar como enviado)
    if request.method == 'POST' and request.POST.get('marcar_enviado'):
        credencial_id = request.POST.get('credencial_id')
        if credencial_id:
            try:
                credencial = AcademiaCampeonatoSenha.objects.get(id=credencial_id, campeonato=campeonato)
                credencial.enviado_whatsapp = True
                credencial.data_envio_whatsapp = timezone.now()
                credencial.save()
                messages.success(request, 'Status de envio atualizado.')
                return redirect('gerenciar_senhas_campeonato', campeonato_id=campeonato.id)
            except AcademiaCampeonatoSenha.DoesNotExist:
                pass
    
    context = {
        'campeonato': campeonato,
        'academias_com_senhas': academias_com_senhas,
        'data_competicao': campeonato.data_competicao.strftime('%d/%m/%Y') if campeonato.data_competicao else 'Não definida',
        'valor_federado': f"R$ {campeonato.valor_inscricao_federado:.2f}" if campeonato.valor_inscricao_federado else 'Não definido',
        'valor_nao_federado': f"R$ {campeonato.valor_inscricao_nao_federado:.2f}" if campeonato.valor_inscricao_nao_federado else 'Não definido',
    }
    
    return render(request, 'atletas/administracao/gerenciar_senhas_campeonato.html', context)

@academia_required
def academia_painel(request):
    """Painel da academia - lista eventos abertos e encerrados"""
    academia = request.academia
    hoje = timezone.now().date()
    
    # Desativar eventos automaticamente após data da competição
    Campeonato.objects.filter(
        data_competicao__lt=hoje,
        ativo=True
    ).update(ativo=False)
    
    # Buscar credenciais da academia (eventos onde ela tem acesso)
    credenciais = AcademiaCampeonatoSenha.objects.filter(
        academia=academia
    ).select_related('campeonato').order_by('-campeonato__data_competicao', '-id')
    
    # Separar eventos: abertos e encerrados (sem duplicação)
    eventos_abertos = []  # Eventos ativos e abertos para inscrição (data_competicao >= hoje AND ativo = True)
    eventos_encerrados = []  # Eventos encerrados (data_competicao < hoje OR ativo = False)
    
    eventos_processados = set()  # Para evitar duplicações
    
    for credencial in credenciais:
        campeonato = credencial.campeonato
        
        # Evitar processar o mesmo evento duas vezes
        if campeonato.id in eventos_processados:
            continue
        eventos_processados.add(campeonato.id)
        
        # Verificar se o evento está encerrado
        # Encerrado = data_competicao < hoje OU ativo = False
        evento_encerrado = (
            (campeonato.data_competicao and campeonato.data_competicao < hoje) or
            not campeonato.ativo
        )
        
        if evento_encerrado:
            # Evento encerrado - apenas consulta
            eventos_encerrados.append(campeonato)
        else:
            # Evento ativo e aberto
            # Verificar se ainda está aberto para inscrição (se tem data limite)
            aberto_inscricao = True
            if campeonato.data_limite_inscricao:
                if hoje > campeonato.data_limite_inscricao:
                    aberto_inscricao = False
            
            if aberto_inscricao:
                eventos_abertos.append(campeonato)
            else:
                # Fechou inscrições mas ainda é evento ativo (antes da data da competição)
                # Considerar como encerrado para inscrições, mas ainda ativo
                eventos_encerrados.append(campeonato)
    
    # Ordenar por data (mais recente primeiro)
    eventos_abertos.sort(key=lambda x: x.data_competicao or date.min, reverse=True)
    eventos_encerrados.sort(key=lambda x: x.data_competicao or date.min, reverse=True)
    
    context = {
        'academia': academia,
        'eventos_abertos': eventos_abertos,
        'eventos_encerrados': eventos_encerrados,
    }
    
    return render(request, 'atletas/academia/painel.html', context)

@academia_required
def academia_evento(request, campeonato_id):
    """Página do evento para a academia"""
    academia = request.academia
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    hoje = timezone.now().date()
    
    # Verificar se o evento está inativo
    evento_inativo = not campeonato.ativo or (campeonato.data_competicao and campeonato.data_competicao < hoje)
    
    # Buscar inscrições da academia neste campeonato
    inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    )
    
    total_inscritos = inscricoes.count()
    aprovados = inscricoes.filter(status_inscricao='aprovado').count()
    pendentes = inscricoes.filter(status_inscricao='pendente').count()
    
    # Calcular resumo financeiro
    valor_federado = campeonato.valor_inscricao_federado or 0
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
    
    inscricoes_aprovadas = inscricoes.filter(status_inscricao='aprovado')
    valor_confirmado = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_aprovadas
    )
    
    inscricoes_pendentes_list = inscricoes.filter(status_inscricao='pendente')
    valor_pendente = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_pendentes_list
    )
    
    valor_previsto = valor_confirmado + valor_pendente
    
    resumo_financeiro = {
        'valor_previsto': valor_previsto,
        'valor_confirmado': valor_confirmado,
        'valor_pendente': valor_pendente,
        'status': 'Tudo confirmado' if pendentes == 0 else f'{pendentes} pendente(s)',
    }
    
    context = {
        'academia': academia,
        'campeonato': campeonato,
        'evento_inativo': evento_inativo,
        'total_inscritos': total_inscritos,
        'aprovados': aprovados,
        'pendentes': pendentes,
        'resumo_financeiro': resumo_financeiro,
        'valor_inscricao_federado': valor_federado,
        'valor_inscricao_nao_federado': valor_nao_federado,
    }
    
    return render(request, 'atletas/academia/evento.html', context)

@academia_required
def academia_lista_atletas(request, campeonato_id=None):
    """Lista atletas da academia - global ou de um evento específico"""
    academia = request.academia
    
    modo_evento = campeonato_id is not None
    campeonato = None
    atletas = []
    resumo_financeiro = None
    
    if modo_evento:
        # Modo evento: listar atletas inscritos no evento
        campeonato = get_object_or_404(Campeonato, id=campeonato_id)
        
        # Buscar inscrições da academia neste campeonato
        inscricoes = Inscricao.objects.filter(
            atleta__academia=academia,
            campeonato=campeonato
        ).select_related('atleta', 'atleta__academia')
        
        # Preparar dados para o template
        atletas = []
        for inscricao in inscricoes:
            atletas.append({
                'atleta': inscricao.atleta,
                'classe_escolhida': inscricao.classe_escolhida,
                'categoria_escolhida': inscricao.categoria_escolhida,
                'status': inscricao.status_inscricao,
            })
        
        # Calcular resumo financeiro
        total_inscritos = inscricoes.count()
        aprovados = inscricoes.filter(status_inscricao='aprovado').count()
        pendentes = inscricoes.filter(status_inscricao='pendente').count()
        
        # Calcular valores
        valor_federado = campeonato.valor_inscricao_federado or 0
        valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
        
        inscricoes_aprovadas = inscricoes.filter(status_inscricao='aprovado')
        valor_confirmado = sum(
            valor_federado if ins.atleta.federado else valor_nao_federado
            for ins in inscricoes_aprovadas
        )
        
        inscricoes_pendentes = inscricoes.filter(status_inscricao='pendente')
        valor_pendente = sum(
            valor_federado if ins.atleta.federado else valor_nao_federado
            for ins in inscricoes_pendentes
        )
        
        valor_previsto = valor_confirmado + valor_pendente
        
        resumo_financeiro = {
            'quantidade': total_inscritos,
            'aprovados': aprovados,
            'pendentes': pendentes,
            'valor_previsto': valor_previsto,
            'valor_confirmado': valor_confirmado,
            'valor_pendente': valor_pendente,
        }
    else:
        # Modo global: listar todos os atletas da academia
        atletas = Atleta.objects.filter(academia=academia).order_by('nome')
    
    context = {
        'academia': academia,
        'atletas': atletas,
        'modo_evento': modo_evento,
        'campeonato': campeonato,
        'resumo_financeiro': resumo_financeiro,
    }
    
    return render(request, 'atletas/academia/lista_atletas.html', context)

@academia_required
def academia_inscrever_atletas(request, campeonato_id):
    """Inscrever atletas da academia em um campeonato"""
    academia = request.academia
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    hoje = timezone.now().date()
    
    # Verificar se o evento está inativo (bloquear inscrições)
    evento_inativo = not campeonato.ativo or (campeonato.data_competicao and campeonato.data_competicao < hoje)
    
    if evento_inativo:
        messages.warning(request, 'Este evento está inativo. Não é possível fazer novas inscrições, apenas consultar.')
        return redirect('academia_evento', campeonato_id=campeonato_id)
    
    # Processar inscrição via POST
    if request.method == 'POST':
        atleta_id = request.POST.get('atleta_id')
        classe_escolhida = request.POST.get('classe_escolhida')
        categoria_escolhida = request.POST.get('categoria_escolhida')
        
        if atleta_id and classe_escolhida and categoria_escolhida:
            try:
                atleta = Atleta.objects.get(id=atleta_id, academia=academia)
                
                # Verificar se já não está inscrito nesta classe/categoria
                inscricao_existente = Inscricao.objects.filter(
                    atleta=atleta,
                    campeonato=campeonato,
                    classe_escolhida=classe_escolhida,
                    categoria_escolhida=categoria_escolhida
                ).first()
                
                if inscricao_existente:
                    messages.warning(request, f'{atleta.nome} já está inscrito em {classe_escolhida} - {categoria_escolhida}.')
                else:
                    # Criar nova inscrição
                    Inscricao.objects.create(
                        atleta=atleta,
                        campeonato=campeonato,
                        classe_escolhida=classe_escolhida,
                        categoria_escolhida=categoria_escolhida,
                        status_inscricao='pendente'
                    )
                    messages.success(request, f'{atleta.nome} inscrito com sucesso em {classe_escolhida} - {categoria_escolhida}!')
            except Atleta.DoesNotExist:
                messages.error(request, 'Atleta não encontrado.')
            except Exception as e:
                messages.error(request, f'Erro ao inscrever atleta: {str(e)}')
        
        return redirect('academia_inscrever_atletas', campeonato_id=campeonato_id)
    
    # GET: Listar atletas da academia
    nome_filtro = request.GET.get('nome', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    
    # Buscar atletas da academia
    atletas_query = Atleta.objects.filter(academia=academia)
    
    # Aplicar filtros
    if nome_filtro:
        atletas_query = atletas_query.filter(nome__icontains=nome_filtro)
    if sexo_filtro:
        atletas_query = atletas_query.filter(sexo=sexo_filtro)
    
    atletas_query = atletas_query.order_by('nome')
    
    # Preparar dados para o template
    atletas = []
    for atleta in atletas_query:
        # Buscar inscrições deste atleta neste campeonato
        inscricoes = Inscricao.objects.filter(
            atleta=atleta,
            campeonato=campeonato
        )
        
        atletas.append({
            'atleta': atleta,
            'total_inscricoes': inscricoes.count(),
            'inscricoes': inscricoes,
        })
    
    # Calcular resumo financeiro
    todas_inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    )
    
    valor_federado = campeonato.valor_inscricao_federado or 0
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
    
    inscricoes_aprovadas = todas_inscricoes.filter(status_inscricao='aprovado')
    valor_confirmado = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_aprovadas
    )
    
    inscricoes_pendentes = todas_inscricoes.filter(status_inscricao='pendente')
    valor_pendente = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes_pendentes
    )
    
    valor_previsto = valor_confirmado + valor_pendente
    
    resumo_financeiro = {
        'valor_previsto': valor_previsto,
        'valor_confirmado': valor_confirmado,
        'valor_pendente': valor_pendente,
    }
    
    # Buscar todas as categorias para o JavaScript
    todas_categorias = Categoria.objects.all().order_by('classe', 'limite_min')
    
    # Preparar categorias no formato esperado pelo template
    categorias_list = []
    for cat in todas_categorias:
        categorias_list.append({
            'id': cat.id,
            'classe': cat.classe,
            'sexo': cat.sexo,
            'label': cat.label,  # Campo label do modelo
            'categoria_nome': cat.categoria_nome,
        })
    
    context = {
        'academia': academia,
        'campeonato': campeonato,
        'atletas': atletas,
        'nome_filtro': nome_filtro,
        'sexo_filtro': sexo_filtro,
        'resumo_financeiro': resumo_financeiro,
        'valor_inscricao_federado': valor_federado,
        'valor_inscricao_nao_federado': valor_nao_federado,
        'categorias': categorias_list,
    }
    
    return render(request, 'atletas/academia/inscrever_atletas.html', context)

@academia_required
def academia_cadastrar_atleta(request, campeonato_id=None):
    """Cadastrar novo atleta pela academia"""
    academia = request.academia
    
    if request.method == 'POST':
        try:
            nome = request.POST.get('nome', '').strip()
            data_nascimento = request.POST.get('data_nascimento')
            sexo = request.POST.get('sexo')
            federado = request.POST.get('federado') == 'on'
            rg = request.POST.get('rg', '').strip()
            cpf = request.POST.get('cpf', '').strip()
            telefone = request.POST.get('telefone', '').strip()
            email = request.POST.get('email', '').strip()
            observacoes = request.POST.get('observacoes', '').strip()
            
            if not nome or not data_nascimento or not sexo:
                messages.error(request, 'Preencha todos os campos obrigatórios.')
            else:
                atleta = Atleta.objects.create(
                    nome=nome,
                    data_nascimento=data_nascimento,
                    sexo=sexo,
                    academia=academia,  # Sempre vincula à academia logada
                    federado=federado,
                    rg=rg or None,
                    cpf=cpf or None,
                    telefone=telefone or None,
                    email=email or None,
                    observacoes=observacoes or None,
                )
                
                # Upload de foto
                if 'foto_perfil' in request.FILES:
                    atleta.foto_perfil = request.FILES['foto_perfil']
                    atleta.save()
                
                messages.success(request, f'Atleta "{atleta.nome}" cadastrado com sucesso!')
                
                # Se veio de um evento, redirecionar para inscrição
                if campeonato_id:
                    return redirect('academia_inscrever_atletas', campeonato_id=campeonato_id)
                else:
                    return redirect('academia_lista_atletas')
        except Exception as e:
            messages.error(request, f'Erro ao cadastrar atleta: {str(e)}')
    
    # GET: Passar academia e campeonato se houver
    context = {
        'academia': academia,
    }
    
    if campeonato_id:
        context['campeonato'] = get_object_or_404(Campeonato, id=campeonato_id)
    
    return render(request, 'atletas/academia/cadastrar_atleta.html', context)

@academia_required
def academia_ver_chaves(request, campeonato_id):
    return render(request, 'atletas/academia/ver_chaves.html', {'campeonato': get_object_or_404(Campeonato, id=campeonato_id)})

@academia_required
def academia_detalhe_chave(request, campeonato_id, chave_id):
    return render(request, 'atletas/academia/detalhe_chave.html', {
        'campeonato': get_object_or_404(Campeonato, id=campeonato_id),
        'chave': get_object_or_404(Chave, id=chave_id)
    })

@academia_required
def academia_baixar_regulamento(request, campeonato_id):
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    if campeonato.regulamento:
        response = HttpResponse(campeonato.regulamento, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="regulamento_{campeonato.nome}.txt"'
        return response
    messages.warning(request, 'Regulamento não disponível.')
    return redirect('academia_evento', campeonato_id=campeonato_id)

@operacional_required
def administracao_painel(request):
    return render(request, 'atletas/administracao/painel.html')

@operacional_required
def administracao_conferencia_inscricoes(request):
    return render(request, 'atletas/administracao/conferencia_inscricoes.html')

@operacional_required
def administracao_confirmar_inscricoes(request):
    return redirect('administracao_conferencia_inscricoes')

@operacional_required
def administracao_financeiro(request):
    return render(request, 'atletas/administracao/financeiro.html')

@operacional_required
def administracao_despesas(request):
    return render(request, 'atletas/administracao/despesas.html')

@operacional_required
def administracao_equipe(request):
    return render(request, 'atletas/administracao/equipe.html')

@operacional_required
def administracao_insumos(request):
    return render(request, 'atletas/administracao/insumos.html')

@operacional_required
def administracao_patrocinios(request):
    return render(request, 'atletas/administracao/patrocinios.html')

@operacional_required
def administracao_relatorios(request):
    return render(request, 'atletas/administracao/relatorios.html')

@operacional_required
def administracao_cadastros_operacionais(request, tipo):
    return render(request, 'atletas/administracao/cadastros_operacionais.html', {'tipo': tipo})

@pode_criar_usuarios_required
def gerenciar_usuarios_operacionais(request):
    return render(request, 'atletas/administracao/gerenciar_usuarios.html', {'usuarios_operacionais': UsuarioOperacional.objects.all()})

# ========== MÓDULO DE PAGAMENTOS ==========

@academia_required
def academia_enviar_comprovante(request, campeonato_id):
    """Enviar comprovante de pagamento pela academia"""
    academia = request.academia
    campeonato = get_object_or_404(Campeonato, id=campeonato_id)
    
    # Calcular valor total
    inscricoes = Inscricao.objects.filter(
        atleta__academia=academia,
        campeonato=campeonato
    )
    
    valor_federado = campeonato.valor_inscricao_federado or 0
    valor_nao_federado = campeonato.valor_inscricao_nao_federado or 0
    
    valor_total = sum(
        valor_federado if ins.atleta.federado else valor_nao_federado
        for ins in inscricoes
    )
    
    # Verificar se já existe pagamento
    pagamento_existente = Pagamento.objects.filter(
        academia=academia,
        campeonato=campeonato
    ).first()
    
    if request.method == 'POST':
        if 'comprovante' in request.FILES:
            comprovante = request.FILES['comprovante']
            
            # Validar tipo de arquivo
            extensao = comprovante.name.split('.')[-1].lower()
            if extensao not in ['jpg', 'jpeg', 'png', 'pdf']:
                messages.error(request, 'Formato de arquivo inválido. Use JPG, PNG ou PDF.')
                return redirect('academia_enviar_comprovante', campeonato_id=campeonato_id)
            
            # Criar ou atualizar pagamento
            if pagamento_existente:
                pagamento_existente.comprovante = comprovante
                pagamento_existente.status = 'AGUARDANDO'
                pagamento_existente.motivo_rejeicao = ''
                pagamento_existente.save()
                messages.success(request, 'Comprovante atualizado com sucesso! Aguarde validação do operador.')
            else:
                pagamento = Pagamento.objects.create(
                    academia=academia,
                    campeonato=campeonato,
                    valor_total=valor_total,
                    comprovante=comprovante,
                    status='AGUARDANDO'
                )
                messages.success(request, 'Comprovante enviado com sucesso! Aguarde validação do operador.')
            
            return redirect('academia_evento', campeonato_id=campeonato_id)
        else:
            messages.error(request, 'Por favor, selecione um arquivo.')
    
    context = {
        'academia': academia,
        'campeonato': campeonato,
        'valor_total': valor_total,
        'inscricoes': inscricoes,
        'pagamento': pagamento_existente,
    }
    
    return render(request, 'atletas/academia/enviar_comprovante.html', context)

@operacional_required
def validacao_pagamentos(request):
    """Painel de validação de pagamentos para operador"""
    # Buscar pagamentos aguardando validação
    pagamentos_aguardando = Pagamento.objects.filter(
        status__in=['PENDENTE', 'AGUARDANDO']
    ).select_related('academia', 'campeonato').order_by('-data_envio')
    
    # Buscar pagamentos validados recentes
    pagamentos_validados = Pagamento.objects.filter(
        status='VALIDADO'
    ).select_related('academia', 'campeonato', 'validado_por').order_by('-data_validacao')[:10]
    
    # Buscar pagamentos rejeitados recentes
    pagamentos_rejeitados = Pagamento.objects.filter(
        status='REJEITADO'
    ).select_related('academia', 'campeonato').order_by('-data_envio')[:10]
    
    context = {
        'pagamentos_aguardando': pagamentos_aguardando,
        'pagamentos_validados': pagamentos_validados,
        'pagamentos_rejeitados': pagamentos_rejeitados,
    }
    
    return render(request, 'atletas/administracao/validacao_pagamentos.html', context)

@operacional_required
def validar_pagamento(request, pagamento_id):
    """Validar pagamento e confirmar inscrições"""
    pagamento = get_object_or_404(Pagamento, id=pagamento_id)
    
    if request.method == 'POST':
        # Atualizar status do pagamento
        pagamento.status = 'VALIDADO'
        pagamento.validado_por = request.user
        pagamento.data_validacao = timezone.now()
        pagamento.motivo_rejeicao = ''
        pagamento.save()
        
        # Confirmar todas as inscrições da academia no campeonato
        inscricoes = Inscricao.objects.filter(
            atleta__academia=pagamento.academia,
            campeonato=pagamento.campeonato
        )
        inscricoes.update(status_inscricao='aprovado')
        
        messages.success(request, f'Pagamento validado! {inscricoes.count()} inscrições confirmadas automaticamente.')
        return redirect('validacao_pagamentos')
    
    # Buscar inscrições da academia
    inscricoes = Inscricao.objects.filter(
        atleta__academia=pagamento.academia,
        campeonato=pagamento.campeonato
    ).select_related('atleta', 'atleta__academia')
    
    context = {
        'pagamento': pagamento,
        'inscricoes': inscricoes,
    }
    
    return render(request, 'atletas/administracao/validar_pagamento.html', context)

@operacional_required
def rejeitar_pagamento(request, pagamento_id):
    """Rejeitar pagamento"""
    pagamento = get_object_or_404(Pagamento, id=pagamento_id)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo_rejeicao', '').strip()
        
        if not motivo:
            messages.error(request, 'Por favor, informe o motivo da rejeição.')
            return redirect('validar_pagamento', pagamento_id=pagamento_id)
        
        pagamento.status = 'REJEITADO'
        pagamento.motivo_rejeicao = motivo
        pagamento.save()
        
        messages.success(request, 'Pagamento rejeitado. A academia foi notificada.')
        return redirect('validacao_pagamentos')
    
    context = {
        'pagamento': pagamento,
    }
    
    return render(request, 'atletas/administracao/rejeitar_pagamento.html', context)
