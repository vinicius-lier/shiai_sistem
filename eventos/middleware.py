"""
Middleware para autenticação de academias no painel.
"""
from django.shortcuts import redirect
from django.urls import reverse
from atletas.models import Academia


class AcademiaAuthMiddleware:
    """
    Middleware para proteger rotas do painel da academia.
    Verifica se há academia_id na sessão.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Rotas que NÃO precisam de autenticação de academia
        self.exempt_paths = [
            '/eventos/academia/login/',
            '/eventos/academia/logout/',
            '/eventos/academia/trocar-senha/',
            '/academia/login/',
            '/academia/logout/',
            '/academia/trocar-senha/',
            '/portal/',
            '/',
            '/admin/',
        ]

    def __call__(self, request):
        # Verificar se a rota precisa de autenticação
        path = request.path
        
        # ✅ CORRIGIDO: Verificar rotas de academia (com e sem prefixo /eventos)
        is_rota_academia = path.startswith('/academia/') or path.startswith('/eventos/academia/')
        
        # Se não é rota de academia, não precisa verificar
        if not is_rota_academia:
            return self.get_response(request)
        
        # ✅ CORRIGIDO: Se está em uma rota exempt (login, logout, trocar-senha), permitir SEMPRE
        rotas_exempt = [
            '/eventos/academia/login/',
            '/eventos/academia/logout/',
            '/eventos/academia/trocar-senha/',
            '/academia/login/',
            '/academia/logout/',
            '/academia/trocar-senha/',
        ]
        
        if any(path == exempt or path.startswith(exempt) for exempt in rotas_exempt):
            return self.get_response(request)
        
        # Verificar se há academia_id na sessão
        academia_id = request.session.get('academia_id')
        
        if not academia_id:
            # Redirecionar para login
            return redirect('eventos:academia_login')
        
        # Verificar se a academia existe e está ativa
        try:
            academia = Academia.objects.get(id=academia_id)
            # Adicionar academia ao request para uso nas views
            request.academia = academia
            
            # ✅ NOVO: Verificar se é primeiro acesso (senha não configurada ou senha padrão)
            # Se não tem senha_acesso ou se a senha é a padrão, forçar troca
            precisa_trocar_senha = False
            if not academia.senha_acesso:
                precisa_trocar_senha = True
            elif academia.senha_acesso and not request.session.get('senha_trocada'):
                # Verificar se é senha padrão (hash de senha conhecida)
                from django.contrib.auth.hashers import check_password
                senhas_padrao = ['123456', 'senha', 'academia', academia.usuario_acesso or '']
                for senha_padrao in senhas_padrao:
                    if senha_padrao and check_password(senha_padrao, academia.senha_acesso):
                        precisa_trocar_senha = True
                        break
            
            # Se precisa trocar senha e não está na página de trocar senha
            if precisa_trocar_senha and not (path.startswith('/academia/trocar-senha') or path.startswith('/eventos/academia/trocar-senha')):
                return redirect('eventos:academia_trocar_senha')
            
        except Academia.DoesNotExist:
            # Academia não existe mais, limpar sessão
            request.session.pop('academia_id', None)
            return redirect('eventos:academia_login')
        
        return self.get_response(request)

