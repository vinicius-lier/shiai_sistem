from django.db import models


class BeltChoices(models.TextChoices):
    BRANCA = "BRANCA", "Branca"
    CINZA = "CINZA", "Cinza"
    PONTEIRA_CINZA = "P_CINZA", "P. Cinza"
    AZUL = "AZUL", "Azul"
    PONTEIRA_AZUL = "P_AZUL", "P. Azul"
    AMARELA = "AMARELA", "Amarela"
    PONTEIRA_AMARELA = "P_AMARELA", "P. Amarela"
    LARANJA = "LARANJA", "Laranja"
    PONTEIRA_LARANJA = "P_LARANJA", "P. Laranja"
    VERDE = "VERDE", "Verde"
    ROXA = "ROXA", "Roxa"
    MARROM = "MARROM", "Marrom"
    PRETA = "PRETA", "Preta"

