"""
URL configuration for competition_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render


def root(request):
    """
    Root público do Competition API.

    - Mostra uma tela informativa (sem redirect automático), pois este módulo
      não deve ser o entrypoint do sistema.
    """
    return render(request, "matches/public_landing.html")

urlpatterns = [
    path("", root),
    path('admin/', admin.site.urls),
    path('matches/', include('matches.urls')),
    path('results/', include('results.urls')),
]
