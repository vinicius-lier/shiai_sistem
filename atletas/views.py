<<<<<<< HEAD
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
=======
import os
import json
import csv
import io
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from atletas.models import Academia, Categoria, Atleta, Chave, Luta, AdminLog, AcademiaPontuacao
from atletas.utils import calcular_classe, get_categorias_disponiveis, ajustar_categoria_por_peso, gerar_chave, get_resultados_chave, calcular_pontuacao_academias, atualizar_proxima_luta, registrar_remanejamento
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


# ========== PÁGINA INICIAL ==========

def index(request):
    """Página inicial"""
    return render(request, 'atletas/index.html')


# ========== CADASTRO DE ACADEMIAS ==========

def lista_academias(request):
    """Lista todas as academias"""
    academias = Academia.objects.all().order_by('-pontos', 'nome')
    return render(request, 'atletas/lista_academias.html', {'academias': academias})


def cadastrar_academia(request):
    """Cadastra uma nova academia"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        cidade = request.POST.get('cidade', '')
        estado = request.POST.get('estado', '')
        
        Academia.objects.create(nome=nome, cidade=cidade, estado=estado)
        messages.success(request, f'Academia "{nome}" cadastrada com sucesso!')
        return redirect('lista_academias')
    
    return render(request, 'atletas/cadastrar_academia.html')


# ========== CADASTRO DE CATEGORIAS ==========

def lista_categorias(request):
    """Lista todas as categorias com filtros"""
    categorias = Categoria.objects.all()
    
    # Filtros
    classe_filtro = request.GET.get('classe', '')
    sexo_filtro = request.GET.get('sexo', '')
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    # Aplicar filtros
    if classe_filtro:
        categorias = categorias.filter(classe=classe_filtro)
    
    if sexo_filtro:
        categorias = categorias.filter(sexo=sexo_filtro)
    
    if categoria_filtro:
        categorias = categorias.filter(categoria_nome__icontains=categoria_filtro)
    
    # Ordenação
    categorias = categorias.order_by('classe', 'sexo', 'limite_min')
    
    # Buscar opções para filtros
    classes = Categoria.objects.values_list('classe', flat=True).distinct().order_by('classe')
    
    context = {
        'categorias': categorias,
        'classes': classes,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/lista_categorias.html', context)


def cadastrar_categoria(request):
    """Cadastra uma nova categoria"""
    if request.method == 'POST':
        classe = request.POST.get('classe')
        sexo = request.POST.get('sexo')
        categoria_nome = request.POST.get('categoria_nome')
        limite_min = float(request.POST.get('limite_min'))
        limite_max_str = request.POST.get('limite_max')
        limite_max = float(limite_max_str) if limite_max_str else 999.0
        
        label = f"{classe} - {categoria_nome}"
        if limite_max < 999.0:
            label += f" ({limite_min} a {limite_max} kg)"
        else:
            label += f" ({limite_min} kg ou mais)"
        
        Categoria.objects.create(
            classe=classe,
            sexo=sexo,
            categoria_nome=categoria_nome,
            limite_min=limite_min,
            limite_max=limite_max,
            label=label
        )
        
        messages.success(request, f'Categoria "{label}" cadastrada com sucesso!')
        return redirect('lista_categorias')
    
    return render(request, 'atletas/cadastrar_categoria.html')


# ========== INSCRIÇÃO DE ATLETAS ==========

def lista_atletas(request):
    """Lista todos os atletas com filtros"""
    atletas = Atleta.objects.all().select_related('academia')
    
    # Filtros
    nome_filtro = request.GET.get('nome', '').strip()
    classe_filtro = request.GET.get('classe', '')
    sexo_filtro = request.GET.get('sexo', '')
    categoria_filtro = request.GET.get('categoria', '')
    academia_filtro = request.GET.get('academia', '')
    status_filtro = request.GET.get('status', '')
    faixa_filtro = request.GET.get('faixa', '').strip()
    
    # Aplicar filtros
    if nome_filtro:
        atletas = atletas.filter(nome__icontains=nome_filtro)
    
    if classe_filtro:
        atletas = atletas.filter(classe=classe_filtro)
    
    if sexo_filtro:
        atletas = atletas.filter(sexo=sexo_filtro)
    
    if categoria_filtro:
        atletas = atletas.filter(
            Q(categoria_nome__icontains=categoria_filtro) | 
            Q(categoria_ajustada__icontains=categoria_filtro)
        )
    
    if academia_filtro:
        try:
            atletas = atletas.filter(academia_id=int(academia_filtro))
        except (ValueError, TypeError):
            pass
    
    if status_filtro:
        atletas = atletas.filter(status=status_filtro)
    
    if faixa_filtro:
        atletas = atletas.filter(faixa__icontains=faixa_filtro)
    
    # Ordenação
    ordenacao = request.GET.get('ordenar', 'nome')
    if ordenacao in ['nome', 'classe', 'categoria_nome', 'academia__nome', 'peso_oficial', 'status']:
        atletas = atletas.order_by(ordenacao)
    else:
        atletas = atletas.order_by('nome')
    
    # Buscar opções para os filtros
    classes = Atleta.objects.values_list('classe', flat=True).distinct().order_by('classe')
    categorias = Atleta.objects.values_list('categoria_nome', flat=True).distinct().order_by('categoria_nome')
    academias = Academia.objects.all().order_by('nome')
    faixas = Atleta.objects.values_list('faixa', flat=True).distinct().order_by('faixa')
    
    context = {
        'atletas': atletas,
        'classes': classes,
        'categorias': categorias,
        'academias': academias,
        'faixas': faixas,
        'nome_filtro': nome_filtro,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
        'academia_filtro': academia_filtro,
        'status_filtro': status_filtro,
        'faixa_filtro': faixa_filtro,
        'ordenacao': ordenacao,
        'total_encontrados': atletas.count(),
    }

    # Modo de impressão: usa outro template, com a mesma lista filtrada
    if request.GET.get('modo') == 'imprimir':
        return render(request, 'atletas/relatorios/atletas_filtrados.html', context)

    return render(request, 'atletas/lista_atletas.html', context)


def cadastrar_atleta(request):
    """Cadastra um novo atleta"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ano_nasc = int(request.POST.get('ano_nasc'))
        sexo = request.POST.get('sexo')
        faixa = request.POST.get('faixa')
        academia_id = int(request.POST.get('academia'))
        categoria_id = int(request.POST.get('categoria'))
        peso_previsto = request.POST.get('peso_previsto')
        
        academia = get_object_or_404(Academia, id=academia_id)
        categoria = get_object_or_404(Categoria, id=categoria_id)
        
        classe = calcular_classe(ano_nasc)
        
        # Corrigir limite para categorias "acima de"
        if categoria.limite_max and categoria.limite_max < 999.0:
            categoria_limite = f"{categoria.limite_min} a {categoria.limite_max} kg"
        else:
            categoria_limite = f"{categoria.limite_min} kg ou mais"
        
        atleta = Atleta.objects.create(
            nome=nome,
            ano_nasc=ano_nasc,
            sexo=sexo,
            faixa=faixa,
            academia=academia,
            classe=classe,
            categoria_nome=categoria.categoria_nome,
            categoria_limite=categoria_limite,
            peso_previsto=float(peso_previsto) if peso_previsto else None
        )
        
        return redirect('lista_atletas')
    
    academias = Academia.objects.all().order_by('nome')
    # Buscar categorias para SUB 11 como exemplo inicial (pode ser ajustado)
    categorias = Categoria.objects.all().order_by('classe', 'limite_min')
    
    return render(request, 'atletas/cadastrar_atleta.html', {
        'academias': academias,
        'categorias': categorias
    })


def cadastrar_festival(request):
    """Cadastra um atleta do Festival"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ano_nasc = int(request.POST.get('ano_nasc'))
        sexo = request.POST.get('sexo')
        faixa = request.POST.get('faixa')
        academia_id = int(request.POST.get('academia'))
        
        academia = get_object_or_404(Academia, id=academia_id)
        
        # Verificar se a idade está entre 3 e 6 anos
        from datetime import date
        idade = date.today().year - ano_nasc
        if idade < 3 or idade > 6:
            messages.warning(request, f'Idade do atleta ({idade} anos) está fora do intervalo permitido para Festival (3 a 6 anos).')
            academias = Academia.objects.all().order_by('nome')
            return render(request, 'atletas/cadastrar_festival.html', {'academias': academias})
        
        # Criar atleta Festival
        atleta = Atleta.objects.create(
            nome=nome,
            ano_nasc=ano_nasc,
            sexo=sexo,
            faixa=faixa,
            academia=academia,
            classe='Festival',
            categoria_nome='Festival',
            categoria_limite='Não compete',
            status='OK'  # Festival sempre OK
        )
        
        # Adicionar 1 ponto imediatamente para a academia
        academia.pontos += 1
        academia.save()
        
        messages.success(request, f'Atleta Festival "{nome}" cadastrado com sucesso! A academia "{academia.nome}" ganhou 1 ponto.')
        return redirect('lista_atletas')
    
    academias = Academia.objects.all().order_by('nome')
    return render(request, 'atletas/cadastrar_festival.html', {'academias': academias})


def get_categorias_por_sexo(request):
    """Retorna categorias filtradas por sexo via AJAX"""
    sexo = request.GET.get('sexo', '')
    classe = request.GET.get('classe', '')
    
    if not sexo:
        return JsonResponse({'categorias': []})
    
    categorias = Categoria.objects.filter(sexo=sexo)
    
    if classe:
        categorias = categorias.filter(classe=classe)
    
    categorias = categorias.order_by('classe', 'limite_min')
    
    categorias_list = [
        {
            'id': cat.id,
            'nome': cat.categoria_nome,
            'label': cat.label,
            'limite_min': cat.limite_min,
            'limite_max': cat.limite_max if cat.limite_max < 999.0 else None
        }
        for cat in categorias
    ]
    
    return JsonResponse({'categorias': categorias_list})


def get_categorias_ajax(request):
    """Retorna categorias disponíveis via AJAX"""
    classe = request.GET.get('classe')
    sexo = request.GET.get('sexo')
    
    categorias = get_categorias_disponiveis(classe, sexo)
    
    data = [{
        'id': cat.id,
        'nome': cat.categoria_nome,
        'label': cat.label,
        'limite_min': cat.limite_min,
        'limite_max': cat.limite_max
    } for cat in categorias]
    
    return JsonResponse({'categorias': data})


def importar_atletas(request):
    """Importa atletas de um arquivo CSV ou Excel"""
    if request.method == 'POST':
        arquivo = request.FILES.get('arquivo')
        if not arquivo:
            messages.error(request, 'Por favor, selecione um arquivo.')
            return render(request, 'atletas/importar_atletas.html')
        
        try:
            # Ler o arquivo
            if arquivo.name.endswith('.csv'):
                # Processar CSV
                conteudo = arquivo.read().decode('utf-8-sig')  # utf-8-sig para lidar com BOM
                reader = csv.DictReader(io.StringIO(conteudo))
                
                sucessos = 0
                erros = []
                
                for linha_num, row in enumerate(reader, start=2):  # Começa em 2 porque linha 1 é o cabeçalho
                    try:
                        # Mapear colunas (flexível)
                        nome = row.get('nome', row.get('Nome', row.get('NOME', ''))).strip()
                        ano_nasc_str = row.get('ano_nasc', row.get('Ano Nasc', row.get('ANO_NASC', row.get('Ano', '')))).strip()
                        sexo_raw = row.get('sexo', row.get('Sexo', row.get('SEXO', ''))).strip()
                        sexo = sexo_raw.upper()[0] if sexo_raw else ''
                        faixa = row.get('faixa', row.get('Faixa', row.get('FAIXA', ''))).strip()
                        academia_nome = row.get('academia', row.get('Academia', row.get('ACADEMIA', ''))).strip()
                        categoria_nome = row.get('categoria', row.get('Categoria', row.get('CATEGORIA', ''))).strip()
                        peso_previsto = row.get('peso_previsto', row.get('Peso Previsto', row.get('PESO_PREVISTO', row.get('peso', row.get('Peso', '')))))
                        
                        # Validar campos obrigatórios
                        if not nome:
                            erros.append(f"Linha {linha_num}: Nome obrigatório")
                            continue
                        if not sexo:
                            erros.append(f"Linha {linha_num}: Sexo obrigatório")
                            continue
                        if not faixa:
                            erros.append(f"Linha {linha_num}: Faixa obrigatória")
                            continue
                        if not academia_nome:
                            erros.append(f"Linha {linha_num}: Academia obrigatória")
                            continue
                        if not categoria_nome:
                            erros.append(f"Linha {linha_num}: Categoria obrigatória")
                            continue
                        
                        # Validar ano_nasc
                        if not ano_nasc_str:
                            erros.append(f"Linha {linha_num}: Ano de nascimento obrigatório")
                            continue
                        
                        try:
                            ano_nasc = int(ano_nasc_str)
                        except ValueError:
                            erros.append(f"Linha {linha_num}: Ano de nascimento inválido: '{ano_nasc_str}'")
                            continue
                        
                        # Validar sexo
                        if sexo not in ['M', 'F']:
                            erros.append(f"Linha {linha_num}: Sexo inválido (deve ser M ou F)")
                            continue
                        
                        # Buscar ou criar academia
                        academia, _ = Academia.objects.get_or_create(
                            nome=academia_nome,
                            defaults={'cidade': '', 'estado': ''}
                        )
                        
                        # Calcular classe
                        classe = calcular_classe(ano_nasc)
                        
                        # Buscar categoria
                        categoria = Categoria.objects.filter(
                            categoria_nome=categoria_nome,
                            classe=classe,
                            sexo=sexo
                        ).first()
                        
                        if not categoria:
                            erros.append(f"Linha {linha_num}: Categoria '{categoria_nome}' não encontrada para {classe} {sexo}")
                            continue
                        
                        # Corrigir limite para categorias "acima de"
                        if categoria.limite_max and categoria.limite_max < 999.0:
                            categoria_limite = f"{categoria.limite_min} a {categoria.limite_max} kg"
                        else:
                            categoria_limite = f"{categoria.limite_min} kg ou mais"
                        
                        # Converter peso previsto
                        peso = None
                        if peso_previsto:
                            try:
                                peso = float(str(peso_previsto).replace(',', '.'))
                            except:
                                pass
                        
                        # Criar atleta
                        Atleta.objects.create(
                            nome=nome,
                            ano_nasc=ano_nasc,
                            sexo=sexo,
                            faixa=faixa,
                            academia=academia,
                            classe=classe,
                            categoria_nome=categoria.categoria_nome,
                            categoria_limite=categoria_limite,
                            peso_previsto=peso
                        )
                        sucessos += 1
                        
                    except Exception as e:
                        erros.append(f"Linha {linha_num}: {str(e)}")
                
                if sucessos > 0:
                    messages.success(request, f'{sucessos} atleta(s) importado(s) com sucesso!')
                if erros:
                    messages.warning(request, f'{len(erros)} erro(s) encontrado(s). Verifique os dados.')
                    # Armazenar erros na sessão para exibir
                    request.session['import_errors'] = erros[:20]  # Limitar a 20 erros
                
                return redirect('lista_atletas')
                
            else:
                messages.error(request, 'Formato de arquivo não suportado. Use CSV (.csv).')
                return render(request, 'atletas/importar_atletas.html')
                
        except Exception as e:
            messages.error(request, f'Erro ao processar arquivo: {str(e)}')
            return render(request, 'atletas/importar_atletas.html')
    
    # GET - mostrar formulário
    erros = request.session.pop('import_errors', [])
    return render(request, 'atletas/importar_atletas.html', {'erros': erros})


# ========== PESAGEM ==========

def pesagem(request):
    """Tela de pesagem com filtros"""
    classe_filtro = request.GET.get('classe', '')
    sexo_filtro = request.GET.get('sexo', '')
    categoria_filtro = request.GET.get('categoria', '')
    
    atletas = Atleta.objects.all().select_related('academia')
    
    if classe_filtro:
        atletas = atletas.filter(classe=classe_filtro)
    if sexo_filtro:
        atletas = atletas.filter(sexo=sexo_filtro)
    if categoria_filtro:
        atletas = atletas.filter(
            Q(categoria_nome=categoria_filtro) | Q(categoria_ajustada=categoria_filtro)
        )
    
    # Buscar opções para filtros
    classes = Atleta.objects.values_list('classe', flat=True).distinct().order_by('classe')
    categorias = Atleta.objects.values_list('categoria_nome', flat=True).distinct().order_by('categoria_nome')
    
    context = {
        'atletas': atletas,
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/pesagem.html', context)

<<<<<<< HEAD
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
=======

def pesagem_mobile_view(request):
    """Tela de pesagem mobile-first para celulares"""
    classe_filtro = request.GET.get('classe', '')
    sexo_filtro = request.GET.get('sexo', '')
    categoria_filtro = request.GET.get('categoria', '').strip()
    
    atletas = Atleta.objects.all().select_related('academia')
    
    if classe_filtro:
        atletas = atletas.filter(classe=classe_filtro)
    if sexo_filtro:
        atletas = atletas.filter(sexo=sexo_filtro)
    if categoria_filtro:
        atletas = atletas.filter(
            Q(categoria_nome__icontains=categoria_filtro) | Q(categoria_ajustada__icontains=categoria_filtro)
        )
    
    # Buscar opções para filtros
    classes = Atleta.objects.values_list('classe', flat=True).distinct().order_by('classe')
    
    context = {
        'atletas': atletas,
        'classes': classes,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/pesagem_mobile.html', context)


def registrar_peso(request, atleta_id):
    """Registra o peso oficial de um atleta e verifica se precisa remanejamento"""
    if request.method == 'POST':
        atleta = get_object_or_404(Atleta, id=atleta_id)
        peso_oficial = float(request.POST.get('peso_oficial'))
        
        # Buscar categoria atual
        categoria_atual = Categoria.objects.filter(
            classe=atleta.classe,
            sexo=atleta.sexo,
            categoria_nome=atleta.categoria_nome
        ).first()
        
        if not categoria_atual:
            messages.error(request, 'Categoria atual não encontrada.')
            if 'mobile' in request.META.get('HTTP_REFERER', ''):
                return redirect('pesagem_mobile')
            return redirect('pesagem')
        
        # Verificar se peso está dentro dos limites
        limite_max_real = categoria_atual.limite_max if categoria_atual.limite_max < 999.0 else 999999.0
        
        if categoria_atual.limite_min <= peso_oficial <= limite_max_real:
            # Peso OK, salvar normalmente
            atleta.peso_oficial = peso_oficial
            atleta.status = "OK"
            atleta.motivo_ajuste = ""
            atleta.save()
            messages.success(request, f'Peso registrado com sucesso: {peso_oficial}kg')
            if 'mobile' in request.META.get('HTTP_REFERER', ''):
                return redirect('pesagem_mobile')
            return redirect('pesagem')
        
        # Peso fora dos limites - precisa verificar se pode remanejar
        categoria_ajustada, motivo = ajustar_categoria_por_peso(atleta, peso_oficial)
        
        if categoria_ajustada:
            # Retornar JSON com informações para diálogo de confirmação
            return JsonResponse({
                'precisa_confirmacao': True,
                'peso': peso_oficial,
                'categoria_atual': categoria_atual.categoria_nome,
                'limite_atual_min': categoria_atual.limite_min,
                'limite_atual_max': limite_max_real,
                'categoria_nova': categoria_ajustada.categoria_nome,
                'limite_novo_min': categoria_ajustada.limite_min,
                'limite_novo_max': categoria_ajustada.limite_max if categoria_ajustada.limite_max < 999.0 else None,
                'motivo': motivo,
                'atleta_id': atleta_id,
                'atleta_nome': atleta.nome
            })
        else:
            # Não pode remanejar - desclassificar
            atleta.peso_oficial = peso_oficial
            atleta.status = "Eliminado Peso"
            atleta.motivo_ajuste = motivo
            atleta.save()
            messages.warning(request, f'Atleta desclassificado: {motivo}')
            if 'mobile' in request.META.get('HTTP_REFERER', ''):
                return redirect('pesagem_mobile')
            return redirect('pesagem')
    
    if 'mobile' in request.META.get('HTTP_REFERER', ''):
        return redirect('pesagem_mobile')
    return redirect('pesagem')


def confirmar_remanejamento(request, atleta_id):
    """Confirma ou rejeita remanejamento de categoria"""
    if request.method == 'POST':
        atleta = get_object_or_404(Atleta, id=atleta_id)
        acao = request.POST.get('acao')  # 'remanejar' ou 'desclassificar'
        peso_oficial = float(request.POST.get('peso_oficial'))
        categoria_nova = request.POST.get('categoria_nova')
        
        atleta.peso_oficial = peso_oficial
        
        if acao == 'remanejar':
            # Remanejar para nova categoria
            categoria = Categoria.objects.filter(
                classe=atleta.classe,
                sexo=atleta.sexo,
                categoria_nome=categoria_nova
            ).first()
            
            if categoria:
                atleta.categoria_ajustada = categoria.categoria_nome
                limite_max = categoria.limite_max if categoria.limite_max < 999.0 else None
                if limite_max:
                    atleta.categoria_limite = f"{categoria.limite_min} a {limite_max} kg"
                else:
                    atleta.categoria_limite = f"{categoria.limite_min} kg ou mais"
                atleta.status = "OK"
                atleta.remanejado = True  # Marcar como remanejado
                atleta.motivo_ajuste = f"Remanejado de {atleta.categoria_nome} para {categoria_nova} (peso {peso_oficial}kg)"
                atleta.save()
                
                # Descontar 1 ponto da academia
                academia = atleta.academia
                academia.pontos = max(0, academia.pontos - 1)  # Não deixar ficar negativo
                academia.save()
                
                messages.success(request, f'Atleta remanejado para {categoria_nova}. Academia perdeu 1 ponto.')
            else:
                messages.error(request, 'Categoria não encontrada.')
        else:
            # Desclassificar
            atleta.status = "Eliminado Peso"
            atleta.motivo_ajuste = f"Desclassificado por peso {peso_oficial}kg fora da categoria {atleta.categoria_nome}"
            atleta.save()
            messages.warning(request, 'Atleta desclassificado.')
        
        # Verificar se veio da versão mobile
        referer = request.META.get('HTTP_REFERER', '')
        if 'mobile' in referer:
            return redirect('pesagem_mobile')
        
        return redirect('pesagem')
    
    return redirect('pesagem')


def rebaixar_categoria(request, atleta_id):
    """Rebaixa atleta para categoria inferior"""
    atleta = get_object_or_404(Atleta, id=atleta_id)
    
    # Buscar categoria inferior
    categoria_atual = Categoria.objects.filter(
        classe=atleta.classe,
        sexo=atleta.sexo,
        categoria_nome=atleta.categoria_nome
    ).first()
    
    if categoria_atual and atleta.peso_oficial:
        categoria_inferior = Categoria.objects.filter(
            classe=atleta.classe,
            sexo=atleta.sexo,
            limite_max__lt=categoria_atual.limite_min
        ).order_by('-limite_max').first()
        
        if categoria_inferior and categoria_inferior.limite_min <= atleta.peso_oficial <= categoria_inferior.limite_max:
            atleta.categoria_ajustada = categoria_inferior.categoria_nome
            # Corrigir limite para categorias "acima de"
            if categoria_inferior.limite_max and categoria_inferior.limite_max < 999.0:
                atleta.categoria_limite = f"{categoria_inferior.limite_min} a {categoria_inferior.limite_max} kg"
            else:
                atleta.categoria_limite = f"{categoria_inferior.limite_min} kg ou mais"
            atleta.motivo_ajuste = f"Rebaixado para {categoria_inferior.label}"
            atleta.status = "OK"
            atleta.save()
    
    return redirect('pesagem')


# ========== GERAÇÃO DE CHAVES ==========

def lista_chaves(request):
    """Lista todas as chaves com filtros"""
    chaves = Chave.objects.all().order_by('classe', 'sexo', 'categoria')

    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()

    if classe_filtro:
        chaves = chaves.filter(classe__icontains=classe_filtro)
    if sexo_filtro:
        chaves = chaves.filter(sexo=sexo_filtro)
    if categoria_filtro:
        chaves = chaves.filter(categoria__icontains=categoria_filtro)

    classes = (
        Chave.objects.values_list('classe', flat=True)
        .distinct()
        .order_by('classe')
    )
    categorias = (
        Chave.objects.values_list('categoria', flat=True)
        .distinct()
        .order_by('categoria')
    )

    context = {
        'chaves': chaves,
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
<<<<<<< HEAD
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
=======
        'total_chaves': chaves.count(),
    }

    return render(request, 'atletas/lista_chaves.html', context)


def gerar_chave_view(request):
    """Gera uma nova chave"""
    if request.method == 'POST':
        classe = request.POST.get('classe')
        sexo = request.POST.get('sexo')
        categoria = request.POST.get('categoria')
        
        chave = gerar_chave(categoria, classe, sexo)
        return redirect('detalhe_chave', chave_id=chave.id)
    
    # Buscar opções
    classes = Atleta.objects.values_list('classe', flat=True).distinct().order_by('classe')
    
    # Filtrar categorias por sexo se selecionado via GET (para atualizar dropdown via AJAX)
    sexo_filtro = request.GET.get('sexo', '')
    if sexo_filtro:
        categorias = Categoria.objects.filter(sexo=sexo_filtro).order_by('classe', 'categoria_nome')
    else:
        categorias = Categoria.objects.all().order_by('classe', 'categoria_nome')
    
    return render(request, 'atletas/gerar_chave.html', {
        'classes': classes,
        'categorias': categorias,
        'sexo_selecionado': sexo_filtro
    })


def gerar_chave_manual(request):
    """
    Gera uma chave manual de lutas casadas:
    - Usuário seleciona atletas (de qualquer classe/categoria)
    - Sistema cria uma chave com lutas 1x1 na ordem selecionada
    - Não conta para ranking (tipo lutas_casadas)
    """
    # Filtros para facilitar seleção dos atletas
    nome_filtro = request.GET.get('nome', '').strip()
    classe_filtro = request.GET.get('classe', '')
    sexo_filtro = request.GET.get('sexo', '')
    academia_filtro = request.GET.get('academia', '')

    atletas = Atleta.objects.all().select_related('academia').order_by('classe', 'sexo', 'categoria_nome', 'nome')

    if nome_filtro:
        atletas = atletas.filter(nome__icontains=nome_filtro)
    if classe_filtro:
        atletas = atletas.filter(classe=classe_filtro)
    if sexo_filtro:
        atletas = atletas.filter(sexo=sexo_filtro)
    if academia_filtro:
        try:
            atletas = atletas.filter(academia_id=int(academia_filtro))
        except (ValueError, TypeError):
            pass

    classes = Atleta.objects.values_list('classe', flat=True).distinct().order_by('classe')
    academias = Academia.objects.all().order_by('nome')

    if request.method == 'POST':
        selecionados = request.POST.getlist('atletas')
        nome_chave = request.POST.get('nome_chave', '').strip() or 'Lutas casadas'
        classe = request.POST.get('classe_chave', '').strip() or 'Livre'
        sexo = request.POST.get('sexo_chave', '').strip() or 'M'

        if len(selecionados) < 2:
            messages.error(request, 'Selecione pelo menos 2 atletas para gerar lutas casadas.')
        else:
            atletas_sel = list(Atleta.objects.filter(id__in=selecionados).order_by('nome'))

            # Criar chave manual
            chave = Chave.objects.create(
                classe=classe,
                sexo=sexo,
                categoria=nome_chave,
                estrutura={}
            )
            chave.atletas.set(atletas_sel)

            # Criar lutas 1x1 na ordem
            from atletas.models import Luta  # evitar import circular

            lutas_ids = []
            for i in range(0, len(atletas_sel), 2):
                atleta_a = atletas_sel[i]
                atleta_b = atletas_sel[i + 1] if i + 1 < len(atletas_sel) else None
                luta = Luta.objects.create(
                    chave=chave,
                    atleta_a=atleta_a,
                    atleta_b=atleta_b,
                    round=1,
                    proxima_luta=None
                )
                lutas_ids.append(luta.id)

            # Estrutura simples apenas para identificar que é chave manual
            chave.estrutura = {
                "tipo": "lutas_casadas",
                "lutas": lutas_ids,
            }
            chave.save()

            messages.success(request, f'Chave manual "{nome_chave}" criada com {len(lutas_ids)} luta(s).')
            return redirect('detalhe_chave', chave_id=chave.id)

    context = {
        'atletas': atletas,
        'classes': classes,
        'academias': academias,
        'nome_filtro': nome_filtro,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'academia_filtro': academia_filtro,
    }

    return render(request, 'atletas/gerar_chave_manual.html', context)


def detalhe_chave(request, chave_id):
    """Mostra detalhes de uma chave"""
    chave = get_object_or_404(Chave, id=chave_id)
    lutas = chave.lutas.all().order_by('round', 'id')
    resultados_ids = get_resultados_chave(chave)
    
    # Buscar atletas dos resultados
    resultados_atletas = []
    for resultado_id in resultados_ids:
        try:
            atleta = Atleta.objects.get(id=resultado_id)
            resultados_atletas.append(atleta)
        except Atleta.DoesNotExist:
            pass
    
    context = {
        'chave': chave,
        'lutas': lutas,
        'resultados': resultados_atletas
    }
    
    return render(request, 'atletas/detalhe_chave.html', context)


def chave_mobile_view(request, chave_id):
    """Visualização mobile da chave"""
    chave = get_object_or_404(Chave, id=chave_id)
    lutas = chave.lutas.all().order_by('round', 'id')
    resultados_ids = get_resultados_chave(chave)
    
    # Buscar atletas dos resultados
    resultados_atletas = []
    for resultado_id in resultados_ids:
        try:
            atleta = Atleta.objects.get(id=resultado_id)
            resultados_atletas.append(atleta)
        except Atleta.DoesNotExist:
            pass
    
    context = {
        'chave': chave,
        'lutas': lutas,
        'resultados': resultados_atletas
    }
    
    return render(request, 'atletas/chave_mobile.html', context)


def luta_mobile_view(request, luta_id):
    """Visualização mobile da luta para escolher vencedor"""
    luta = get_object_or_404(Luta, id=luta_id)
    
    # Buscar próxima luta se houver
    proxima_luta = None
    if luta.proxima_luta:
        try:
            proxima_luta = Luta.objects.get(id=luta.proxima_luta, chave=luta.chave)
        except Luta.DoesNotExist:
            pass
    
    context = {
        'luta': luta,
        'proxima_luta': proxima_luta
    }
    
    return render(request, 'atletas/luta_mobile.html', context)


# ========== REGISTRO DE LUTAS ==========

def registrar_vencedor(request, luta_id):
    """Registra o vencedor de uma luta"""
    if request.method == 'POST':
        luta = get_object_or_404(Luta, id=luta_id)
        vencedor_id = int(request.POST.get('vencedor'))
        tipo_vitoria = request.POST.get('tipo_vitoria', 'IPPON')
        
        vencedor = get_object_or_404(Atleta, id=vencedor_id)
        luta.vencedor = vencedor
        luta.tipo_vitoria = tipo_vitoria
        luta.pontos_perdedor = 0
        
        # Calcular pontos conforme tipo de vitória
        if tipo_vitoria == "IPPON":
            luta.pontos_vencedor = 10
            luta.ippon_count = 1
            luta.wazari_count = 0
            luta.yuko_count = 0
        elif tipo_vitoria in ["WAZARI", "WAZARI_WAZARI"]:
            luta.pontos_vencedor = 7
            luta.ippon_count = 0
            luta.wazari_count = 1
            luta.yuko_count = 0
        elif tipo_vitoria == "YUKO":
            luta.pontos_vencedor = 1
            luta.ippon_count = 0
            luta.wazari_count = 0
            luta.yuko_count = 1
        
        luta.concluida = True
        luta.save()
        
        # Atualizar estrutura JSON da chave
        estrutura = luta.chave.estrutura
        if isinstance(estrutura, dict):
            # Buscar informações da luta no JSON
            for round_num, lutas_round in estrutura.get("rounds", {}).items():
                if luta.id in lutas_round:
                    if "lutas_detalhes" not in estrutura:
                        estrutura["lutas_detalhes"] = {}
                    estrutura["lutas_detalhes"][str(luta.id)] = {
                        "numero": luta.id,
                        "atleta_a": luta.atleta_a.id if luta.atleta_a else None,
                        "atleta_b": luta.atleta_b.id if luta.atleta_b else None,
                        "vencedor": vencedor_id,
                        "tipo_vitoria": tipo_vitoria,
                        "pontos": luta.pontos_vencedor
                    }
            
            # Para melhor de 3 e triangular
            if "lutas" in estrutura and luta.id in estrutura["lutas"]:
                if "lutas_detalhes" not in estrutura:
                    estrutura["lutas_detalhes"] = {}
                estrutura["lutas_detalhes"][str(luta.id)] = {
                    "numero": luta.id,
                    "atleta_a": luta.atleta_a.id if luta.atleta_a else None,
                    "atleta_b": luta.atleta_b.id if luta.atleta_b else None,
                    "vencedor": vencedor_id,
                    "tipo_vitoria": tipo_vitoria,
                    "pontos": luta.pontos_vencedor
                }
            
            luta.chave.estrutura = estrutura
            luta.chave.save()
        
        # Atualizar próxima luta
        atualizar_proxima_luta(luta)

        # Reprocessar pontuação de academias
        calcular_pontuacao_academias()
        
        # Verificar se veio da versão mobile (check header ou referrer)
        referer = request.META.get('HTTP_REFERER', '')
        if 'mobile' in referer:
            # Buscar próxima luta
            proxima_luta = None
            if luta.proxima_luta:
                try:
                    proxima_luta = Luta.objects.get(id=luta.proxima_luta, chave=luta.chave)
                    return redirect('luta_mobile', luta_id=proxima_luta.id)
                except Luta.DoesNotExist:
                    pass
            # Se não há próxima luta, voltar para a chave mobile
            return redirect('chave_mobile', chave_id=luta.chave.id)
        
        return redirect('detalhe_chave', chave_id=luta.chave.id)
    
    return redirect('lista_chaves')


# ========== RESULTADOS E PONTUAÇÃO ==========

def calcular_pontuacao(request):
    """Calcula e atualiza a pontuação de todas as academias"""
    calcular_pontuacao_academias()
    return redirect('ranking_academias')


def ranking_academias(request):
    """Ranking final das academias"""
    academias = Academia.objects.all().order_by('-pontos', 'nome')
    return render(request, 'atletas/ranking_academias.html', {'academias': academias})


@require_http_methods(["GET"])
def api_ranking_academias(request):
    """API JSON com ranking de academias"""
    # Usar campeonato ativo ou padrão
    from atletas.models import Campeonato
    campeonato = Campeonato.objects.filter(ativo=True).first()
    if not campeonato:
        campeonato = Campeonato.objects.order_by('-id').first()
    if not campeonato:
        return JsonResponse([], safe=False)
    
    registros = AcademiaPontuacao.objects.filter(campeonato=campeonato).select_related('academia').order_by('-pontos_totais', 'academia__nome')
    data = []
    for reg in registros:
        data.append({
            "academia": reg.academia.nome,
            "ouro": reg.ouro,
            "prata": reg.prata,
            "bronze": reg.bronze,
            "quarto": reg.quarto,
            "quinto": reg.quinto,
            "festival": reg.festival,
            "remanejamento": reg.remanejamento,
            "pontos_total": reg.pontos_totais,
        })
    return JsonResponse(data, safe=False)


# ========== RELATÓRIOS ==========

def relatorio_atletas_inscritos(request):
    """Relatório de atletas inscritos"""
    atletas = Atleta.objects.all().select_related('academia').order_by('classe', 'sexo', 'categoria_nome', 'nome')
    return render(request, 'atletas/relatorios/atletas_inscritos.html', {'atletas': atletas})


def relatorio_pesagem_final(request):
    """Relatório de pesagem final"""
    atletas = Atleta.objects.exclude(peso_oficial__isnull=True).select_related('academia').order_by('classe', 'sexo', 'categoria_nome', 'nome')
    return render(request, 'atletas/relatorios/pesagem_final.html', {'atletas': atletas})


def relatorio_chaves(request):
    """Relatório de todas as chaves"""
    chaves = Chave.objects.all().order_by('classe', 'sexo', 'categoria')
    return render(request, 'atletas/relatorios/chaves.html', {'chaves': chaves})


def relatorio_resultados_categoria(request):
    """Relatório de resultados por categoria"""
    chaves = Chave.objects.all().order_by('classe', 'sexo', 'categoria')
    
    resultados_por_categoria = []
    for chave in chaves:
        resultados_ids = get_resultados_chave(chave)
        resultados_atletas = []
        for resultado_id in resultados_ids:
            try:
                atleta = Atleta.objects.get(id=resultado_id)
                resultados_atletas.append(atleta)
            except Atleta.DoesNotExist:
                pass
        
        resultados_por_categoria.append({
            'chave': chave,
            'resultados': resultados_atletas
        })
    
    return render(request, 'atletas/relatorios/resultados_categoria.html', {
        'resultados_por_categoria': resultados_por_categoria
    })


def dashboard(request):
    """Dashboard com estatísticas gerais"""
    from django.db.models import Count
    
    # Total de atletas
    total_atletas = Atleta.objects.count()
    total_atletas_ok = Atleta.objects.filter(status='OK').count()
    total_festival = Atleta.objects.filter(classe='Festival').count()
    
    # Atletas por classe
    atletas_por_classe = Atleta.objects.values('classe').annotate(
        total=Count('id')
    ).order_by('classe')
    
    # Atletas por academia
    atletas_por_academia = Atleta.objects.values('academia__nome').annotate(
        total=Count('id')
    ).order_by('-total')[:20]  # Top 20 academias
    
    # Contar medalhas por academia
    academias = Academia.objects.all()
    medalhas_por_academia = []
    total_ouros = 0
    total_pratas = 0
    total_bronzes = 0
    
    for academia in academias:
        ouro = 0
        prata = 0
        bronze = 0
        
        # Buscar todas as chaves
        chaves = Chave.objects.all()
        
        for chave in chaves:
            resultados_ids = get_resultados_chave(chave)
            
            # Buscar atletas dos resultados
            resultados_atletas = []
            for resultado_id in resultados_ids[:4]:  # Apenas 1º, 2º, 3º, 3º
                try:
                    atleta = Atleta.objects.get(id=resultado_id)
                    resultados_atletas.append(atleta)
                except Atleta.DoesNotExist:
                    pass
            
            # Contar medalhas da academia
            for idx, atleta in enumerate(resultados_atletas, 1):
                if atleta.academia.id == academia.id:
                    if idx == 1:  # 1º lugar - Ouro
                        ouro += 1
                        total_ouros += 1
                    elif idx == 2:  # 2º lugar - Prata
                        prata += 1
                        total_pratas += 1
                    elif idx >= 3:  # 3º lugares - Bronze
                        bronze += 1
                        total_bronzes += 1
        
        if ouro > 0 or prata > 0 or bronze > 0 or academia.atletas.exists():
            medalhas_por_academia.append({
                'academia': academia,
                'ouro': ouro,
                'prata': prata,
                'bronze': bronze,
                'total_medalhas': ouro + prata + bronze
            })
    
    # Ordenar por total de medalhas (desc)
    medalhas_por_academia.sort(key=lambda x: (x['ouro'], x['prata'], x['bronze']), reverse=True)
    
    context = {
        'total_atletas': total_atletas,
        'total_atletas_ok': total_atletas_ok,
        'total_festival': total_festival,
        'atletas_por_classe': atletas_por_classe,
        'atletas_por_academia': atletas_por_academia,
        'medalhas_por_academia': medalhas_por_academia,
        'total_ouros': total_ouros,
        'total_pratas': total_pratas,
        'total_bronzes': total_bronzes,
    }
    
    return render(request, 'atletas/relatorios/dashboard.html', context)


# ========== ADMIN - RESET CAMPEONATO ==========

class ResetCompeticaoAPIView(APIView):
    """API REST para resetar toda a competição"""
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        data = request.data or {}
        senha = data.get('senha', '')

        # Obter IP do usuário
        usuario_ip = request.META.get('REMOTE_ADDR', None)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            usuario_ip = x_forwarded_for.split(',')[0].strip()

        # Verificar tentativas (throttling)
        cache_key = f'reset_attempts_{usuario_ip}'
        attempts = cache.get(cache_key, 0)

        if attempts >= 5:
            AdminLog.objects.create(
                acao=f"TENTATIVA RESET BLOQUEADA - Muitas tentativas (IP: {usuario_ip})",
                usuario_ip=usuario_ip
            )
            return Response({"detail": "Senha incorreta. Ação não autorizada."}, status=status.HTTP_403_FORBIDDEN)

        senha_correta = os.environ.get('RESET_ADMIN_PASSWORD')

        if not senha_correta or senha != senha_correta:
            attempts += 1
            cache.set(cache_key, attempts, 300)

            AdminLog.objects.create(
                acao=f"TENTATIVA RESET FALHADA - Senha incorreta (IP: {usuario_ip})",
                usuario_ip=usuario_ip
            )
            return Response({"detail": "Senha incorreta. Ação não autorizada."}, status=status.HTTP_403_FORBIDDEN)

        try:
            with transaction.atomic():
                # Limpar pontuações agregadas de academias
                AcademiaPontuacao.objects.all().delete()

                # Resetar pontos das academias
                Academia.objects.all().update(pontos=0)

                # Apagar TODAS as chaves e lutas da competição
                # (Lutas são apagadas em cascata ao remover chaves, mas
                # manter a ordem deixa a intenção explícita.)
                Luta.objects.all().delete()
                Chave.objects.all().delete()

                # Resetar atletas (remanejamento, pesagem, status)
                Atleta.objects.all().update(
                    peso_oficial=None,
                    categoria_ajustada='',
                    motivo_ajuste='',
                    status='OK',
                    remanejado=False
                )

                AdminLog.objects.create(
                    acao=f"RESET CAMPEONATO COMPLETO (IP: {usuario_ip})",
                    usuario_ip=usuario_ip
                )

                cache.delete(cache_key)

                return Response({"detail": "Sistema resetado com sucesso."}, status=status.HTTP_200_OK)

        except Exception as e:
            AdminLog.objects.create(
                acao=f"ERRO NO RESET: {str(e)} (IP: {usuario_ip})",
                usuario_ip=usuario_ip
            )
            return Response({"detail": "Erro ao resetar campeonato."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
