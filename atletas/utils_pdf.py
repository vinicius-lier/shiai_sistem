"""
Utilitários para geração de PDF usando xhtml2pdf
Compatível com Render e outras plataformas de deploy
"""
from django.http import HttpResponse
from django.template.loader import render_to_string
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def gerar_pdf_de_html(html_content, filename='documento.pdf', content_disposition='attachment'):
    """
    Gera um PDF a partir de conteúdo HTML usando xhtml2pdf
    
    Args:
        html_content (str): Conteúdo HTML a ser convertido em PDF
        filename (str): Nome do arquivo PDF
        content_disposition (str): 'attachment' para download ou 'inline' para visualização
    
    Returns:
        HttpResponse: Resposta HTTP com o PDF gerado
    """
    try:
        from xhtml2pdf import pisa
        
        # Criar buffer para o PDF
        buffer = BytesIO()
        
        # Converter HTML para PDF
        pdf = pisa.pisaDocument(
            BytesIO(html_content.encode('UTF-8')),
            buffer,
            encoding='UTF-8'
        )
        
        if pdf.err:
            logger.error(f'Erro ao gerar PDF: {pdf.err}')
            raise Exception(f'Erro ao gerar PDF: {pdf.err}')
        
        # Obter conteúdo do buffer
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Criar resposta HTTP
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'{content_disposition}; filename="{filename}"'
        
        return response
        
    except ImportError:
        logger.error('xhtml2pdf não está instalado. Instale com: pip install xhtml2pdf')
        raise ImportError(
            'xhtml2pdf não está instalado. '
            'Instale com: pip install xhtml2pdf'
        )
    except Exception as e:
        logger.error(f'Erro ao gerar PDF: {str(e)}')
        raise


def renderizar_template_para_pdf(template_path, context, filename='documento.pdf', content_disposition='attachment'):
    """
    Renderiza um template Django e converte para PDF
    
    Args:
        template_path (str): Caminho do template Django
        context (dict): Contexto para o template
        filename (str): Nome do arquivo PDF
        content_disposition (str): 'attachment' para download ou 'inline' para visualização
    
    Returns:
        HttpResponse: Resposta HTTP com o PDF gerado
    """
    try:
        # Renderizar template para HTML
        html_content = render_to_string(template_path, context)
        
        # Gerar PDF a partir do HTML
        return gerar_pdf_de_html(html_content, filename, content_disposition)
        
    except Exception as e:
        logger.error(f'Erro ao renderizar template para PDF: {str(e)}')
        raise

