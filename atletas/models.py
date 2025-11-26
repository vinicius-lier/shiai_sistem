from django.db import models
class Academia(models.Model):
    nome = models.CharField(max_length=200)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)

    class Meta:
        verbose_name = "Academia"
        verbose_name_plural = "Academias"
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    classe = models.CharField(max_length=20)  # SUB 9, SUB 11, SUB 13...
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    categoria_nome = models.CharField(max_length=100)
    limite_min = models.FloatField()
    limite_max = models.FloatField()
    label = models.CharField(max_length=150)  # ex.: "SUB 11 - Meio Leve"

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['classe', 'sexo', 'limite_min']

    def __str__(self):
        return self.label


class Atleta(models.Model):

    class Meta:
        verbose_name = "Atleta"
        verbose_name_plural = "Atletas"
        ordering = ['nome']

    @property
    def idade(self):
        """Calcula a idade do atleta"""
    classe = models.CharField(max_length=20)
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    categoria = models.CharField(max_length=100)
    atletas = models.ManyToManyField(Atleta, related_name='chaves')
    estrutura = models.JSONField(default=dict)  # Estrutura da chave (árvore de lutas)

    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"


class Luta(models.Model):
    TIPO_VITORIA_CHOICES = [
        ("IPPON", "Ippon"),
        ("WAZARI", "Wazari"),
        ("YUKO", "Yuko"),
    ]
    
    chave = models.ForeignKey(Chave, on_delete=models.CASCADE, related_name='lutas')
    atleta_a = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lutas_como_a', null=True, blank=True)
    atleta_b = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lutas_como_b', null=True, blank=True)
    vencedor = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lutas_vencidas', null=True, blank=True)
    round = models.IntegerField()  # 1, 2, 3... (fase da chave)
    proxima_luta = models.IntegerField(null=True, blank=True)  # ID da próxima luta
    concluida = models.BooleanField(default=False)
    tipo_vitoria = models.CharField(max_length=20, choices=TIPO_VITORIA_CHOICES, blank=True)
    pontos_vencedor = models.IntegerField(default=0)
    pontos_perdedor = models.IntegerField(default=0)
    ippon_count = models.IntegerField(default=0)
    wazari_count = models.IntegerField(default=0)
    yuko_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Luta"
        verbose_name_plural = "Lutas"
        ordering = ['chave', 'round', 'id']

    def __str__(self):
        nome_a = self.atleta_a.nome if self.atleta_a else "WO"
        nome_b = self.atleta_b.nome if self.atleta_b else "WO"
        return f"Round {self.round}: {nome_a} vs {nome_b}"


class AdminLog(models.Model):
    data_hora = models.DateTimeField(default=timezone.now)
    acao = models.CharField(max_length=200)
    usuario_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Log Administrativo"
        verbose_name_plural = "Logs Administrativos"
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.data_hora} - {self.acao}"



    class Meta:
        verbose_name = "Campeonato"
        verbose_name_plural = "Campeonatos"
        ordering = ['-data_inicio', 'nome']

    def __str__(self):
        return self.nome


class AcademiaPontuacao(models.Model):
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='pontuacoes')
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='pontuacoes')
    ouro = models.IntegerField(default=0)
    prata = models.IntegerField(default=0)
    bronze = models.IntegerField(default=0)
    quarto = models.IntegerField(default=0)
    quinto = models.IntegerField(default=0)
    festival = models.IntegerField(default=0)
    remanejamento = models.IntegerField(default=0)
    pontos_totais = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Pontuação de Academia"
        verbose_name_plural = "Pontuações de Academias"
        unique_together = ('campeonato', 'academia')
        ordering = ['-pontos_totais', 'academia__nome']

    def __str__(self):
