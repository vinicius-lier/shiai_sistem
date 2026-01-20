"""Middlewares da aplicação atletas."""
import re
from django.http import HttpResponseRedirect, HttpResponseNotFound

from atletas.models import Organizador


class MobileRedirectMiddleware:
    """Middleware que redireciona automaticamente para versões mobile"""
    
    MOBILE_PATTERNS = [
        r'android',
        r'iphone',
        r'ipad',
        r'ipod',
        r'blackberry',
        r'windows phone',
        r'mobile',
        r'opera mini',
        r'opera mobi'
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Verificar se já está na versão mobile ou se tem parâmetro ?desktop
        if request.GET.get('desktop') == '1' or 'mobile' in request.path:
            response = self.get_response(request)
            return response
        
        # Verificar User-Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = any(re.search(pattern, user_agent) for pattern in self.MOBILE_PATTERNS)
        
        # Verificar largura da tela (se disponível via cookie)
        screen_width = request.COOKIES.get('screen_width')
        if screen_width:
            try:
                is_mobile = int(screen_width) < 768
            except (ValueError, TypeError):
                pass
        
        # Se for mobile, redirecionar para versão mobile
        if is_mobile:
            path = request.path.strip('/')
            
            # Pesagem
            if path == 'pesagem':
                return HttpResponseRedirect('/pesagem/mobile/')
            
            # Chave (apenas se for detalhe de chave específica)
            elif path.startswith('chaves/') and path.count('/') == 1 and path.replace('chaves/', '').isdigit():
                chave_id = path.split('/')[-1]
                try:
                    int(chave_id)  # Verificar se é um ID válido
                    return HttpResponseRedirect(f'/chave/mobile/{chave_id}/')
                except ValueError:
                    pass
        
        response = self.get_response(request)
        
        # Adicionar script para detectar largura da tela e redirecionar se necessário
        if response.get('Content-Type', '').startswith('text/html'):
            script = '''
            <script>
            (function() {
                // Detectar largura da tela e definir cookie
                var screenWidth = window.innerWidth;
                if (!document.cookie.includes('screen_width')) {
                    document.cookie = 'screen_width=' + screenWidth + '; path=/';
                }
                
                // Verificar se já está na versão mobile ou tem desktop=1
                if (window.location.href.includes('mobile') || window.location.href.includes('desktop=1')) {
                    return;
                }
                
                // Detectar mobile
                var isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                               screenWidth < 768;
                
                if (isMobile) {
                    var path = window.location.pathname;
                    
                    // Pesagem
                    if (path === '/pesagem/' || path === '/pesagem') {
                        window.location.href = '/pesagem/mobile/';
                        return;
                    }
                    
                    // Detalhe da chave
                    var chaveMatch = path.match(/^\\/chaves\\/(\\d+)\\/?$/);
                    if (chaveMatch) {
                        window.location.href = '/chave/mobile/' + chaveMatch[1] + '/';
                        return;
                    }
                }
            })();
            </script>
            '''
            # Inserir script antes do fechamento do body
            try:
                content = response.content.decode('utf-8')
                if '</body>' in content:
                    content = content.replace('</body>', script + '</body>')
                    response.content = content.encode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                pass
        
        return response


class OrganizacaoMiddleware:
    """
    Middleware responsável por resolver a organização (Organizador) a partir do primeiro
    segmento da URL (`/<organizacao_slug>/...`) e vinculá-la ao `request.organizacao`.
    
    IMPORTANTE:
    - NÃO interfere em rotas globais: '/', '/login/', '/logout/', '/painel/organizacoes/', '/admin/', '/academia/*', '/static/', '/media/'.
    - Apenas caminhos que começam com um slug de organização são tratados.
    """

    GLOBAL_PREFIXES = (
        '/admin/',
        '/static/',
        '/media/',
        '/matches',
        '/matches/',
        '/login/',
        '/logout/',
        '/selecionar-organizacao/',
        '/painel/',
        '/academia/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path or '/'

        # Ignorar rotas globais e raiz
        if path == '/' or any(path.startswith(prefix) for prefix in self.GLOBAL_PREFIXES):
            return self.get_response(request)

        # Extrair possível slug do primeiro segmento
        # Ex: /minha-org/dashboard/ -> slug = 'minha-org'
        partes = path.lstrip('/').split('/', 1)
        if not partes or not partes[0]:
            return self.get_response(request)

        slug = partes[0]

        try:
            organizacao = Organizador.objects.get(slug=slug, ativo=True)
        except Organizador.DoesNotExist:
            # Se não encontrar organização para um path que deveria ser multi-tenant,
            # retornamos 404 explicando o problema.
            return HttpResponseNotFound("Organização não encontrada ou inativa.")

        # Anexar ao request para uso nas views/templates
        request.organizacao = organizacao
        request.organizador = organizacao  # alias para compatibilidade
        request.organizacao_slug = slug

        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Remove o slug dos kwargs para evitar TypeError em views que não declaram
        explicitamente o parâmetro e mantém a organização já resolvida no request.
        """
        if view_kwargs is not None:
            view_kwargs.pop('organizacao_slug', None)
        return None
