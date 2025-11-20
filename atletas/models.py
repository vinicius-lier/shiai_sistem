from django.db import models
from datetime import date
from django.utils import timezone
from django.contrib.auth.models import User


class Academia(models.Model):
    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=10, blank=True, default='')
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    telefone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='logos_academias/', null=True, blank=True)
    senha_externa = models.CharField(max_length=100, blank=True)  # Senha para login externo (legado)
    
    # ✅ NOVO: Login independente para academias
    usuario_acesso = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Usuário de Acesso")
    senha_acesso = models.CharField(max_length=128, blank=True, null=True, verbose_name="Senha de Acesso (hash)")
    
    pontos = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Academia"
        verbose_name_plural = "Academias"
        ordering = ['nome']

    def __str__(self):
        if self.sigla:
            return f"{self.sigla} – {self.nome}"
        return self.nome
    
    def get_telefone_limpo(self):
        """Retorna o telefone apenas com números"""
        if not self.telefone:
            return ''
        return ''.join(filter(str.isdigit, self.telefone))
    
    def get_whatsapp_url(self, mensagem=''):
        """Gera URL do WhatsApp"""
        telefone_limpo = self.get_telefone_limpo()
        if not telefone_limpo:
            return None
        texto = mensagem or f"Olá, {'[' + self.sigla + '] ' if self.sigla else ''}{self.nome}!"
        from urllib.parse import quote
        return f"https://wa.me/55{telefone_limpo}?text={quote(texto)}"


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
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('Eliminado Peso', 'Eliminado por Peso'),
        ('Eliminado Indisciplina', 'Eliminado por Indisciplina'),
    ]

    nome = models.CharField(max_length=200)
    ano_nasc = models.IntegerField()
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    faixa = models.CharField(max_length=50)
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='atletas')
    
    # Campos de federação
    federado = models.BooleanField(default=False, verbose_name="É Federado?")
    zempo = models.CharField(max_length=15, blank=True, null=True, verbose_name="Número ZEMPO")
    
    # Campos calculados/setados durante inscrição
    classe = models.CharField(max_length=20, blank=True)
    categoria_nome = models.CharField(max_length=100, blank=True)
    categoria_limite = models.CharField(max_length=50, blank=True)  # "x a y kg"
    peso_previsto = models.FloatField(null=True, blank=True)
    
    # Campos da pesagem
    peso_oficial = models.FloatField(null=True, blank=True)
    categoria_ajustada = models.CharField(max_length=100, blank=True)
    motivo_ajuste = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='OK')
    remanejado = models.BooleanField(default=False)  # Marca se foi remanejado de categoria

    class Meta:
        verbose_name = "Atleta"
        verbose_name_plural = "Atletas"
        ordering = ['nome']
    
    def clean(self):
        """Validação: se federado=True, zempo é obrigatório. Se federado=False, zempo deve estar vazio."""
        from django.core.exceptions import ValidationError
        
        if self.federado and not self.zempo:
            raise ValidationError({'zempo': 'Número ZEMPO é obrigatório para atletas federados.'})
        
        if not self.federado and self.zempo:
            raise ValidationError({'zempo': 'Número ZEMPO só pode ser preenchido para atletas federados.'})
    
    def save(self, *args, **kwargs):
        """Override save para garantir validação e limpar zempo se não federado"""
        if not self.federado:
            self.zempo = None
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def idade(self):
        """Calcula a idade do atleta"""
        hoje = date.today()
        return hoje.year - self.ano_nasc
    
    def get_categoria_atual(self):
        """Retorna a categoria atual (ajustada ou original)"""
        categoria_nome = self.categoria_ajustada if self.categoria_ajustada else self.categoria_nome
        # Importar aqui para evitar import circular
        from atletas.models import Categoria as CategoriaModel
        return CategoriaModel.objects.filter(
            classe=self.classe,
            sexo=self.sexo,
            categoria_nome=categoria_nome
        ).first()
    
    def get_limite_categoria(self):
        """Retorna o limite correto da categoria atual"""
        categoria = self.get_categoria_atual()
        if categoria:
            if categoria.limite_max >= 999.0:
                return f"{categoria.limite_min} kg ou mais"
            else:
                return f"{categoria.limite_min} a {categoria.limite_max} kg"
        return self.categoria_limite
    
    def get_medalhas_count(self):
        """Retorna o número de medalhas conquistadas pelo atleta"""
        # Contar medalhas (1º, 2º, 3º lugar) nas chaves
        from atletas.utils import get_resultados_chave
        medalhas = 0
        for chave in self.chaves.all():
            resultados = get_resultados_chave(chave)
            if self.id in resultados[:3]:  # 1º, 2º ou 3º lugar
                medalhas += 1
        return medalhas
    
    def get_participacoes_count(self):
        """Retorna o número de participações em competições"""
        # Contar quantas chaves o atleta participou
        return self.chaves.count()

    def __str__(self):
        return f"{self.nome} ({self.classe} - {self.categoria_nome})"


class Chave(models.Model):
    TIPO_CHAVE_CHOICES = [
        ('MELHOR_DE_3', 'Melhor de 3 (2 atletas)'),
        ('CASADA_3', 'Lutas casadas para 3 atletas (A x B → Perdedor x C → Final)'),
        ('SIMPLES_3', 'Eliminatória Simples com 3 atletas (Stand-by)'),  # ✅ NOVO
        ('RODIZIO', 'Rodízio (3 a 5 atletas)'),
        ('ELIMINATORIA_SIMPLES', 'Eliminatória Simples'),
        ('ELIMINATORIA_REPESCAGEM', 'Eliminatória com Repescagem (modelo CBJ)'),
        ('OLIMPICA', 'Chave Olímpica (IJF)'),
        ('LIGA', 'Chave Liga (rodízio + semifinais)'),
        ('GRUPOS', 'Chave em Grupos (pools)'),
    ]
    
    classe = models.CharField(max_length=20)
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    categoria = models.CharField(max_length=100)
    atletas = models.ManyToManyField(Atleta, related_name='chaves')
    estrutura = models.JSONField(default=dict)  # Estrutura da chave (árvore de lutas)
    tipo_chave = models.CharField(
        max_length=30,
        choices=TIPO_CHAVE_CHOICES,
        null=True,
        blank=True,
        verbose_name="Tipo de Chave"
    )
    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        related_name='chaves',
        verbose_name="Evento"
    )
    finalizada = models.BooleanField(default=False, verbose_name="Chave Finalizada")
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"
        ordering = ['classe', 'sexo', 'categoria']

    def __str__(self):
        return f"{self.classe} - {self.get_sexo_display()} - {self.categoria}"
    
    def get_total_atletas(self):
        """Retorna o total de atletas na chave"""
        return self.atletas.count()
    
    def get_lutas_pendentes(self):
        """Retorna o número de lutas pendentes"""
        return self.lutas.filter(concluida=False).count()
    
    def get_lutas_concluidas(self):
        """Retorna o número de lutas concluídas"""
        return self.lutas.filter(concluida=True).count()


class Luta(models.Model):
    TIPO_VITORIA_CHOICES = [
        ("IPPON", "Ippon"),
        ("WAZARI", "Wazari"),
        ("WAZARI_WAZARI", "Wazari-Wazari"),
        ("YUKO", "Yuko"),
        ("WO", "W.O. (Walkover)"),
        ("DESCLASSIFICADO", "Desclassificado"),
    ]
    
    TIPO_LUTA_CHOICES = [
        ('NORMAL', 'Luta Normal'),
        ('REPESCAGEM', 'Repescagem'),
        ('BRONZE', 'Disputa de Bronze'),
        ('FINAL', 'Final'),
    ]
    
    chave = models.ForeignKey(Chave, on_delete=models.CASCADE, related_name='lutas')
    evento = models.ForeignKey(
        'eventos.Evento',
        on_delete=models.CASCADE,
        related_name='lutas',
        verbose_name="Evento"
    )
    atleta_a = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lutas_como_a', null=True, blank=True)
    atleta_b = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lutas_como_b', null=True, blank=True)
    vencedor = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lutas_vencidas', null=True, blank=True)
    perdedor = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lutas_perdidas', null=True, blank=True)
    round = models.IntegerField()  # 1, 2, 3... (fase da chave)
    proxima_luta = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='lutas_anteriores')
    proxima_luta_repescagem = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='lutas_repescagem_anteriores')
    concluida = models.BooleanField(default=False)
    tipo_vitoria = models.CharField(max_length=20, choices=TIPO_VITORIA_CHOICES, blank=True)
    tipo_luta = models.CharField(max_length=20, choices=TIPO_LUTA_CHOICES, default='NORMAL')
    pontos_vencedor = models.IntegerField(default=0)
    pontos_perdedor = models.IntegerField(default=0)
    ippon_count = models.IntegerField(default=0)
    wazari_count = models.IntegerField(default=0)
    yuko_count = models.IntegerField(default=0)
    wo_atleta_a = models.BooleanField(default=False, verbose_name="WO Atleta A")
    wo_atleta_b = models.BooleanField(default=False, verbose_name="WO Atleta B")
    observacoes = models.TextField(blank=True, verbose_name="Observações")

    class Meta:
        verbose_name = "Luta"
        verbose_name_plural = "Lutas"
        ordering = ['chave', 'round', 'id']
        indexes = [
            models.Index(fields=['evento', 'chave']),
            models.Index(fields=['evento', 'round']),
        ]

    def __str__(self):
        nome_a = self.atleta_a.nome if self.atleta_a else "WO"
        nome_b = self.atleta_b.nome if self.atleta_b else "WO"
        tipo = f" [{self.get_tipo_luta_display()}]" if self.tipo_luta != 'NORMAL' else ""
        return f"Round {self.round}{tipo}: {nome_a} vs {nome_b}"
    
    def get_perdedor(self):
        """Retorna o perdedor da luta"""
        if self.vencedor:
            if self.atleta_a and self.atleta_a.id == self.vencedor.id:
                return self.atleta_b
            elif self.atleta_b and self.atleta_b.id == self.vencedor.id:
                return self.atleta_a
        return None
    
    def tem_wo(self):
        """Verifica se a luta tem WO"""
        return self.wo_atleta_a or self.wo_atleta_b


class AdminLog(models.Model):
    TIPO_CHOICES = [
        ('REMANEJAMENTO', 'Remanejamento'),
        ('DESCLASSIFICACAO', 'Desclassificação'),
        ('PESAGEM', 'Pesagem'),
        ('OUTRO', 'Outro'),
    ]
    
    data_hora = models.DateTimeField(default=timezone.now)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='OUTRO')
    acao = models.CharField(max_length=200)
    atleta = models.ForeignKey(Atleta, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    academia = models.ForeignKey(Academia, on_delete=models.SET_NULL, null=True, blank=True, related_name='logs')
    detalhes = models.TextField(blank=True)  # Para armazenar informações adicionais (ex: categoria antiga/nova)
    usuario_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Log Administrativo"
        verbose_name_plural = "Logs Administrativos"
        ordering = ['-data_hora']

    def __str__(self):
        return f"{self.data_hora} - {self.get_tipo_display()}: {self.acao}"


class Campeonato(models.Model):
    nome = models.CharField(max_length=200, default="Campeonato Padrão")
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    local = models.CharField(max_length=200, blank=True)
    prazo_inscricao = models.DateField(null=True, blank=True)
    publicado = models.BooleanField(default=False)  # Se está visível no portal público
    ativo = models.BooleanField(default=True)

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
        return f"{self.academia.nome} - {self.campeonato.nome} ({self.pontos_totais} pts)"


class UserProfile(models.Model):
    TIPO_USUARIO_CHOICES = [
        ('academia', 'Academia'),
        ('operacional', 'Operacional/Gestão'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    tipo_usuario = models.CharField(max_length=20, choices=TIPO_USUARIO_CHOICES, default='operacional')
    academia = models.ForeignKey(Academia, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')
    telefone = models.CharField(max_length=20, blank=True)
    
    # Permissões específicas
    pode_inscricao = models.BooleanField(default=True)
    pode_pesagem = models.BooleanField(default=True)
    pode_chave = models.BooleanField(default=True)
    pode_dashboard = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuários"
        ordering = ['user__username']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_usuario_display()}"