import os
import json
import csv
import io
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
from atletas.models import Academia, Categoria, Atleta, Chave, Luta, AdminLog, AcademiaPontuacao, Campeonato, UserProfile
from atletas.utils import calcular_classe, get_categorias_disponiveis, ajustar_categoria_por_peso, gerar_chave, get_resultados_chave, calcular_pontuacao_academias, atualizar_proxima_luta, registrar_remanejamento
from atletas.decorators import academia_required, operacional_required, admin_required
from django.db.models import Q, Count, Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


# ========== PÁGINA INICIAL ==========

def index(request):
    """Página inicial institucional com landing completa"""
    from django.db.models import Count
    
    # Estatísticas principais
    total_atletas = Atleta.objects.count()
    total_atletas_ok = Atleta.objects.filter(status='OK').count()
    total_academias = Academia.objects.count()
    total_categorias = Categoria.objects.count()
    # ✅ CORRIGIDO: Contar apenas chaves com evento vinculado
    total_chaves = Chave.objects.filter(evento__isnull=False).count()
    
    # Pesagens realizadas (atletas com peso oficial)
    pesagens_realizadas = Atleta.objects.filter(peso_oficial__isnull=False).count()
    
    # Ranking resumido (top 5 academias)
    top_academias = Academia.objects.order_by('-pontos')[:5]
    
    # ✅ CORRIGIDO: Usar apenas Evento (deprecar Campeonato)
    from eventos.models import Evento
    evento_atual = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    if not evento_atual:
        evento_atual = Evento.objects.order_by('-data_evento').first()
    
    context = {
        'total_atletas': total_atletas,
        'total_atletas_ok': total_atletas_ok,
        'total_academias': total_academias,
        'total_categorias': total_categorias,
        'total_chaves': total_chaves,
        'pesagens_realizadas': pesagens_realizadas,
        'top_academias': top_academias,
        'evento_atual': evento_atual,  # Evento atual para ações rápidas
    }
    
    return render(request, 'atletas/index.html', context)


# ========== CADASTRO DE ACADEMIAS ==========

def lista_academias(request):
    """Lista todas as academias"""
    academias = Academia.objects.all().order_by('-pontos', 'nome')
    return render(request, 'atletas/lista_academias.html', {'academias': academias})


def cadastrar_academia(request):
    """Cadastra uma nova academia"""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        sigla = request.POST.get('sigla', '')
        cidade = request.POST.get('cidade', '')
        estado = request.POST.get('estado', '')
        telefone = request.POST.get('telefone', '')
        
        academia = Academia.objects.create(
            nome=nome,
            sigla=sigla or '',
            cidade=cidade,
            estado=estado,
            telefone=telefone
        )
        
        # Upload do logo se fornecido
        if 'logo' in request.FILES:
            academia.logo = request.FILES['logo']
            academia.save()
        
        messages.success(request, f'Academia "{nome}" cadastrada com sucesso!')
        return redirect('lista_academias')
    
    return render(request, 'atletas/cadastrar_academia.html')


def editar_academia(request, academia_id):
    """Edita uma academia existente"""
    from django.contrib.auth.hashers import make_password
    
    academia = get_object_or_404(Academia, id=academia_id)
    
    if request.method == 'POST':
        academia.nome = request.POST.get('nome')
        academia.sigla = request.POST.get('sigla', '')
        academia.cidade = request.POST.get('cidade', '')
        academia.estado = request.POST.get('estado', '')
        academia.telefone = request.POST.get('telefone', '')
        
        # ✅ NOVO: Campos de login e senha
        usuario_acesso = request.POST.get('usuario_acesso', '').strip()
        senha_acesso = request.POST.get('senha_acesso', '').strip()
        senha_acesso_confirmar = request.POST.get('senha_acesso_confirmar', '').strip()
        
        # Validar usuário de acesso
        if usuario_acesso:
            # Verificar se o usuário já existe em outra academia
            academia_existente = Academia.objects.filter(
                usuario_acesso=usuario_acesso
            ).exclude(id=academia.id).first()
            
            if academia_existente:
                messages.error(request, f'O usuário "{usuario_acesso}" já está em uso por outra academia.')
                return render(request, 'atletas/editar_academia.html', {'academia': academia})
            
            academia.usuario_acesso = usuario_acesso
        
        # Validar e atualizar senha
        if senha_acesso:
            if senha_acesso != senha_acesso_confirmar:
                messages.error(request, 'As senhas não coincidem.')
                return render(request, 'atletas/editar_academia.html', {'academia': academia})
            
            if len(senha_acesso) < 6:
                messages.error(request, 'A senha deve ter pelo menos 6 caracteres.')
                return render(request, 'atletas/editar_academia.html', {'academia': academia})
            
            # Hash da senha
            academia.senha_acesso = make_password(senha_acesso)
        
        # Upload do logo se fornecido
        if 'logo' in request.FILES:
            academia.logo = request.FILES['logo']
        
        academia.save()
        messages.success(request, f'Academia "{academia.nome}" atualizada com sucesso!')
        return redirect('lista_academias')
    
    return render(request, 'atletas/editar_academia.html', {'academia': academia})


def excluir_academia(request, academia_id):
    """Exclui uma academia"""
    academia = get_object_or_404(Academia, id=academia_id)
    
    if request.method == 'POST':
        nome = academia.nome
        academia.delete()
        messages.success(request, f'Academia "{nome}" excluída com sucesso!')
        return redirect('lista_academias')
    
    return render(request, 'atletas/excluir_academia.html', {'academia': academia})


def atletas_academia(request, academia_id):
    """Lista os atletas de uma academia específica"""
    academia = get_object_or_404(Academia, id=academia_id)
    atletas = academia.atletas.all().order_by('nome')
    
    return render(request, 'atletas/atletas_academia.html', {
        'academia': academia,
        'atletas': atletas
    })


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
    
    # Buscar evento atual para ações rápidas
    from eventos.models import Evento
    evento_atual = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    if not evento_atual:
        evento_atual = Evento.objects.order_by('-data_evento').first()
    
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
        'evento_atual': evento_atual,  # Novo: evento atual para ações rápidas
    }

    # Modo de impressão: usa outro template, com a mesma lista filtrada
    if request.GET.get('modo') == 'imprimir':
        return render(request, 'atletas/relatorios/atletas_filtrados.html', context)

    return render(request, 'atletas/lista_atletas.html', context)


def detalhe_atleta(request, id):
    """Mostra detalhes completos de um atleta"""
    atleta = get_object_or_404(Atleta, id=id)
    
    # Buscar evento atual para ações rápidas
    from eventos.models import Evento
    evento_atual = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    if not evento_atual:
        evento_atual = Evento.objects.order_by('-data_evento').first()
    
    context = {
        'atleta': atleta,
        'evento_atual': evento_atual,  # Novo: evento atual para ações rápidas
    }
    
    return render(request, 'atletas/detalhe_atleta.html', context)


@login_required
def cadastrar_atleta(request):
    """Cadastra um novo atleta (apenas dados base - sem categoria/peso)"""
    # Verificar se usuário é academia e pegar sua academia
    academia_logada = None
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.tipo_usuario == 'academia' and request.user.profile.academia:
            academia_logada = request.user.profile.academia
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        ano_nasc = int(request.POST.get('ano_nasc'))
        sexo = request.POST.get('sexo')
        faixa = request.POST.get('faixa')
        
        # Se há academia logada, usar ela; senão, pegar do formulário
        if academia_logada:
            academia_id = academia_logada.id
        else:
            # Verificar permissão para cadastrar atletas de outras academias
            if request.user.is_authenticated and hasattr(request.user, 'profile'):
                if request.user.profile.tipo_usuario == 'academia':
                    messages.error(request, 'Você só pode cadastrar atletas da sua academia.')
                    return redirect('academia_painel')
            academia_id = int(request.POST.get('academia'))
        
        academia = get_object_or_404(Academia, id=academia_id)
        
        # Campos de federação
        federado = request.POST.get('federado') == 'on'
        zempo = request.POST.get('zempo', '').strip() if federado else None
        
        # Validação: se federado, zempo é obrigatório
        if federado and not zempo:
            messages.error(request, 'Número ZEMPO é obrigatório para atletas federados.')
            academias = Academia.objects.all().order_by('nome') if not academia_logada else None
            return render(request, 'atletas/cadastrar_atleta.html', {
                'academias': academias,
                'academia_logada': academia_logada
            })
        
        # Calcular classe automaticamente (mas não salvar categoria ainda)
        classe = calcular_classe(ano_nasc)
        
        # Criar atleta apenas com dados base (sem categoria/peso)
        atleta = Atleta.objects.create(
            nome=nome,
            ano_nasc=ano_nasc,
            sexo=sexo,
            faixa=faixa,
            academia=academia,
            classe=classe,  # Classe calculada automaticamente
            categoria_nome='',  # Vazio - será definido na inscrição
            categoria_limite='',  # Vazio
            peso_previsto=None,  # Não solicitado no cadastro base
            federado=federado,
            zempo=zempo if federado else None
        )
        
        messages.success(request, f'Atleta "{nome}" cadastrado com sucesso!')
        
        # Se é academia, redirecionar para o painel
        if academia_logada:
            return redirect('academia_painel')
        return redirect('lista_atletas')
    
    academias = Academia.objects.all().order_by('nome')
    
    return render(request, 'atletas/cadastrar_atleta.html', {
        'academias': academias,
        'academia_logada': academia_logada
    })


@login_required
def editar_atleta(request, id):
    """Edita um atleta existente (apenas dados básicos, não pesagem)"""
    atleta = get_object_or_404(Atleta, id=id)
    
    # Verificar permissões
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        if request.user.profile.tipo_usuario == 'academia':
            # Academia só pode editar seus próprios atletas
            if atleta.academia != request.user.profile.academia:
                messages.error(request, 'Você só pode editar atletas da sua academia.')
                return redirect('academia_painel')
            academia_logada = request.user.profile.academia
        else:
            academia_logada = None
    else:
        academia_logada = None
    
    if request.method == 'POST':
        atleta.nome = request.POST.get('nome')
        atleta.ano_nasc = int(request.POST.get('ano_nasc'))
        atleta.sexo = request.POST.get('sexo')
        atleta.faixa = request.POST.get('faixa')
        
        # Academia (só operacional pode alterar)
        if not academia_logada:
            academia_id = int(request.POST.get('academia'))
            atleta.academia = get_object_or_404(Academia, id=academia_id)
        
        # Campos de federação
        federado = request.POST.get('federado') == 'on'
        zempo = request.POST.get('zempo', '').strip() if federado else None
        
        # Validação: se federado, zempo é obrigatório
        if federado and not zempo:
            messages.error(request, 'Número ZEMPO é obrigatório para atletas federados.')
            academias = Academia.objects.all().order_by('nome') if not academia_logada else None
            return render(request, 'atletas/editar_atleta.html', {
                'atleta': atleta,
                'academias': academias,
                'academia_logada': academia_logada
            })
        
        atleta.federado = federado
        atleta.zempo = zempo if federado else None
        
        # Recalcular classe baseado no ano de nascimento
        from datetime import date
        ano_atual = date.today().year
        idade = ano_atual - atleta.ano_nasc
        atleta.classe = calcular_classe(atleta.ano_nasc)
        
        # Upload de foto se fornecido
        if 'foto' in request.FILES:
            atleta.foto = request.FILES['foto']
        
        atleta.save()
        messages.success(request, f'Atleta "{atleta.nome}" atualizado com sucesso!')
        
        # Redirecionar
        if academia_logada:
            return redirect('academia_painel')
        return redirect('lista_atletas')
    
    academias = Academia.objects.all().order_by('nome') if not academia_logada else None
    
    return render(request, 'atletas/editar_atleta.html', {
        'atleta': atleta,
        'academias': academias,
        'academia_logada': academia_logada
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
    """
    ⚠️ DESATIVADO: Pesagem agora está dentro de eventos.
    Redireciona para view de eventos.
    """
    from eventos.models import Evento
    from django.contrib import messages
    
    evento_id = request.GET.get('evento_id') or request.POST.get('evento_id')
    
    if evento_id:
        return redirect('eventos:pesagem_evento', evento_id=evento_id)
    
    # Sem evento_id, buscar evento ativo
    evento_ativo = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    
    if evento_ativo:
        messages.info(request, f'Redirecionando para pesagem do evento: {evento_ativo.nome}')
        return redirect('eventos:pesagem_evento', evento_id=evento_ativo.id)
    
    # Sem evento ativo, redirecionar para lista de eventos
    messages.info(request, 'Acesse a pesagem através de um evento específico.')
    return redirect('eventos:lista_eventos')


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


@require_http_methods(["POST"])
def registrar_peso(request, atleta_id):
    """
    Registra o peso oficial de um atleta.
    NUNCA salva automaticamente quando o peso está fora da categoria.
    Retorna JSON indicando se precisa mostrar modal de confirmação.
    """
    atleta = get_object_or_404(Atleta, id=atleta_id)
    
    try:
        peso_oficial = float(request.POST.get('peso_oficial'))
    except (ValueError, TypeError):
        return JsonResponse({'erro': 'Peso inválido'}, status=400)
    
    # Buscar categoria atual
    categoria_atual = Categoria.objects.filter(
        classe=atleta.classe,
        sexo=atleta.sexo,
        categoria_nome=atleta.categoria_nome
    ).first()
    
    if not categoria_atual:
        return JsonResponse({'erro': 'Categoria atual não encontrada'}, status=400)
    
    # Verificar se peso está dentro dos limites
    limite_max_real = categoria_atual.limite_max if categoria_atual.limite_max < 999.0 else 999999.0
    
    # SITUAÇÃO A: Peso dentro da categoria atual - SALVAR DIRETAMENTE
    if categoria_atual.limite_min <= peso_oficial <= limite_max_real:
        atleta.peso_oficial = peso_oficial
        atleta.status = "OK"
        atleta.motivo_ajuste = ""
        atleta.save()
        return JsonResponse({
            'sucesso': True,
            'mensagem': f'Peso registrado com sucesso: {peso_oficial}kg',
            'status': 'OK'
        })
    
    # SITUAÇÃO B: Peso fora dos limites - BUSCAR CATEGORIA SUGERIDA (SEM SALVAR)
    # Usar função utilitária que segue as regras corretas
    from atletas.utils import categoria_por_peso
    categoria_sugerida = categoria_por_peso(atleta.classe, atleta.sexo, peso_oficial)
    
    # Se encontrou categoria sugerida, verificar se é diferente da atual
    if categoria_sugerida and categoria_sugerida.id == categoria_atual.id:
        # A categoria sugerida é a mesma da atual - isso não deveria acontecer
        # mas se acontecer, não mostrar modal (já está na categoria correta)
        categoria_sugerida = None
    
    # Preparar resposta para modal
    limite_atual_str = f"{categoria_atual.limite_min} a {limite_max_real} kg" if limite_max_real < 999999.0 else f"{categoria_atual.limite_min} kg ou mais"
    
    if categoria_sugerida:
        # Existe categoria sugerida - mostrar modal com opção de remanejar
        # Garantir que a categoria sugerida é da mesma classe
        if categoria_sugerida.classe != atleta.classe:
            # ERRO: Categoria sugerida de classe diferente - não permitir
            categoria_sugerida = None
        else:
            # Calcular limite da categoria sugerida
            limite_sugerido_max = categoria_sugerida.limite_max if categoria_sugerida.limite_max < 999.0 else None
            limite_sugerido_str = f"{categoria_sugerida.limite_min} a {limite_sugerido_max} kg" if limite_sugerido_max else f"{categoria_sugerida.limite_min} kg ou mais"
            
            return JsonResponse({
                'show_modal': True,
                'peso': peso_oficial,
                'atleta_id': atleta_id,
                'atleta_nome': atleta.nome,
                'categoria_atual': {
                    'nome': categoria_atual.categoria_nome,
                    'classe': categoria_atual.classe,  # Adicionar classe para validação
                    'limite': limite_atual_str,
                    'limite_min': categoria_atual.limite_min,
                    'limite_max': limite_max_real
                },
                'categoria_sugerida': {
                    'nome': categoria_sugerida.categoria_nome,
                    'classe': categoria_sugerida.classe,  # Adicionar classe para validação
                    'limite': limite_sugerido_str,
                    'limite_min': categoria_sugerida.limite_min,
                    'limite_max': limite_sugerido_max if limite_sugerido_max else 999999.0
                },
                'pode_remanejar': True
            })
    
    # Não existe categoria sugerida - mostrar modal apenas com opção de desclassificar
    return JsonResponse({
        'show_modal': True,
        'peso': peso_oficial,
        'atleta_id': atleta_id,
        'atleta_nome': atleta.nome,
        'categoria_atual': {
            'nome': categoria_atual.categoria_nome,
            'classe': categoria_atual.classe,  # Adicionar classe para validação
            'limite': limite_atual_str,
            'limite_min': categoria_atual.limite_min,
            'limite_max': limite_max_real
        },
        'categoria_sugerida': None,
        'pode_remanejar': False
    })


@require_http_methods(["POST"])
def remanejar_peso(request, atleta_id):
    """
    Remaneja atleta para nova categoria após confirmação no modal.
    Grava peso, atualiza categoria, marca remanejado=True, reduz 1 ponto da academia.
    """
    atleta = get_object_or_404(Atleta, id=atleta_id)
    
    try:
        peso_oficial = float(request.POST.get('peso_oficial'))
        categoria_nova_nome = request.POST.get('categoria_nova')
    except (ValueError, TypeError, AttributeError):
        return JsonResponse({'erro': 'Dados inválidos'}, status=400)
    
    if not categoria_nova_nome:
        return JsonResponse({'erro': 'Categoria nova não informada'}, status=400)
    
    # Buscar categoria nova
    categoria_nova = Categoria.objects.filter(
        classe=atleta.classe,
        sexo=atleta.sexo,
        categoria_nome=categoria_nova_nome
    ).first()
    
    if not categoria_nova:
        return JsonResponse({'erro': 'Categoria não encontrada'}, status=400)
    
    # Atualizar atleta
    atleta.peso_oficial = peso_oficial
    atleta.categoria_ajustada = categoria_nova.categoria_nome
    limite_max = categoria_nova.limite_max if categoria_nova.limite_max < 999.0 else None
    if limite_max:
        atleta.categoria_limite = f"{categoria_nova.limite_min} a {limite_max} kg"
    else:
        atleta.categoria_limite = f"{categoria_nova.limite_min} kg ou mais"
    atleta.status = "OK"
    atleta.remanejado = True
    atleta.motivo_ajuste = f"Remanejado de {atleta.categoria_nome} para {categoria_nova_nome} (peso {peso_oficial}kg)"
    atleta.save()
    
    # Descontar 1 ponto da academia
    academia = atleta.academia
    academia.pontos = max(0, academia.pontos - 1)
    academia.save()
    
    # Criar log
    AdminLog.objects.create(
        tipo='REMANEJAMENTO',
        acao=f'Remanejamento - {atleta.nome}',
        atleta=atleta,
        academia=academia,
        detalhes=f'De {atleta.categoria_nome} para {categoria_nova_nome}. Peso: {peso_oficial} kg. Penalidade: -1 ponto(s).'
    )
    
    return JsonResponse({
        'sucesso': True,
        'mensagem': f'Atleta remanejado para {categoria_nova_nome}. Academia perdeu 1 ponto.',
        'status': 'REMANEJADO'
    })


@require_http_methods(["POST"])
def desclassificar_peso(request, atleta_id):
    """
    Desclassifica atleta por peso após confirmação no modal.
    Grava peso, marca status = "Eliminado Peso", categoria não muda.
    """
    atleta = get_object_or_404(Atleta, id=atleta_id)
    
    try:
        peso_oficial = float(request.POST.get('peso_oficial'))
    except (ValueError, TypeError):
        return JsonResponse({'erro': 'Peso inválido'}, status=400)
    
    # Atualizar atleta
    atleta.peso_oficial = peso_oficial
    atleta.status = "Eliminado Peso"
    atleta.motivo_ajuste = f"Desclassificado por peso {peso_oficial}kg fora da categoria {atleta.categoria_nome}"
    atleta.save()
    
    # Criar log
    AdminLog.objects.create(
        tipo='DESCLASSIFICACAO',
        acao=f'Desclassificação - {atleta.nome}',
        atleta=atleta,
        academia=atleta.academia,
        detalhes=f'Peso fora do limite: {peso_oficial} kg. Motivo: Peso fora do limite permitido.'
    )
    
    return JsonResponse({
        'sucesso': True,
        'mensagem': 'Atleta desclassificado por peso.',
        'status': 'DESCLASSIFICADO'
    })


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
    
    # ✅ CORRIGIDO: Não redirecionar para pesagem, apenas listar atletas
    return redirect('lista_atletas')


# ========== GERAÇÃO DE CHAVES ==========

def lista_chaves(request):
    """
    ⚠️ DESATIVADO: Lista de chaves agora está dentro de eventos.
    Redireciona para lista de eventos ou exige evento_id.
    """
    from eventos.models import Evento
    from django.contrib import messages
    
    # Verificar se tem evento_id na URL
    evento_id = request.GET.get('evento_id') or request.POST.get('evento_id')
    
    if evento_id:
        # Redirecionar para view de eventos
        return redirect('eventos:listar_chaves_evento', evento_id=evento_id)
    
    # Sem evento_id, buscar evento mais recente ou listar eventos
    evento_ativo = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    
    if evento_ativo:
        messages.info(request, f'Redirecionando para chaves do evento: {evento_ativo.nome}')
        return redirect('eventos:listar_chaves_evento', evento_id=evento_ativo.id)
    
    # Sem evento ativo, redirecionar para lista de eventos
    messages.info(request, 'Acesse as chaves através de um evento específico.')
    return redirect('eventos:lista_eventos')


def lista_chaves_legacy(request):
    """⚠️ LEGADO: Mantido apenas para compatibilidade. Use eventos."""
    chaves = Chave.objects.filter(evento__isnull=False).order_by('-evento__data_evento', 'classe', 'sexo', 'categoria')

    classe_filtro = request.GET.get('classe', '').strip()
    sexo_filtro = request.GET.get('sexo', '').strip()
    categoria_filtro = request.GET.get('categoria', '').strip()
    evento_id = request.GET.get('evento_id')

    # Filtrar por evento se fornecido
    if evento_id:
        chaves = chaves.filter(evento_id=evento_id)

    if classe_filtro:
        chaves = chaves.filter(classe__icontains=classe_filtro)
    if sexo_filtro:
        chaves = chaves.filter(sexo=sexo_filtro)
    if categoria_filtro:
        chaves = chaves.filter(categoria__icontains=categoria_filtro)

    # Código legado removido - redireciona para eventos


def verificar_atletas_categoria(request):
    """Verifica quantos atletas existem na categoria e se todos foram pesados"""
    from django.http import JsonResponse
    
    classe = request.GET.get('classe')
    sexo = request.GET.get('sexo')
    categoria = request.GET.get('categoria')
    
    if not classe or not sexo or not categoria:
        return JsonResponse({'erro': 'Parâmetros incompletos'}, status=400)
    
    # Buscar atletas aptos (status OK) da categoria
    atletas = Atleta.objects.filter(
        classe=classe,
        sexo=sexo,
        status='OK'
    ).exclude(
        classe='Festival'  # Festival não entra em chaves
    ).filter(
        Q(categoria_nome=categoria) | Q(categoria_ajustada=categoria)
    )
    
    num_atletas = atletas.count()
    
    # Verificar se todos têm peso validado
    pendentes = []
    for atleta in atletas:
        if not atleta.peso_oficial:
            pendentes.append(atleta.nome)
    
    if pendentes:
        mensagem = f"Ainda há {len(pendentes)} atleta(s) sem peso validado: {', '.join(pendentes[:3])}{'...' if len(pendentes) > 3 else ''}"
        return JsonResponse({
            'erro': mensagem,
            'num_atletas': num_atletas,
            'pendentes': pendentes
        })
    
    return JsonResponse({
        'sucesso': True,
        'num_atletas': num_atletas
    })


def gerar_chave_view(request):
    """
    ⚠️ DESATIVADO: Geração de chaves agora está dentro de eventos.
    Redireciona para view de eventos.
    """
    from eventos.models import Evento
    from django.contrib import messages
    
    evento_id = request.GET.get('evento_id') or request.POST.get('evento_id')
    
    if evento_id:
        # Redirecionar para listar categorias do evento
        return redirect('eventos:listar_categorias', evento_id=evento_id)
    
    # Sem evento_id, buscar evento ativo ou listar eventos
    evento_ativo = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    
    if evento_ativo:
        messages.info(request, f'Redirecionando para geração de chaves do evento: {evento_ativo.nome}')
        return redirect('eventos:listar_categorias', evento_id=evento_ativo.id)
    
    # Sem evento ativo, redirecionar para lista de eventos
    messages.info(request, 'Acesse a geração de chaves através de um evento específico.')
    return redirect('eventos:lista_eventos')


def gerar_chave_manual(request):
    """
    ⚠️ DESATIVADO: Chaves manuais agora precisam estar vinculadas a um evento.
    Redireciona para view de eventos ou exige evento_id.
    """
    from eventos.models import Evento
    from django.contrib import messages
    
    evento_id = request.GET.get('evento_id') or request.POST.get('evento_id')
    
    if evento_id:
        # Para chaves manuais, usar view de eventos ou criar uma nova rota
        messages.info(request, 'Chaves manuais devem ser criadas através de um evento específico.')
        return redirect('eventos:listar_categorias', evento_id=evento_id)
    
    # Sem evento_id, buscar evento ativo
    evento_ativo = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    
    if evento_ativo:
        messages.info(request, f'Redirecionando para criação de chaves do evento: {evento_ativo.nome}')
        return redirect('eventos:listar_categorias', evento_id=evento_ativo.id)
    
    # Sem evento ativo, redirecionar para lista de eventos
    messages.info(request, 'Acesse a criação de chaves através de um evento específico.')
    return redirect('eventos:lista_eventos')

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
    """
    ⚠️ DESATIVADO: Detalhe de chave agora está dentro de eventos.
    Redireciona para view de eventos.
    """
    from django.contrib import messages
    
    chave = get_object_or_404(Chave, id=chave_id)
    
    if not chave.evento:
        messages.error(request, 'Esta chave não está vinculada a nenhum evento. Use o comando de migração.')
        return redirect('eventos:lista_eventos')
    
    # Redirecionar para view de eventos
    return redirect('eventos:detalhe_chave_evento', evento_id=chave.evento.id, chave_id=chave.id)


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
        from atletas.services.luta_services import atualizar_vencedor_luta, recalcular_chave
        
        luta = get_object_or_404(Luta, id=luta_id)
        
        # ✅ BLOQUEIO: Não permitir editar resultados após o evento
        if luta.evento and luta.evento.is_expired:
            return JsonResponse({"error": "Resultados não podem ser modificados após o evento."}, status=403)
        
        vencedor_id = int(request.POST.get('vencedor'))
        tipo_vitoria = request.POST.get('tipo_vitoria', 'IPPON')
        wo_atleta_a = request.POST.get('wo_atleta_a') == 'on'
        wo_atleta_b = request.POST.get('wo_atleta_b') == 'on'
        
        vencedor = get_object_or_404(Atleta, id=vencedor_id)
        
        # ✅ USAR SERVIÇO DE ATUALIZAÇÃO
        atualizar_vencedor_luta(luta, vencedor, tipo_vitoria, wo_atleta_a, wo_atleta_b)
        
        # Recalcular chave para atualizar todas as próximas lutas
        recalcular_chave(luta.chave)
        
        # Atualizar estrutura JSON da chave (compatibilidade)
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

        # Reprocessar pontuação de academias (se chave finalizada)
        if luta.chave.finalizada:
            calcular_pontuacao_academias()
        
        # ✅ CORRIGIDO: Redirecionar para view de eventos se a chave tem evento
        if luta.chave.evento:
            # Verificar se veio da versão mobile (check header ou referrer)
            referer = request.META.get('HTTP_REFERER', '')
            if 'mobile' in referer:
                # Buscar próxima luta
                proxima_luta = None
                if luta.proxima_luta:
                    try:
                        proxima_luta = Luta.objects.get(id=luta.proxima_luta, chave=luta.chave)
                        return redirect('eventos:detalhe_chave_evento', evento_id=luta.chave.evento.id, chave_id=luta.chave.id)
                    except Luta.DoesNotExist:
                        pass
                # Se não há próxima luta, voltar para a chave do evento
                return redirect('eventos:detalhe_chave_evento', evento_id=luta.chave.evento.id, chave_id=luta.chave.id)
            
            return redirect('eventos:detalhe_chave_evento', evento_id=luta.chave.evento.id, chave_id=luta.chave.id)
        
        # ✅ LEGADO: Manter compatibilidade com chaves antigas sem evento
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
    """Ranking final das academias baseado em Evento"""
    # ✅ CORRIGIDO: Usar Evento ao invés de Campeonato
    from eventos.models import Evento, EventoAtleta
    from django.db.models import Sum
    
    # Buscar evento ativo ou mais recente
    evento = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    if not evento:
        evento = Evento.objects.order_by('-data_evento').first()
    
    if not evento:
        return render(request, 'atletas/ranking_academias.html', {
            'academias': [],
            'evento': None
        })
    
    # Calcular pontuação por academia baseado em EventoAtleta
    from atletas.models import Academia
    academias_com_pontos = []
    
    for academia in Academia.objects.all():
        evento_atletas = EventoAtleta.objects.filter(evento=evento, academia=academia)
        pontos_totais = evento_atletas.aggregate(total=Sum('pontos'))['total'] or 0
        
        # Contar medalhas (1º, 2º, 3º lugar)
        from atletas.models import Chave
        from atletas.services.luta_services import obter_resultados_chave
        
        ouro = prata = bronze = 0
        for chave in Chave.objects.filter(evento=evento):
            resultados = obter_resultados_chave(chave)
            if resultados:
                for pos, atleta_id in enumerate(resultados[:3], 1):
                    if evento_atletas.filter(atleta_id=atleta_id).exists():
                        if pos == 1:
                            ouro += 1
                        elif pos == 2:
                            prata += 1
                        elif pos == 3:
                            bronze += 1
        
        if pontos_totais > 0 or ouro > 0 or prata > 0 or bronze > 0:
            academias_com_pontos.append({
                'academia': academia,
                'pontos': pontos_totais,
                'ouro': ouro,
                'prata': prata,
                'bronze': bronze,
            })
    
    # Ordenar por pontos totais
    academias_ordenadas = sorted(academias_com_pontos, key=lambda x: x['pontos'], reverse=True)
    
    return render(request, 'atletas/ranking_academias.html', {
        'academias': academias_ordenadas,
        'evento': evento
    })


@require_http_methods(["GET"])
def api_ranking_academias(request):
    """API JSON com ranking de academias baseado em Evento"""
    # ✅ CORRIGIDO: Usar Evento ao invés de Campeonato
    from eventos.models import Evento, EventoAtleta
    from django.db.models import Sum
    
    # Buscar evento ativo ou mais recente
    evento = Evento.objects.filter(ativo=True).order_by('-data_evento').first()
    if not evento:
        evento = Evento.objects.order_by('-data_evento').first()
    
    if not evento:
        return JsonResponse([], safe=False)
    
    # Calcular pontuação por academia baseado em EventoAtleta
    from atletas.models import Academia
    from atletas.models import Chave
    from atletas.services.luta_services import obter_resultados_chave
    
    data = []
    for academia in Academia.objects.all():
        evento_atletas = EventoAtleta.objects.filter(evento=evento, academia=academia)
        pontos_total = evento_atletas.aggregate(total=Sum('pontos'))['total'] or 0
        
        # Contar medalhas
        ouro = prata = bronze = quarto = quinto = festival = remanejamento = 0
        for chave in Chave.objects.filter(evento=evento):
            resultados = obter_resultados_chave(chave)
            if resultados:
                for pos, atleta_id in enumerate(resultados[:5], 1):
                    if evento_atletas.filter(atleta_id=atleta_id).exists():
                        if pos == 1:
                            ouro += 1
                        elif pos == 2:
                            prata += 1
                        elif pos == 3:
                            bronze += 1
                        elif pos == 4:
                            quarto += 1
                        elif pos == 5:
                            quinto += 1
        
        # Contar festival e remanejamento
        festival = evento_atletas.filter(atleta__classe='Festival').count()
        remanejamento = evento_atletas.filter(remanejado=True).count()
        
        if pontos_total > 0 or ouro > 0 or prata > 0 or bronze > 0:
            data.append({
                "academia": academia.nome,
                "ouro": ouro,
                "prata": prata,
                "bronze": bronze,
                "quarto": quarto,
                "quinto": quinto,
                "festival": festival,
                "remanejamento": remanejamento,
                "pontos_total": pontos_total,
            })
    
    # Ordenar por pontos totais
    data.sort(key=lambda x: x['pontos_total'], reverse=True)
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


# ========== MÓDULO DE COMPETIÇÃO ==========

def lista_competicoes(request):
    """
    DESATIVADO: Esta view foi desativada.
    Use o módulo Eventos: /eventos/
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    messages.info(request, 'O módulo de Competições foi desativado. Use o módulo Eventos.')
    return redirect('eventos:lista_eventos')


def nova_competicao(request):
    """
    DESATIVADO: Esta view foi desativada.
    Use o módulo Eventos: /eventos/criar/
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    messages.info(request, 'O módulo de Competições foi desativado. Use o módulo Eventos.')
    return redirect('eventos:criar_evento')


def competicao_atual(request):
    """
    DESATIVADO: Esta view foi desativada.
    Use o módulo Eventos: /eventos/<id>/
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    from eventos.models import Evento
    # Redirecionar para o primeiro evento encerrado (histórico)
    evento = Evento.objects.filter(status='ENCERRADO').first()
    if evento:
        return redirect('eventos:ver_inscritos', evento_id=evento.id)
    messages.info(request, 'O módulo de Competições foi desativado. Use o módulo Eventos.')
    return redirect('eventos:lista_eventos')


def configurar_competicao(request, competicao_id):
    """
    DESATIVADO: Esta view foi desativada.
    Use o módulo Eventos: /eventos/<id>/configurar/
    """
    from django.shortcuts import redirect
    from django.contrib import messages
    from eventos.models import Evento
    # Tentar redirecionar para evento equivalente
    evento = Evento.objects.filter(status='ENCERRADO').first()
    if evento:
        return redirect('eventos:configurar_evento', evento_id=evento.id)
    messages.info(request, 'O módulo de Competições foi desativado. Use o módulo Eventos.')
    return redirect('eventos:lista_eventos')


# ========== SISTEMA DE LOGIN ==========

def login_tipo(request):
    """Tela intermediária de escolha do tipo de login"""
    if request.user.is_authenticated:
        # Se já está logado, redirecionar baseado no tipo
        if hasattr(request.user, 'profile'):
            if request.user.profile.tipo_usuario == 'academia':
                return redirect('academia_painel')
            elif request.user.profile.tipo_usuario in ['operacional', 'admin']:
                return redirect('index')
        # Superusers também vão para o sistema, não para o admin
        if request.user.is_superuser:
            return redirect('index')
    
    return render(request, 'atletas/login/login_tipo.html')


def login_academia(request):
    """Login para academias"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.tipo_usuario == 'academia':
            return redirect('academia_painel')
        else:
            logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar se tem perfil e se é academia
            if hasattr(user, 'profile'):
                if user.profile.tipo_usuario == 'academia':
                    login(request, user)
                    messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                    return redirect('academia_painel')
                else:
                    messages.error(request, 'Este login é apenas para academias. Use o login operacional.')
            else:
                messages.error(request, 'Perfil de usuário não encontrado. Entre em contato com o administrador.')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    
    return render(request, 'atletas/login/login_academia.html')


def login_operacional(request):
    """Login para usuários operacionais/gestão"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'profile') and request.user.profile.tipo_usuario in ['operacional', 'admin']:
            return redirect('index')
        elif request.user.is_superuser:
            return redirect('index')
        else:
            logout(request)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar se é superuser ou tem perfil operacional/admin
            if user.is_superuser:
                login(request, user)
                messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                return redirect('index')
            elif hasattr(user, 'profile'):
                if user.profile.tipo_usuario in ['operacional', 'admin']:
                    login(request, user)
                    messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                    return redirect('index')
                else:
                    messages.error(request, 'Este login é apenas para usuários operacionais. Use o login da academia.')
            else:
                messages.error(request, 'Perfil de usuário não encontrado. Entre em contato com o administrador.')
        else:
            messages.error(request, 'Usuário ou senha incorretos.')
    
    return render(request, 'atletas/login/login_operacional.html')


def user_logout(request):
    """Logout do usuário"""
    logout(request)
    messages.success(request, 'Logout realizado com sucesso.')
    return redirect('portal_publico')


# ========== PORTAL PÚBLICO ==========

def portal_publico(request):
    """
    Landing page pública do portal de inscrições.
    Lista eventos de forma organizada:
    - Eventos abertos para inscrição
    - Eventos futuros
    - Eventos em andamento (com chaves)
    - Eventos encerrados (com ranking final)
    """
    from eventos.models import Evento
    from atletas.models import Chave
    from datetime import date
    
    hoje = date.today()
    
    # 1. Eventos abertos para inscrição (status INSCRICOES e data_limite >= hoje)
    eventos_inscricao_aberta = Evento.objects.filter(
        ativo=True,
        status='INSCRICOES',
        data_limite_inscricao__gte=hoje
    ).order_by('data_evento')
    # ✅ NOVO: Filtrar eventos expirados
    eventos_inscricao_aberta = [e for e in eventos_inscricao_aberta if not e.is_expired]
    
    # 2. Eventos em pesagem (status PESAGEM)
    eventos_pesagem = Evento.objects.filter(
        ativo=True,
        status='PESAGEM'
    ).order_by('data_evento')
    # ✅ NOVO: Filtrar eventos expirados
    eventos_pesagem = [e for e in eventos_pesagem if not e.is_expired]
    
    # 3. Eventos em andamento (status ANDAMENTO e com chaves geradas)
    from django.db.models import Count as CountModel
    eventos_andamento = Evento.objects.filter(
        ativo=True,
        status='ANDAMENTO'
    ).annotate(
        total_chaves=CountModel('chaves')
    ).filter(total_chaves__gt=0).order_by('-data_evento')
    # ✅ NOVO: Filtrar eventos expirados
    eventos_andamento = [e for e in eventos_andamento if not e.is_expired]
    
    # 4. Eventos futuros (data_evento > hoje e ainda não começaram)
    eventos_futuros = Evento.objects.filter(
        ativo=True,
        data_evento__gt=hoje,
        status__in=['RASCUNHO', 'INSCRICOES']
    ).order_by('data_evento')
    # ✅ NOVO: Filtrar eventos expirados
    eventos_futuros = [e for e in eventos_futuros if not e.is_expired]
    
    # 5. Eventos encerrados (status ENCERRADO e com ranking final OU is_expired=True)
    eventos_encerrados = Evento.objects.filter(
        ativo=True,
        status='ENCERRADO'
    ).annotate(
        total_chaves=CountModel('chaves')
    ).filter(total_chaves__gt=0).order_by('-data_evento')[:10]  # Últimos 10
    # ✅ NOVO: Incluir eventos expirados mesmo que não tenham status ENCERRADO
    eventos_expirados_extra = Evento.objects.filter(
        ativo=True
    ).annotate(
        total_chaves=CountModel('chaves')
    ).filter(total_chaves__gt=0).exclude(id__in=[e.id for e in eventos_encerrados])
    eventos_expirados_extra = [e for e in eventos_expirados_extra if e.is_expired][:10]
    eventos_encerrados = list(eventos_encerrados) + eventos_expirados_extra
    eventos_encerrados = sorted(eventos_encerrados, key=lambda x: x.data_evento, reverse=True)[:10]
    
    context = {
        'eventos_inscricao_aberta': eventos_inscricao_aberta,
        'eventos_pesagem': eventos_pesagem,
        'eventos_andamento': eventos_andamento,
        'eventos_futuros': eventos_futuros,
        'eventos_encerrados': eventos_encerrados,
    }
    
    return render(request, 'atletas/portal/index.html', context)


@academia_required
def academia_painel(request):
    """Painel de inscrições da academia (após login)"""
    if not hasattr(request.user, 'profile') or not request.user.profile.academia:
        messages.error(request, 'Academia não vinculada ao seu perfil.')
        return redirect('login_tipo')
    
    academia = request.user.profile.academia
    
    # ✅ CORRIGIDO: Usar Evento ao invés de Campeonato
    from eventos.models import Evento
    from datetime import date
    hoje = date.today()
    eventos_publicos = Evento.objects.filter(
        ativo=True,
        status='INSCRICOES',
        data_limite_inscricao__gte=hoje
    ).order_by('data_evento')
    
    # Buscar atletas da academia (filtrado automaticamente)
    atletas = academia.atletas.all().order_by('nome')
    
    context = {
        'academia': academia,
        'eventos_publicos': eventos_publicos,
        'atletas': atletas,
    }
    
    return render(request, 'atletas/portal/academia_painel.html', context)


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
