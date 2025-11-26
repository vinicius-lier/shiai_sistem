"""Middleware para detectar dispositivos móveis e redirecionar automaticamente"""
import re
from django.http import HttpResponseRedirect


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

