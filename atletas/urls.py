from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.landing_publica, name='landing_publica'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('painel/organizacoes/', views.painel_organizacoes, name='painel_organizacoes'),
    path('painel/organizacoes/<int:organizacao_id>/alterar-status/', views.toggle_organizacao_status, name='toggle_organizacao_status'),
    path('<slug:organizacao_slug>/', include('atletas.urls_org')),
]
