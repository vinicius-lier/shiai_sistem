from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from atletas.models import Organizador


def _is_superuser(user):
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(_is_superuser)
def selecionar_organizacao(request):
    """Tela simples para superuser escolher uma organização e entrar no dashboard"""
    organizacoes = Organizador.objects.all().order_by('nome')
    if request.method == 'POST':
        slug = request.POST.get('organizacao_slug')
        if slug and Organizador.objects.filter(slug=slug, ativo=True).exists():
            return redirect('index', organizacao_slug=slug)
    return render(request, 'atletas/selecionar_organizacao.html', {'organizacoes': organizacoes})

