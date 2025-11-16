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
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
    }
    
    return render(request, 'atletas/pesagem.html', context)


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
        'classes': classes,
        'categorias': categorias,
        'classe_filtro': classe_filtro,
        'sexo_filtro': sexo_filtro,
        'categoria_filtro': categoria_filtro,
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
