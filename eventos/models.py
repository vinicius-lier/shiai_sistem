from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import now
from atletas.models import Academia, Atleta


def calcular_classe_por_idade(idade):
    """
    Calcula a classe do atleta baseado na idade
    Regras:
    - SUB 9: até 9 anos
    - SUB 11: 10-11 anos
    - SUB 13: 12-13 anos
    - SUB 15: 14-15 anos
    - SUB 18: 16-17 anos
    - SUB 21: 18-20 anos
    - Sênior: 21+ anos
    """
    if idade <= 9:
        return 'SUB 9'
    elif idade <= 11:
        return 'SUB 11'
    elif idade <= 13:
        return 'SUB 13'
    elif idade <= 15:
        return 'SUB 15'
    elif idade <= 17:
        return 'SUB 18'
    elif idade <= 20:
        return 'SUB 21'
    else:
        return 'Sênior'


class Evento(models.Model):
    """Modelo para representar um evento de judô"""
    STATUS_CHOICES = [
        ('RASCUNHO', 'Rascunho'),
        ('INSCRICOES', 'Inscrições Abertas'),
        ('PESAGEM', 'Pesagem'),
        ('ANDAMENTO', 'Em andamento'),
        ('ENCERRADO', 'Encerrado'),
    ]
    
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    local = models.CharField(max_length=150)
    data_evento = models.DateField()
    data_limite_inscricao = models.DateField()
    ativo = models.BooleanField(default=True)
    
    # Valores diferentes para federados / não federados
    valor_federado = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Valor Inscrição Federado (R$)")
    valor_nao_federado = models.DecimalField(max_digits=6, decimal_places=2, default=0.00, verbose_name="Valor Inscrição Não Federado (R$)")
    
    # Parâmetros baseados em evento anterior (JSON)
    parametros = models.JSONField(default=dict, blank=True)
    
    # Campos adicionais (compatibilidade)
    cidade = models.CharField(max_length=120, blank=True, default='')
    regulamento = models.FileField(upload_to='regulamentos/', null=True, blank=True)
    parametros_baseado_em = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_baseados',
        verbose_name='Parâmetros baseados em'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    pesagem_encerrada = models.BooleanField(default=False, verbose_name="Pesagem Encerrada")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='RASCUNHO', verbose_name="Status do Evento")
    
    # Regras do evento
    aceita_nao_federado = models.BooleanField(default=True, verbose_name="Aceita Não Federados?")
    aceita_remanejamento = models.BooleanField(default=True, verbose_name="Aceita Remanejamento?")

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ['-data_evento']

    def __str__(self):
        return f"{self.nome} - {self.data_evento}"

    @property
    def inscricoes_abertas(self):
        """Verifica se as inscrições estão abertas"""
        hoje = timezone.now().date()
        return hoje <= self.data_limite_inscricao
    
    @property
    def is_expired(self):
        """✅ NOVO: Verifica se o evento já foi realizado (data passou)"""
        if not self.data_evento:
            return False
        return timezone.now().date() > self.data_evento
    
    @property
    def pesagem_liberada(self):
        """✅ NOVO: Verifica se a pesagem ainda está liberada (até o dia do evento)"""
        if not self.data_evento:
            return True
        hoje = timezone.now().date()
        return hoje <= self.data_evento

    @property
    def total_inscritos(self):
        """Retorna o total de atletas inscritos"""
        return self.evento_atletas.count()
    
    @property
    def inscricoes(self):
        """Alias para evento_atletas (compatibilidade)"""
        return self.evento_atletas


class EventoParametro(models.Model):
    """Parâmetros e regras específicas de um evento"""
    evento = models.OneToOneField(
        Evento,
        on_delete=models.CASCADE,
        related_name='parametros_config'  # ✅ Renomeado para evitar conflito com campo JSON
    )
    idade_min = models.IntegerField(default=0, verbose_name="Idade Mínima")
    idade_max = models.IntegerField(default=99, verbose_name="Idade Máxima")
    usar_pesagem = models.BooleanField(default=True, verbose_name="Usar Pesagem")
    usar_chaves_automaticas = models.BooleanField(default=True, verbose_name="Gerar Chaves Automaticamente")
    permitir_festival = models.BooleanField(default=False, verbose_name="Permitir Festival (3-6 anos)")
    pontuacao_primeiro = models.IntegerField(default=10, verbose_name="Pontuação 1º Lugar")
    pontuacao_segundo = models.IntegerField(default=7, verbose_name="Pontuação 2º Lugar")
    pontuacao_terceiro = models.IntegerField(default=5, verbose_name="Pontuação 3º Lugar")
    penalidade_remanejamento = models.IntegerField(default=1, verbose_name="Penalidade por Remanejamento (pontos)")

    class Meta:
        verbose_name = "Parâmetro do Evento"
        verbose_name_plural = "Parâmetros dos Eventos"

    def __str__(self):
        return f"Parâmetros de {self.evento.nome}"

    @classmethod
    def copiar_de_evento(cls, evento_origem, evento_destino):
        """Copia parâmetros de um evento para outro"""
        if evento_origem.parametros_config.exists():
            params_origem = evento_origem.parametros_config.first()
            return cls.objects.create(
                evento=evento_destino,
                idade_min=params_origem.idade_min,
                idade_max=params_origem.idade_max,
                usar_pesagem=params_origem.usar_pesagem,
                usar_chaves_automaticas=params_origem.usar_chaves_automaticas,
                permitir_festival=params_origem.permitir_festival,
                pontuacao_primeiro=params_origem.pontuacao_primeiro,
                pontuacao_segundo=params_origem.pontuacao_segundo,
                pontuacao_terceiro=params_origem.pontuacao_terceiro,
                penalidade_remanejamento=params_origem.penalidade_remanejamento,
            )
        return None


class EventoAtleta(models.Model):
    """
    Vínculo entre Evento e Atleta.
    Este modelo armazena dados específicos da competição.
    O modelo Atleta permanece intacto (permanente).
    """
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('ELIMINADO_PESO', 'Eliminado por peso'),
        ('ELIMINADO_IND', 'Eliminado por indisciplina'),
    ]
    
    evento = models.ForeignKey(
        Evento,
        on_delete=models.CASCADE,
        related_name='evento_atletas'
    )
    atleta = models.ForeignKey(
        Atleta,
        on_delete=models.CASCADE,
        related_name='evento_atletas'
    )
    academia = models.ForeignKey(
        Academia,
        on_delete=models.CASCADE,
        related_name='evento_atletas'
    )
    inscrito_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evento_atletas_inscritos'
    )
    data_inscricao = models.DateTimeField(auto_now_add=True)
    observacao = models.TextField(blank=True)
    
    # Dados de federação na inscrição
    federado = models.BooleanField(default=False, verbose_name="É Federado?")
    zempo = models.CharField(max_length=15, blank=True, null=True, verbose_name="Número ZEMPO")

    # Dados congelados para o evento (não mudam após inscrição)
    classe = models.CharField(max_length=20, blank=True, verbose_name="Classe no Evento")
    categoria_inicial = models.ForeignKey(
        'atletas.Categoria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inscricoes_iniciais',
        verbose_name="Categoria Inicial"
    )
    categoria_final = models.ForeignKey(
        'atletas.Categoria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inscricoes_finais',
        verbose_name="Categoria Final"
    )
    
    # Pesos
    peso_previsto = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Peso Previsto (kg)")
    peso_oficial = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Peso Oficial (kg)")
    
    # Status e remanejamento
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='OK',
        verbose_name="Status no Evento"
    )
    remanejado = models.BooleanField(default=False, verbose_name="Foi Remanejado?")
    motivo = models.TextField(blank=True, verbose_name="Motivo")
    
    # Pontos conquistados neste evento
    pontos = models.IntegerField(default=0, verbose_name="Pontos no Evento")
    pontos_evento = models.IntegerField(default=0, verbose_name="Pontos no Evento (alias)")  # Alias para compatibilidade
    
    # Valor da inscrição
    valor_inscricao = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name="Valor da Inscrição (R$)")
    
    # Campos de compatibilidade (manter por enquanto)
    categoria = models.ForeignKey(
        'atletas.Categoria',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='evento_atletas',
        verbose_name="Categoria no Evento (compatibilidade)"
    )
    categoria_ajustada = models.CharField(max_length=100, blank=True, verbose_name="Categoria Ajustada (nome)")
    status_pesagem = models.CharField(
        max_length=20,
        choices=[
            ('PENDENTE', 'Pendente'),
            ('OK', 'OK'),
            ('REMANEJADO', 'Remanejado'),
            ('DESC', 'Desclassificado'),
        ],
        default='PENDENTE',
        verbose_name="Status da Pesagem (compatibilidade)"
    )
    desclassificado = models.BooleanField(default=False, verbose_name="Foi Desclassificado? (compatibilidade)")

    class Meta:
        verbose_name = "Atleta no Evento"
        verbose_name_plural = "Atletas nos Eventos"
        unique_together = ['evento', 'atleta']  # Um atleta só pode se inscrever uma vez por evento
        ordering = ['-data_inscricao']

    def __str__(self):
        return f"{self.atleta.nome} - {self.evento.nome}"

    def save(self, *args, **kwargs):
        """Override save para sincronizar campos"""
        # Sincronizar pontos e pontos_evento
        if self.pontos != self.pontos_evento:
            self.pontos_evento = self.pontos
        
        # Sincronizar categoria_final e categoria (compatibilidade)
        if self.categoria_final and not self.categoria:
            self.categoria = self.categoria_final
        
        # Sincronizar status e status_pesagem (compatibilidade)
        if self.status == 'ELIMINADO_PESO':
            self.status_pesagem = 'DESC'
            self.desclassificado = True
        elif self.status == 'OK':
            if self.remanejado:
                self.status_pesagem = 'REMANEJADO'
            else:
                self.status_pesagem = 'OK'
            self.desclassificado = False
        
        # Sincronizar categoria_final com categoria_ajustada (compatibilidade)
        if self.categoria_final and not self.categoria_ajustada:
            self.categoria_ajustada = self.categoria_final.categoria_nome
        
        super().save(*args, **kwargs)
