from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from datetime import date, timedelta
from django.utils import timezone
from django.utils.text import slugify


def documento_upload_path(instance, filename):
    """Define o caminho de upload do documento do atleta"""
    # Se o atleta já tem ID, usar ele; caso contrário, usar 'temp' e depois mover
    if hasattr(instance, 'id') and instance.id:
        return f'documentos/atletas/{instance.id}/{filename}'
    else:
        # Para uploads temporários antes de salvar (será movido após save)
        import uuid
        return f'documentos/temp/{uuid.uuid4()}_{filename}'


def foto_perfil_atleta_upload_path(instance, filename):
    """Define o caminho de upload da foto de perfil do atleta"""
    if hasattr(instance, 'id') and instance.id:
        return f'fotos/atletas/{instance.id}/{filename}'
    else:
        import uuid
        return f'fotos/temp/{uuid.uuid4()}_{filename}'


def foto_perfil_academia_upload_path(instance, filename):
    """Define o caminho de upload da foto de perfil da academia"""
    if hasattr(instance, 'id') and instance.id:
        return f'fotos/academias/{instance.id}/{filename}'
    else:
        import uuid
        return f'fotos/temp/{uuid.uuid4()}_{filename}'


def logo_organizador_upload_path(instance, filename):
    """Define o caminho de upload do logo do organizador"""
    if hasattr(instance, 'id') and instance.id:
        return f'organizadores/logos/{instance.id}/{filename}'
    else:
        import uuid
        return f'organizadores/temp/{uuid.uuid4()}_{filename}'


class Organizador(models.Model):
    """Organizador de eventos - Multi-tenant principal"""
    nome = models.CharField(max_length=255, verbose_name="Nome do Organizador")
    email = models.EmailField(verbose_name="E-mail", blank=True, null=True)
    telefone = models.CharField(max_length=30, blank=True, verbose_name="Telefone")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizadores_dono",
        verbose_name="Dono (superuser)"
    )
    logo = models.ImageField(
        upload_to=logo_organizador_upload_path,
        blank=True,
        null=True,
        verbose_name="Logo",
        help_text="Logo do organizador (JPG, PNG)"
    )
    slug = models.SlugField(
        max_length=80,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Slug",
        help_text="Identificador único usado nas URLs."
    )
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        verbose_name = "Organizador"
        verbose_name_plural = "Organizadores"
        ordering = ['nome']

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        # Gera slug automaticamente se não estiver preenchido
        if not self.slug and self.nome:
            base_slug = slugify(self.nome)[:60] or "organizacao"  # reserva caracteres para sufixo
            slug_candidate = base_slug
            counter = 1
            while Organizador.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug[:50]}-{counter}"
                counter += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)


class Academia(models.Model):
    organizador = models.ForeignKey(Organizador, on_delete=models.CASCADE, related_name='academias', verbose_name="Organização", null=True, blank=True)
    nome = models.CharField(max_length=200)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    telefone = models.CharField(max_length=20, blank=True, help_text="Telefone de contato da academia")
    responsavel = models.CharField(max_length=200, blank=True, verbose_name="Responsável", help_text="Nome do responsável pela academia")
    endereco = models.CharField(max_length=300, blank=True, verbose_name="Endereço", help_text="Endereço da academia (opcional)")
    pontos = models.IntegerField(default=0)
    foto_perfil = models.ImageField(
        upload_to=foto_perfil_academia_upload_path,
        blank=True,
        null=True,
        verbose_name="Foto de Perfil",
        help_text="Foto de perfil da academia (JPG, PNG)"
    )
    
    # Campos de autenticação para Login de Academia (DEPRECADOS - mantidos para compatibilidade)
    # Login e senha agora são gerados apenas por evento via AcademiaCampeonatoSenha
    login = models.CharField(max_length=100, blank=True, null=True, unique=True, help_text="[DEPRECADO] Login da academia - não usar mais")
    senha_login = models.CharField(max_length=128, blank=True, help_text="[DEPRECADO] Senha para login - não usar mais")
    ativo_login = models.BooleanField(default=True, help_text="Permite login da academia")
    
    # Bônus do professor
    bonus_percentual = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Bônus Percentual (%)", help_text="Percentual de bônus sobre inscrições confirmadas")
    bonus_fixo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Bônus Fixo por Atleta", help_text="Valor fixo de bônus por atleta confirmado")

    class Meta:
        verbose_name = "Academia"
        verbose_name_plural = "Academias"
        ordering = ['nome']

    def __str__(self):
        return self.nome
    
    def verificar_senha(self, senha):
        """Verifica se a senha fornecida corresponde à senha da academia"""
        import hashlib
        if not self.senha_login:
            return False
        # Hash simples (em produção, usar bcrypt ou similar)
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        return self.senha_login == senha_hash
    
    def definir_senha(self, senha):
        """Define a senha da academia (com hash)"""
        import hashlib
        self.senha_login = hashlib.sha256(senha.encode()).hexdigest()


class Classe(models.Model):
    """Classe de idade dos atletas (FESTIVAL, SUB 9, SUB 11, etc.)"""
    nome = models.CharField(max_length=20, unique=True, verbose_name="Nome da Classe")
    idade_min = models.PositiveIntegerField(verbose_name="Idade Mínima")
    idade_max = models.PositiveIntegerField(verbose_name="Idade Máxima")

    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ["idade_min"]

    def __str__(self):
        return self.nome


class Categoria(models.Model):
    """Categoria de peso por classe e sexo"""
    classe = models.ForeignKey(Classe, on_delete=models.CASCADE, related_name="categorias", verbose_name="Classe")
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')], verbose_name="Sexo")
    categoria_nome = models.CharField(max_length=50, verbose_name="Nome da Categoria")  # Meio Leve, Pesado…
    limite_min = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Limite Mínimo (kg)")
    limite_max = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="Limite Máximo (kg)")
    label = models.CharField(max_length=80, verbose_name="Label")  # Ex: "SUB 11 - Meio Leve -42kg"

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["classe__idade_min", "sexo", "limite_min"]

    def __str__(self):
        return self.label


class Atleta(models.Model):
    """Cadastro global permanente do atleta (não vinculado a evento)"""
    # Campos básicos obrigatórios
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    # Mantém ano_nasc temporariamente para compatibilidade, adiciona data_nascimento depois
    ano_nasc = models.IntegerField(null=True, blank=True, verbose_name="Ano de Nascimento")  # Temporário para migração
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')], verbose_name="Gênero")
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='atletas', verbose_name="Academia")
    classe_inicial = models.CharField(max_length=20, blank=True, verbose_name="Classe Inicial", help_text="Classe base do atleta (calculada automaticamente)")
    
    # Documento oficial (obrigatório para inscrição)
    documento_oficial = models.FileField(
        upload_to=documento_upload_path,
        blank=True,
        null=True,
        verbose_name="Documento Oficial",
        help_text="Upload de documento de identidade (JPG, PNG ou PDF)"
    )
    
    # Foto de perfil
    foto_perfil = models.ImageField(
        upload_to=foto_perfil_atleta_upload_path,
        blank=True,
        null=True,
        verbose_name="Foto de Perfil",
        help_text="Foto de perfil do atleta (JPG, PNG)"
    )
    
    # Status
    status_ativo = models.BooleanField(default=True, verbose_name="Ativo", help_text="Atleta ativo no sistema")
    
    # Campos adicionais (opcionais)
    FAIXA_CHOICES = [
        ('BRANCA', 'Branca'),
        ('P.CINZA', 'P. Cinza'),
        ('CINZA', 'Cinza'),
        ('P.AZUL', 'P. Azul'),
        ('AZUL', 'Azul'),
        ('P.AMARELA', 'P. Amarela'),
        ('AMARELA', 'Amarela'),
        ('P.LARANJA', 'P. Laranja'),
        ('LARANJA', 'Laranja'),
        ('VERDE', 'Verde'),
        ('ROXA', 'Roxa'),
        ('MARRON', 'Marrom'),
        ('PRETA', 'Preta'),
    ]
    faixa = models.CharField(
        max_length=20,
        choices=FAIXA_CHOICES,
        blank=True,
        null=True,
        verbose_name="Faixa",
        help_text="Graduação do atleta"
    )
    federado = models.BooleanField(default=False, verbose_name="Federado")
    numero_zempo = models.CharField(max_length=50, blank=True, null=True, verbose_name="Número Zempo", help_text="Número Zempo (obrigatório para atletas federados)")
    
    # Campos para Equipe Técnica
    pode_ser_equipe_tecnica = models.BooleanField(default=False, verbose_name="Pode Fazer Parte da Equipe Técnica", help_text="Permite que esta pessoa seja selecionada para compor a equipe técnica em eventos")
    funcao_equipe_tecnica = models.CharField(max_length=100, blank=True, null=True, verbose_name="Função/Cargo na Equipe Técnica", help_text="Função padrão na equipe técnica (ex: Árbitro, Mesário, Coordenador)")
    chave_pix = models.CharField(max_length=200, blank=True, null=True, verbose_name="Chave PIX", help_text="Chave PIX para pagamento (obrigatório para equipe técnica)")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone", help_text="Telefone de contato")
    
    # Campos de auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Data de Atualização")

    class Meta:
        verbose_name = "Atleta"
        verbose_name_plural = "Atletas"
        ordering = ['nome']

    @property
    def idade(self):
        """Calcula a idade do atleta"""
        if not self.data_nascimento:
            return None
        hoje = date.today()
        return hoje.year - self.data_nascimento.year - ((hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day))
    
    def get_ano_nasc(self):
        """Retorna o ano de nascimento (para compatibilidade)"""
        if self.data_nascimento:
            return self.data_nascimento.year
        return self.ano_nasc  # Fallback para dados antigos
    
    def tem_documento(self):
        """Verifica se o atleta tem documento oficial cadastrado"""
        return bool(self.documento_oficial)
    
    def get_classe_atual(self):
        """Calcula a classe atual baseada na data de nascimento"""
        try:
            from .utils import calcular_classe
            ano = self.get_ano_nasc()
            if ano:
                classe = calcular_classe(ano)
                if classe:
                    return classe
            # Fallback para classe_inicial ou padrão
            if self.classe_inicial:
                return self.classe_inicial
            return "SÊNIOR"  # Padrão se não houver dados
        except Exception as e:
            # Em caso de erro, retornar classe_inicial ou padrão
            if self.classe_inicial:
                return self.classe_inicial
            return "SÊNIOR"  # Padrão se não houver dados

    def __str__(self):
        return f"{self.nome} ({self.academia.nome})"


class Chave(models.Model):
    campeonato = models.ForeignKey('Campeonato', on_delete=models.CASCADE, related_name='chaves', verbose_name="Campeonato", null=True, blank=True, help_text="Campeonato ao qual esta chave pertence")
    classe = models.CharField(max_length=20)
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    categoria = models.CharField(max_length=100)
    atletas = models.ManyToManyField(Atleta, related_name='chaves')
    estrutura = models.JSONField(default=dict)  # Estrutura da chave (árvore de lutas)

    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"
        ordering = ['-campeonato__data_competicao', 'classe', 'sexo', 'categoria']

    def __str__(self):
        campeonato_nome = f" - {self.campeonato.nome}" if self.campeonato else ""
        return f"{self.classe} - {self.get_sexo_display()} - {self.categoria}{campeonato_nome}"


class Luta(models.Model):
    TIPO_VITORIA_CHOICES = [
        ("IPPON", "Ippon"),
        ("WAZARI", "Wazari"),
        ("WAZARI_WAZARI", "Wazari-Wazari"),
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


class FormaPagamento(models.Model):
    """Formas de pagamento disponíveis no sistema"""
    TIPO_CHOICES = [
        ('PIX', 'PIX'),
        ('DINHEIRO', 'Dinheiro'),
        ('CARTAO', 'Cartão'),
        ('TRANSFERENCIA', 'Transferência Bancária'),
    ]
    
    nome = models.CharField(max_length=100, verbose_name="Nome")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, verbose_name="Tipo")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Forma de Pagamento"
        verbose_name_plural = "Formas de Pagamento"
        ordering = ['tipo', 'nome']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nome}"


class Campeonato(models.Model):
    organizador = models.ForeignKey(Organizador, on_delete=models.CASCADE, related_name='campeonatos', verbose_name="Organizador", null=True, blank=True)
    nome = models.CharField(max_length=200, default="Campeonato Padrão")
    data_inicio = models.DateField(null=True, blank=True, help_text="Data de início das inscrições")
    data_competicao = models.DateField(null=True, blank=True, help_text="Data da competição")
    data_limite_inscricao = models.DateField(null=True, blank=True, help_text="Data limite para inscrições")
    data_limite_inscricao_academia = models.DateField(null=True, blank=True, verbose_name="Data Limite para Inscrições por Academia", help_text="Após esta data, academias não poderão mais inscrever ou editar atletas. Apenas a equipe operacional poderá fazer inscrições.")
    ativo = models.BooleanField(default=False, help_text="Apenas um campeonato pode estar ativo por vez")
    regulamento = models.TextField(blank=True, help_text="Regulamento do campeonato")
    valor_inscricao_federado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Valor da inscrição para atletas federados")
    valor_inscricao_nao_federado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Valor da inscrição para atletas não federados")
    
    # Campos de pagamento
    chave_pix = models.CharField(max_length=200, blank=True, verbose_name="Chave PIX", help_text="Chave PIX para pagamento (CPF, CNPJ, Email, Telefone ou Chave Aleatória)")
    titular_pix = models.CharField(max_length=200, blank=True, verbose_name="Titular da Chave PIX", help_text="Nome do titular da conta PIX")
    formas_pagamento = models.ManyToManyField('FormaPagamento', blank=True, verbose_name="Formas de Pagamento Aceitas", help_text="Selecione as formas de pagamento aceitas para este evento")

    class Meta:
        verbose_name = "Campeonato"
        verbose_name_plural = "Campeonatos"
        ordering = ['-data_inicio', 'nome']

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        """Garante que apenas um campeonato pode estar ativo por vez"""
        # Se este campeonato está sendo ativado, desativar TODOS os outros primeiro
        if self.ativo:
            # Desativar todos, incluindo este (se já existir) para garantir limpeza
            Campeonato.objects.all().update(ativo=False)
            # Depois salvar este como ativo
        super().save(*args, **kwargs)
        # Garantir novamente após salvar (caso o save não tenha funcionado corretamente)
        if self.ativo:
            Campeonato.objects.exclude(id=self.id).update(ativo=False)
    
    def clean(self):
        """Validação adicional"""
        from django.core.exceptions import ValidationError
        from django.utils import timezone
        
        # Validar datas
        hoje = timezone.now().date()
        
        if self.data_inicio and self.data_limite_inscricao:
            if self.data_limite_inscricao < self.data_inicio:
                raise ValidationError('A data limite de inscrição não pode ser anterior à data de início.')
        
        if self.data_limite_inscricao_academia and self.data_limite_inscricao:
            if self.data_limite_inscricao_academia > self.data_limite_inscricao:
                raise ValidationError('A data limite para inscrições por academia não pode ser posterior à data limite geral de inscrições.')
        
        if self.data_competicao and self.data_limite_inscricao:
            if self.data_competicao < self.data_limite_inscricao:
                raise ValidationError('A data da competição não pode ser anterior à data limite de inscrições.')
    
    @property
    def permite_inscricao_academia(self):
        """Verifica se ainda permite inscrições por academia"""
        from django.utils import timezone
        hoje = timezone.now().date()
        
        if not self.ativo:
            return False
        
        if self.data_limite_inscricao_academia:
            return hoje <= self.data_limite_inscricao_academia
        
        if self.data_limite_inscricao:
            return hoje <= self.data_limite_inscricao
        
        return True
    
    @property
    def permite_cadastro_atleta(self):
        """Verifica se ainda permite cadastro de novos atletas"""
        return self.permite_inscricao_academia


class Inscricao(models.Model):
    """Inscrição de um atleta em um campeonato específico"""
    STATUS_CHOICES = [
        ('pendente_pesagem', 'Pendente de Pesagem'),
        ('ok', 'OK'),
        ('remanejado', 'Remanejado'),
        ('desclassificado', 'Desclassificado'),
        # Compatibilidade
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]

    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='inscricoes', verbose_name="Atleta")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='inscricoes', verbose_name="Campeonato")
    
    # Classe e categoria calculadas/escolhidas na inscrição (legado)
    classe_escolhida = models.CharField(max_length=20, verbose_name="Classe Escolhida")
    categoria_calculada = models.CharField(max_length=100, verbose_name="Categoria Calculada", blank=True)
    categoria_escolhida = models.CharField(max_length=100, verbose_name="Categoria Escolhida", blank=True)

    # Campos novos normalizados (FK / Decimal / status)
    classe_real = models.ForeignKey(
        Classe,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inscricoes_classe_real",
        verbose_name="Classe Real"
    )
    categoria_real = models.ForeignKey(
        Categoria,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="inscricoes_categoria_real",
        verbose_name="Categoria Real"
    )
    peso_real = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Peso Real (kg)"
    )
    STATUS_ATUAL_CHOICES = [
        ('pendente', 'Pendente'),
        ('inscrito', 'Inscrito'),
        ('aprovado', 'Aprovado'),
        ('remanejado', 'Remanejado'),
        ('desclassificado', 'Desclassificado'),
    ]
    status_atual = models.CharField(
        max_length=20,
        choices=STATUS_ATUAL_CHOICES,
        default='pendente',
        verbose_name="Status Atual",
        db_index=True
    )
    
    # Peso informado na inscrição
    peso_informado = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name="Peso Informado (kg)")
    
    # Dados da pesagem (preenchidos após pesagem)
    peso = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True, verbose_name="Peso Oficial (kg)")
    categoria_ajustada = models.CharField(max_length=100, blank=True, verbose_name="Categoria Ajustada")
    motivo_ajuste = models.TextField(blank=True, verbose_name="Motivo do Ajuste")
    remanejado = models.BooleanField(default=False, verbose_name="Remanejado")
    bloqueado_chave = models.BooleanField(default=False, verbose_name="Bloqueado para chaveamento")
    
    # Status da inscrição (legado)
    status_inscricao = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente_pesagem',
        verbose_name="Status da Inscrição"
    )
    
    # Datas
    data_inscricao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Inscrição")
    data_pesagem = models.DateTimeField(null=True, blank=True, verbose_name="Data da Pesagem")

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"
        # Permite múltiplas inscrições do mesmo atleta no mesmo campeonato, mas não na mesma classe/categoria
        unique_together = ('atleta', 'campeonato', 'classe_escolhida', 'categoria_escolhida')
        ordering = ['-data_inscricao']

    def __str__(self):
        return f"{self.atleta.nome} - {self.campeonato.nome} ({self.classe_escolhida})"
    
    def pode_gerar_chave(self):
        """Verifica se a inscrição está apta para gerar chave"""
        return self.status_inscricao in ['ok', 'remanejado', 'aprovado'] and not self.bloqueado_chave and self.peso is not None

    def eh_apto_chave(self):
        return self.pode_gerar_chave()

    def eh_desclassificado(self):
        return self.status_inscricao == 'desclassificado' or self.bloqueado_chave


class PesagemHistorico(models.Model):
    """Histórico de pesagens por evento - registra todas as pesagens realizadas"""
    inscricao = models.ForeignKey(Inscricao, on_delete=models.CASCADE, related_name='historico_pesagens', verbose_name="Inscrição")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='pesagens_historico', verbose_name="Campeonato")
    peso_registrado = models.DecimalField(max_digits=6, decimal_places=1, verbose_name="Peso Registrado (kg)")
    categoria_ajustada = models.CharField(max_length=100, blank=True, verbose_name="Categoria Ajustada")
    motivo_ajuste = models.TextField(blank=True, verbose_name="Motivo do Ajuste")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    pesado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='pesagens_realizadas', verbose_name="Pesado por")
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora da Pesagem")
    
    class Meta:
        verbose_name = "Histórico de Pesagem"
        verbose_name_plural = "Históricos de Pesagem"
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['campeonato', '-data_hora']),
            models.Index(fields=['inscricao', '-data_hora']),
        ]
    
    def __str__(self):
        return f"{self.inscricao.atleta.nome} - {self.peso_registrado}kg - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class OcorrenciaAtleta(models.Model):
    """Ocorrências automáticas em pesagem/remanejamento/desclassificação"""
    TIPO_CHOICES = [
        ('REMANEJAMENTO', 'Remanejamento'),
        ('DESCLASSIFICACAO', 'Desclassificação'),
    ]
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='ocorrencias_pesagem', verbose_name="Atleta")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='ocorrencias_pesagem', verbose_name="Campeonato")
    tipo = models.CharField(max_length=30, choices=TIPO_CHOICES, verbose_name="Tipo")
    motivo = models.CharField(max_length=255, blank=True, verbose_name="Motivo")
    detalhes_json = models.JSONField(default=dict, blank=True, verbose_name="Detalhes")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    
    class Meta:
        verbose_name = "Ocorrência de Atleta"
        verbose_name_plural = "Ocorrências de Atletas"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.atleta.nome} - {self.get_tipo_display()} - {self.campeonato.nome}"


class AcademiaCampeonato(models.Model):
    """Relação entre Academia e Campeonato com controle de permissão"""
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='vinculos_campeonatos', verbose_name="Academia")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='academias_vinculadas', verbose_name="Campeonato")
    permitido = models.BooleanField(default=True, verbose_name="Permitido no Campeonato", help_text="Se desmarcado, a academia não poderá participar deste campeonato")
    data_vinculacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Vinculação")
    
    class Meta:
        verbose_name = "Academia no Campeonato"
        verbose_name_plural = "Academias nos Campeonatos"
        unique_together = ('academia', 'campeonato')
        ordering = ['academia__nome']
    
    def __str__(self):
        status = "Permitida" if self.permitido else "Bloqueada"
        return f"{self.academia.nome} - {self.campeonato.nome} ({status})"


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


class Despesa(models.Model):
    """Despesas e Receitas do campeonato"""
    TIPO_CHOICES = [
        ('despesa', 'Despesa'),
        ('receita', 'Receita'),
    ]
    
    CATEGORIA_DESPESA_CHOICES = [
        ('arbitros', 'Árbitros'),
        ('mesarios', 'Mesários'),
        ('coordenadores', 'Coordenadores'),
        ('oficiais_pesagem', 'Oficiais de Pesagem'),
        ('oficiais_mesa', 'Oficiais de Mesa'),
        ('insumos', 'Insumos'),
        ('ambulancia', 'Ambulância'),
        ('estrutura', 'Estrutura'),
        ('limpeza', 'Limpeza'),
        ('outras', 'Outras'),
    ]
    
    CATEGORIA_RECEITA_CHOICES = [
        ('inscricoes', 'Inscrições'),
        ('venda_camisas', 'Venda de Camisas'),
        ('venda_ingressos', 'Venda de Ingressos'),
        ('venda_alimentos', 'Venda de Alimentos/Bebidas'),
        ('patrocinio', 'Patrocínio'),
        ('venda_equipamentos', 'Venda de Equipamentos'),
        ('outras_receitas', 'Outras Receitas'),
    ]
    
    STATUS_CHOICES = [
        ('pago', 'Pago/Recebido'),
        ('pendente', 'Pendente'),
    ]
    
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='despesas', verbose_name="Campeonato", null=False, blank=False)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='despesa', verbose_name="Tipo")
    categoria = models.CharField(max_length=50, verbose_name="Categoria")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    contato_nome = models.CharField(max_length=200, blank=True, verbose_name="Contato Responsável")
    contato_whatsapp = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp do Contato")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento/Recebimento")
    comprovante_pagamento = models.FileField(upload_to='comprovantes_pagamento/', null=True, blank=True, verbose_name="Comprovante de Pagamento")
    
    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ['-data_cadastro']
    
    def get_categoria_display(self):
        """Retorna o display da categoria baseado no tipo"""
        if self.tipo == 'despesa':
            return dict(self.CATEGORIA_DESPESA_CHOICES).get(self.categoria, self.categoria)
        else:
            return dict(self.CATEGORIA_RECEITA_CHOICES).get(self.categoria, self.categoria)
    
    def __str__(self):
        tipo_display = "Despesa" if self.tipo == 'despesa' else "Receita"
        return f"{tipo_display}: {self.nome} - {self.get_categoria_display()} - R$ {self.valor}"


class CategoriaInsumo(models.Model):
    """Categorias customizáveis de insumos e estrutura"""
    nome = models.CharField(max_length=100, unique=True, verbose_name="Nome da Categoria", help_text="Ex: Tatames, Aluguéis, Transportes, etc.")
    descricao = models.TextField(blank=True, verbose_name="Descrição", help_text="Descrição opcional da categoria")
    ativo = models.BooleanField(default=True, verbose_name="Ativo", help_text="Se desativado, não aparecerá nas opções")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    
    class Meta:
        verbose_name = "Categoria de Insumo"
        verbose_name_plural = "Categorias de Insumos"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class InsumoEstrutura(models.Model):
    """Insumos e estrutura do campeonato"""
    STATUS_CHOICES = [
        ('pago', 'Pago'),
        ('pendente', 'Pendente'),
    ]
    
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='insumos_estrutura', verbose_name="Campeonato")
    categoria = models.ForeignKey(CategoriaInsumo, on_delete=models.PROTECT, related_name='insumos', verbose_name="Categoria")
    nome = models.CharField(max_length=200, verbose_name="Nome do Item", help_text="Ex: Aluguel de tatames, Transporte de equipamentos, etc.")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor (R$)")
    quantidade = models.IntegerField(default=1, verbose_name="Quantidade", help_text="Quantidade de itens ou unidades")
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Unitário", help_text="Valor por unidade (calculado automaticamente)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status do Pagamento")
    fornecedor = models.CharField(max_length=200, blank=True, verbose_name="Fornecedor", help_text="Nome do fornecedor ou empresa")
    contato_nome = models.CharField(max_length=200, blank=True, verbose_name="Contato Responsável")
    contato_whatsapp = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp do Contato")
    observacao = models.TextField(blank=True, verbose_name="Observações", help_text="Observações adicionais sobre o insumo")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    
    class Meta:
        verbose_name = "Insumo/Estrutura"
        verbose_name_plural = "Insumos e Estrutura"
        ordering = ['-data_cadastro']
    
    def save(self, *args, **kwargs):
        """Calcula valor unitário automaticamente"""
        if self.valor and self.quantidade and self.quantidade > 0:
            self.valor_unitario = self.valor / self.quantidade
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nome} - {self.categoria.nome} - R$ {self.valor}"


class CadastroOperacional(models.Model):
    """Cadastros operacionais (árbitros, mesários, etc.)"""
    TIPO_CHOICES = [
        ('arbitro', 'Árbitro'),
        ('mesario', 'Mesário'),
        ('coordenador', 'Coordenador'),
        ('oficial_pesagem', 'Oficial de Pesagem'),
        ('oficial_mesa', 'Oficial de Mesa'),
        ('ambulancia', 'Ambulância'),
        ('patrocinador', 'Patrocinador'),
        ('insumo', 'Insumo'),
    ]
    
    organizador = models.ForeignKey(Organizador, on_delete=models.CASCADE, related_name='cadastros_operacionais', verbose_name="Organizador", null=True, blank=True)
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, verbose_name="Tipo")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Cadastro Operacional"
        verbose_name_plural = "Cadastros Operacionais"
        ordering = ['tipo', 'nome']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nome}"


class UserProfile(models.Model):
    """Perfil de usuário multi-tenant completo"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Organização (superior)
    organizador = models.ForeignKey(
        Organizador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )

    # NOVO CAMPO – ACADEMIA
    academia = models.ForeignKey(
        Academia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios_academia'
    )

    class Meta:
        verbose_name = "Perfil de Usuário"
        verbose_name_plural = "Perfis de Usuário"

    def __str__(self):
        texto = [self.user.username]
        if self.organizador:
            texto.append(f"Org: {self.organizador.nome}")
        if self.academia:
            texto.append(f"Acad: {self.academia.nome}")
        return " | ".join(texto)




class UsuarioOperacional(models.Model):
    """Perfil de usuário operacional com permissões e expiração"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_operacional', verbose_name="Usuário")
    pode_resetar_campeonato = models.BooleanField(default=False, verbose_name="Pode Resetar Campeonato", help_text="Permissão para resetar campeonato (apenas usuário principal)")
    pode_criar_usuarios = models.BooleanField(default=False, verbose_name="Pode Criar Usuários", help_text="Permissão para criar novos usuários operacionais (apenas usuário principal)")
    data_expiracao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Expiração", help_text="Data de expiração do acesso (null = vitalício)")
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios_criados', verbose_name="Criado Por")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    senha_alterada = models.BooleanField(default=False, verbose_name="Senha Alterada", help_text="Indica se o usuário já alterou a senha no primeiro acesso")
    
    class Meta:
        verbose_name = "Usuário Operacional"
        verbose_name_plural = "Usuários Operacionais"
        ordering = ['-data_criacao']
    
    def __str__(self):
        if not self.data_expiracao:
            return f"{self.user.username} - Vitalício"
        else:
            return f"{self.user.username} - Expira em {self.data_expiracao.strftime('%d/%m/%Y')}"
    
    @property
    def esta_expirado(self):
        """Verifica se o acesso está expirado"""
        if not self.data_expiracao:
            return False  # Vitalício
        return timezone.now() > self.data_expiracao
    
    @property
    def dias_restantes(self):
        """Retorna quantos dias restam até a expiração"""
        if not self.data_expiracao:
            return None  # Vitalício
        delta = self.data_expiracao - timezone.now()
        return max(0, delta.days)

    @property
    def organizacao(self):
        """Retorna a organização associada ao usuário operacional."""
        try:
            perfil = self.user.profile
            if perfil and perfil.organizador:
                return perfil.organizador
        except Exception:
            pass
        return None


class PessoaEquipeTecnica(models.Model):
    """Lista fixa de pessoas que podem fazer parte da equipe técnica (cadastradas uma única vez)"""
    # Pessoa pode ser um atleta cadastrado OU uma pessoa externa
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='pessoa_equipe_tecnica', verbose_name="Atleta", help_text="Selecione um atleta cadastrado (opcional)", null=True, blank=True)
    
    # Campos para pessoa externa (quando não é atleta)
    nome = models.CharField(max_length=200, blank=True, verbose_name="Nome Completo", help_text="Nome completo da pessoa (obrigatório se não for atleta)")
    telefone = models.CharField(max_length=20, blank=True, verbose_name="Telefone/WhatsApp", help_text="Telefone para contato e envio de convites")
    chave_pix = models.CharField(max_length=200, blank=True, verbose_name="Chave PIX", help_text="Chave PIX para pagamentos")
    
    observacao = models.TextField(blank=True, verbose_name="Observações", help_text="Observações gerais sobre esta pessoa")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    ativo = models.BooleanField(default=True, verbose_name="Ativo", help_text="Se desativado, não aparecerá nas opções")
    
    class Meta:
        verbose_name = "Pessoa da Equipe Técnica"
        verbose_name_plural = "Pessoas da Equipe Técnica"
        ordering = ['nome']
        unique_together = [
            ('atleta',),  # Atleta só pode aparecer uma vez
        ]
    
    def clean(self):
        """Validação: deve ter OU atleta OU nome preenchido"""
        from django.core.exceptions import ValidationError
        if not self.atleta and not self.nome:
            raise ValidationError('É necessário informar um atleta ou o nome da pessoa.')
        if self.atleta and self.nome:
            # Se é atleta, usar nome do atleta
            self.nome = self.atleta.nome
    
    def save(self, *args, **kwargs):
        """Atualiza nome automaticamente se for atleta"""
        if self.atleta:
            self.nome = self.atleta.nome
            # Se atleta tem telefone/PIX, usar deles se não preenchido
            if not self.telefone and self.atleta.telefone:
                self.telefone = self.atleta.telefone
            if not self.chave_pix and self.atleta.chave_pix:
                self.chave_pix = self.atleta.chave_pix
        super().save(*args, **kwargs)
    
    def __str__(self):
        if self.atleta:
            return f"{self.atleta.nome} (Atleta)"
        return f"{self.nome} (Externo)"
    
    @property
    def nome_completo(self):
        """Retorna o nome completo"""
        if self.atleta:
            return self.atleta.nome
        return self.nome
    
    @property
    def e_atleta(self):
        """Retorna True se é um atleta cadastrado"""
        return self.atleta is not None


class EquipeTecnicaCampeonato(models.Model):
    """Vínculo de pessoas da lista fixa à equipe técnica de um campeonato específico"""
    FUNCAO_CHOICES = [
        ('arbitro', 'Árbitro'),
        ('mesario', 'Mesário'),
        ('coordenador', 'Coordenador'),
        ('oficial_pesagem', 'Oficial de Pesagem'),
        ('oficial_mesa', 'Oficial de Mesa'),
        ('outro', 'Outro'),
    ]
    
    pessoa = models.ForeignKey(PessoaEquipeTecnica, on_delete=models.CASCADE, related_name='vinculos_campeonatos', verbose_name="Pessoa", help_text="Pessoa da lista fixa de equipe técnica", null=True, blank=True)
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='equipe_tecnica', verbose_name="Campeonato")
    funcao = models.CharField(max_length=50, choices=FUNCAO_CHOICES, verbose_name="Função no Evento", help_text="Função específica neste campeonato")
    funcao_customizada = models.CharField(max_length=100, blank=True, null=True, verbose_name="Função Customizada", help_text="Se 'Outro', especifique a função")
    pro_labore = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Pró-Labore", help_text="Valor do pró-labore/salário para esta função (será contabilizado como despesa)")
    despesa_gerada = models.ForeignKey('Despesa', on_delete=models.SET_NULL, null=True, blank=True, related_name='equipe_tecnica_origem', verbose_name="Despesa Gerada", help_text="Despesa gerada automaticamente a partir do pró-labore")
    
    observacao = models.TextField(blank=True, verbose_name="Observação", help_text="Observações sobre a participação desta pessoa na equipe técnica deste evento")
    data_vinculacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Vinculação")
    ativo = models.BooleanField(default=True, verbose_name="Ativo", help_text="Se desativado, a pessoa não faz parte da equipe técnica deste evento")
    
    class Meta:
        verbose_name = "Membro da Equipe Técnica no Campeonato"
        verbose_name_plural = "Equipe Técnica nos Campeonatos"
        ordering = ['campeonato', 'funcao', 'pessoa__nome']
        unique_together = [
            ('pessoa', 'campeonato', 'funcao'),  # Mesma pessoa não pode ter mesma função duas vezes no mesmo campeonato
        ]
    
    def __str__(self):
        funcao_display = self.funcao_customizada if self.funcao == 'outro' and self.funcao_customizada else self.get_funcao_display()
        return f"{self.pessoa.nome_completo} - {self.campeonato.nome} ({funcao_display})"
    
    @property
    def nome_completo(self):
        """Retorna o nome completo da pessoa"""
        return self.pessoa.nome_completo
    
    @property
    def telefone(self):
        """Retorna o telefone da pessoa"""
        return self.pessoa.telefone or ""
    
    @property
    def chave_pix(self):
        """Retorna a chave PIX da pessoa"""
        return self.pessoa.chave_pix or ""
    
    @property
    def documento(self):
        """Retorna o documento da pessoa (se disponível)"""
        if self.atleta.documento_oficial:
            return "Documento cadastrado"
        return "Sem documento"
    
    @property
    def telefone_contato(self):
        """Retorna o telefone da pessoa"""
        return self.atleta.telefone or "Não informado"
    
    @property
    def chave_pix_pagamento(self):
        """Retorna a chave PIX da pessoa"""
        return self.atleta.chave_pix or "Não informado"


class AcademiaCampeonatoSenha(models.Model):
    """Credenciais temporárias por campeonato para cada academia"""
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='senhas_campeonatos', verbose_name="Academia")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='senhas_academias', verbose_name="Campeonato")
    login = models.CharField(max_length=50, null=True, blank=True, verbose_name="Login Temporário", help_text="Login gerado automaticamente (ex: ACADEMIA_045)")
    senha = models.CharField(max_length=128, verbose_name="Senha (criptografada)")
    senha_plana = models.CharField(max_length=20, verbose_name="Senha Plana", help_text="Senha em texto plano (apenas para exibição inicial)")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    data_expiracao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Expiração", help_text="Data de expiração do acesso (5 dias após término do campeonato)")
    enviado_whatsapp = models.BooleanField(default=False, verbose_name="Enviado por WhatsApp")
    data_envio_whatsapp = models.DateTimeField(null=True, blank=True, verbose_name="Data de Envio WhatsApp")
    
    class Meta:
        verbose_name = "Senha de Academia por Campeonato"
        verbose_name_plural = "Senhas de Academias por Campeonato"
        unique_together = ['academia', 'campeonato']
        ordering = ['-data_criacao']
    
    def __str__(self):
        return f"{self.academia.nome} - {self.campeonato.nome}"
    
    def verificar_senha(self, senha):
        """Verifica se a senha fornecida corresponde à senha do campeonato"""
        import hashlib
        senha_hash = hashlib.sha256(senha.encode()).hexdigest()
        return self.senha == senha_hash
    
    def definir_senha(self, senha):
        """Define a senha do campeonato (com hash)"""
        import hashlib
        self.senha = hashlib.sha256(senha.encode()).hexdigest()
        self.senha_plana = senha  # Armazenar em texto plano temporariamente
    
    @property
    def esta_expirado(self):
        """Verifica se o acesso está expirado"""
        if not self.data_expiracao:
            return False  # Vitalício
        return timezone.now() > self.data_expiracao
    
    @property
    def dias_restantes(self):
        """Retorna quantos dias restam até a expiração"""
        if not self.data_expiracao:
            return None  # Vitalício
        delta = self.data_expiracao - timezone.now()
        return max(0, delta.days)

class Pagamento(models.Model):
    """Comprovantes de pagamento enviados pelas academias"""
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente Pagamento'),
        ('AGUARDANDO', 'Aguardando Validação'),
        ('VALIDADO', 'Validado'),
        ('REJEITADO', 'Rejeitado'),
    ]
    
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='pagamentos', verbose_name="Academia")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='pagamentos', verbose_name="Campeonato")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    comprovante = models.FileField(
        upload_to='comprovantes/%Y/%m/',
        verbose_name="Comprovante",
        help_text="Comprovante de pagamento (JPG, PNG, PDF ou HEIC)"
    )
    data_envio = models.DateTimeField(auto_now_add=True, verbose_name="Data de Envio")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name="Status"
    )
    motivo_rejeicao = models.TextField(blank=True, verbose_name="Motivo da Rejeição", help_text="Motivo da rejeição do pagamento (preenchido pelo operador)")
    validado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagamentos_validados',
        verbose_name="Validado por"
    )
    data_validacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Validação")
    
    class Meta:
        verbose_name = "Pagamento"
        verbose_name_plural = "Pagamentos"
        ordering = ['-data_envio']
        unique_together = ('academia', 'campeonato')
    
    def __str__(self):
        return f"{self.academia.nome} - {self.campeonato.nome} - R$ {self.valor_total}"


class ConferenciaPagamento(models.Model):
    """Modelo unificado para controle de pagamento por academia por evento"""
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('CONFIRMADO', 'Confirmado'),
        ('DIVERGENTE', 'Divergente'),
        ('NAO_ENCONTRADO', 'Não Encontrado'),
    ]
    
    academia = models.ForeignKey(Academia, on_delete=models.CASCADE, related_name='conferencias_pagamento', verbose_name="Academia")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='conferencias_pagamento', verbose_name="Campeonato", null=False, blank=False)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name="Status da Conferência"
    )
    valor_esperado = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Esperado")
    valor_recebido = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Valor Recebido")
    comprovante = models.FileField(
        upload_to='comprovantes/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Comprovante",
        help_text="Comprovante de pagamento enviado pela academia (JPG, PNG, PDF ou HEIC)"
    )
    conferido_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conferencias_realizadas',
        verbose_name="Conferido por"
    )
    data_conferencia = models.DateTimeField(null=True, blank=True, verbose_name="Data da Conferência")
    atualizado_em = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    quantidade_atletas = models.IntegerField(default=0, verbose_name="Quantidade de Atletas")
    
    class Meta:
        verbose_name = "Conferência de Pagamento"
        verbose_name_plural = "Conferências de Pagamento"
        ordering = ['-data_conferencia']
        unique_together = ('academia', 'campeonato')
    
    def __str__(self):
        return f"{self.academia.nome} - {self.campeonato.nome} - {self.get_status_display()}"


class HistoricoSistema(models.Model):
    """Registro de histórico de todas as ações importantes no sistema"""
    TIPO_ACAO_CHOICES = [
        ('INSCRICAO', 'Inscrição'),
        ('PESAGEM', 'Pesagem'),
        ('PAGAMENTO', 'Pagamento'),
        ('CONFERENCIA_PAGAMENTO', 'Conferência de Pagamento'),
        ('CHAVE', 'Geração de Chave'),
        ('RESULTADO', 'Registro de Resultado'),
        ('PONTUACAO', 'Cálculo de Pontuação'),
        ('ACADEMIA', 'Cadastro/Edição de Academia'),
        ('ATLETA', 'Cadastro/Edição de Atleta'),
        ('CAMPEONATO', 'Cadastro/Edição de Campeonato'),
        ('USUARIO', 'Criação/Edição de Usuário'),
        ('OUTRO', 'Outro'),
    ]
    
    tipo_acao = models.CharField(max_length=50, choices=TIPO_ACAO_CHOICES, verbose_name="Tipo de Ação")
    descricao = models.TextField(verbose_name="Descrição")
    usuario = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_acoes',
        verbose_name="Usuário"
    )
    campeonato = models.ForeignKey(
        Campeonato,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_acoes',
        verbose_name="Campeonato"
    )
    academia = models.ForeignKey(
        Academia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_acoes',
        verbose_name="Academia"
    )
    atleta = models.ForeignKey(
        Atleta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historico_acoes',
        verbose_name="Atleta"
    )
    dados_extras = models.JSONField(null=True, blank=True, verbose_name="Dados Extras", help_text="Dados adicionais em formato JSON")
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="Endereço IP")
    
    class Meta:
        verbose_name = "Histórico do Sistema"
        verbose_name_plural = "Históricos do Sistema"
        ordering = ['-data_hora']
        indexes = [
            models.Index(fields=['tipo_acao', 'data_hora']),
            models.Index(fields=['campeonato', 'data_hora']),
            models.Index(fields=['usuario', 'data_hora']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_acao_display()} - {self.descricao[:50]} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"


class Ocorrencia(models.Model):
    """Registro de ocorrências e problemas durante eventos"""
    CATEGORIA_CHOICES = [
        ('RELATO_PROFESSOR', 'Relato de Professor'),
        ('PROBLEMA_PESAGEM', 'Problema em Pesagem'),
        ('INDISCIPLINA', 'Indisciplina'),
        ('ACIDENTE', 'Acidente'),
        ('PROBLEMA_TECNICO', 'Problema Técnico'),
        ('PROBLEMA_ORGANIZACIONAL', 'Problema Organizacional'),
        ('RECLAMACAO', 'Reclamação'),
        ('SUGESTAO', 'Sugestão'),
        ('OUTRO', 'Outro'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('BAIXA', 'Baixa'),
        ('MEDIA', 'Média'),
        ('ALTA', 'Alta'),
        ('URGENTE', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('EM_ANDAMENTO', 'Em Andamento'),
        ('RESOLVIDA', 'Resolvida'),
        ('ENCERRADA', 'Encerrada'),
    ]
    
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, verbose_name="Categoria")
    titulo = models.CharField(max_length=200, verbose_name="Título")
    descricao = models.TextField(verbose_name="Descrição Detalhada")
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='MEDIA', verbose_name="Prioridade")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABERTA', verbose_name="Status")
    
    campeonato = models.ForeignKey(
        Campeonato,
        on_delete=models.CASCADE,
        related_name='ocorrencias',
        verbose_name="Campeonato"
    )
    academia = models.ForeignKey(
        Academia,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias',
        verbose_name="Academia"
    )
    atleta = models.ForeignKey(
        Atleta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias',
        verbose_name="Atleta Envolvido"
    )
    inscricao = models.ForeignKey(
        Inscricao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias',
        verbose_name="Inscrição Relacionada"
    )
    
    # Responsáveis
    registrado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias_registradas',
        verbose_name="Registrado por"
    )
    responsavel_resolucao = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias_responsavel',
        verbose_name="Responsável pela Resolução"
    )
    
    # Datas
    data_ocorrencia = models.DateTimeField(verbose_name="Data da Ocorrência", help_text="Data e hora em que o problema ocorreu")
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Registro")
    data_resolucao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Resolução")
    
    # Resolução
    solucao = models.TextField(blank=True, verbose_name="Solução Aplicada")
    observacoes = models.TextField(blank=True, verbose_name="Observações Adicionais")
    
    # Anexos (fotos, documentos)
    anexos = models.JSONField(null=True, blank=True, verbose_name="Anexos", help_text="Lista de URLs de arquivos anexados")
    
    class Meta:
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = ['-data_ocorrencia', '-data_registro']
        indexes = [
            models.Index(fields=['campeonato', 'status']),
            models.Index(fields=['categoria', 'status']),
            models.Index(fields=['prioridade', 'status']),
        ]
    
    def __str__(self):
        return f"{self.get_categoria_display()} - {self.titulo} - {self.campeonato.nome}"
    
    def marcar_como_resolvida(self, usuario, solucao=''):
        """Marca a ocorrência como resolvida"""
        from django.utils import timezone
        self.status = 'RESOLVIDA'
        self.data_resolucao = timezone.now()
        self.responsavel_resolucao = usuario
        if solucao:
            self.solucao = solucao
        self.save()
