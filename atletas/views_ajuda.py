"""
Views para o módulo de ajuda e manuais
"""
import re
from django.shortcuts import render
from django.http import HttpResponse
import os
from django.conf import settings

def markdown_to_html(markdown_text):
    """Converte Markdown básico para HTML"""
    html = markdown_text
    
    # Code blocks primeiro (para não interferir com outras conversões)
    html = re.sub(r'```(\w+)?\n(.*?)```', r'<pre><code>\2</code></pre>', html, flags=re.DOTALL)
    
    # Headers (processar do maior para o menor)
    html = re.sub(r'^#### (.+)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
    
    # Horizontal rules
    html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
    
    # Blockquotes
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)
    
    # Bold (antes de italic para evitar conflitos)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    
    # Italic (após bold)
    html = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', html)
    
    # Inline code
    html = re.sub(r'`([^`]+)`', r'<code>\1</code>', html)
    
    # Links
    html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)
    
    # Processar linhas para parágrafos e listas
    lines = html.split('\n')
    in_list = False
    list_type = None
    result = []
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Verificar se é item de lista
        if re.match(r'^[-*+] (.+)$', line_stripped):
            if not in_list or list_type != 'ul':
                if in_list and list_type == 'ol':
                    result.append('</ol>')
                if not in_list:
                    result.append('<ul>')
                in_list = True
                list_type = 'ul'
            content = re.sub(r'^[-*+] (.+)$', r'\1', line_stripped)
            result.append(f'<li>{content}</li>')
        elif re.match(r'^\d+\. (.+)$', line_stripped):
            if not in_list or list_type != 'ol':
                if in_list and list_type == 'ul':
                    result.append('</ul>')
                if not in_list:
                    result.append('<ol>')
                in_list = True
                list_type = 'ol'
            content = re.sub(r'^\d+\. (.+)$', r'\1', line_stripped)
            result.append(f'<li>{content}</li>')
        else:
            # Fechar lista se estava em uma
            if in_list:
                result.append(f'</{list_type}>')
                in_list = False
                list_type = None
            
            # Processar linha
            if line_stripped:
                # Se já é um elemento HTML (h1, h2, etc.), adicionar direto
                if line_stripped.startswith('<'):
                    result.append(line_stripped)
                else:
                    # Verificar se não é um elemento HTML já processado
                    if not any(line_stripped.startswith(f'<{tag}') for tag in ['h1', 'h2', 'h3', 'h4', 'hr', 'blockquote', 'pre', 'ul', 'ol']):
                        result.append(f'<p>{line_stripped}</p>')
            else:
                result.append('')
    
    # Fechar lista se ainda estiver aberta
    if in_list:
        result.append(f'</{list_type}>')
    
    html = '\n'.join(result)
    
    # Limpar parágrafos vazios e múltiplos
    html = re.sub(r'<p></p>', '', html)
    html = re.sub(r'<p>\s*</p>', '', html)
    
    return html

def ajuda_manual(request):
    """Página principal de ajuda e manuais"""
    return render(request, 'atletas/ajuda_manual.html')

def ajuda_manual_web(request, tipo):
    """Exibe manual em formato web (markdown renderizado)"""
    if tipo == 'operacional':
        manual_path = os.path.join(settings.BASE_DIR, 'MANUAL_OPERACIONAL.md')
        titulo = 'Manual Operacional'
        descricao = 'Guia completo para gestores e organizadores de competições'
    elif tipo == 'academia':
        manual_path = os.path.join(settings.BASE_DIR, 'MANUAL_ACADEMIA.md')
        titulo = 'Manual Academia'
        descricao = 'Guia completo para academias participantes'
    else:
        return render(request, 'atletas/ajuda_manual.html')
    
    try:
        with open(manual_path, 'r', encoding='utf-8') as f:
            conteudo_md = f.read()
        conteudo_html = markdown_to_html(conteudo_md)
    except FileNotFoundError:
        conteudo_html = f"<p>Manual {tipo} não encontrado.</p>"
    
    context = {
        'titulo': titulo,
        'descricao': descricao,
        'conteudo': conteudo_html,
        'tipo': tipo
    }
    return render(request, 'atletas/ajuda_manual_web.html', context)

def ajuda_documentacao_tecnica(request):
    """Exibe documentação técnica resumida"""
    doc_path = os.path.join(settings.BASE_DIR, 'DOCUMENTACAO_TECNICA.md')
    
    try:
        with open(doc_path, 'r', encoding='utf-8') as f:
            conteudo_md = f.read()
        # Limitar a 2000 primeiras linhas para resumo
        linhas = conteudo_md.split('\n')
        if len(linhas) > 2000:
            conteudo_md = '\n'.join(linhas[:2000]) + '\n\n... (documentação completa disponível no arquivo DOCUMENTACAO_TECNICA.md)'
        conteudo_html = markdown_to_html(conteudo_md)
    except FileNotFoundError:
        conteudo_html = "<p>Documentação técnica não encontrada.</p>"
    
    context = {
        'titulo': 'Documentação Técnica',
        'descricao': 'Documentação completa para desenvolvedores',
        'conteudo': conteudo_html
    }
    return render(request, 'atletas/ajuda_manual_web.html', context)

