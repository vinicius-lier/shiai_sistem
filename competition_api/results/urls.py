from django.urls import path

from results import views

app_name = "results"

urlpatterns = [
    path("oficiais/", views.oficiais, name="oficiais"),
]

