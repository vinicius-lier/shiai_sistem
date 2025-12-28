from django.urls import path

from matches import views

app_name = "matches"

urlpatterns = [
    path("", views.acompanhamento, name="acompanhamento"),
    path("mesa/", views.mesa_matches, name="mesa"),
    path("mesas/", views.organizacao_mesas, name="mesas"),
    path("acompanhamento/", views.acompanhamento, name="acompanhamento_page"),
]

