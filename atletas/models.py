from django.db import models
<<<<<<< HEAD
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone


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


=======
from datetime import date
from django.utils import timezone


>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
class Academia(models.Model):
    nome = models.CharField(max_length=200)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
<<<<<<< HEAD
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
=======
    pontos = models.IntegerField(default=0)
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17

    class Meta:
        verbose_name = "Academia"
        verbose_name_plural = "Academias"
        ordering = ['nome']

    def __str__(self):
        return self.nome
<<<<<<< HEAD
    
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
=======
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17


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
<<<<<<< HEAD
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
    
    # Campos de auditoria
    data_cadastro = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name="Data de Cadastro")
    data_atualizacao = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name="Data de Atualização")
=======
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
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17

    class Meta:
        verbose_name = "Atleta"
        verbose_name_plural = "Atletas"
        ordering = ['nome']

    @property
    def idade(self):
        """Calcula a idade do atleta"""
<<<<<<< HEAD
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
                return calcular_classe(ano)
            return self.classe_inicial or "SÊNIOR"
        except:
            return self.classe_inicial or "SÊNIOR"

    def __str__(self):
        return f"{self.nome} ({self.academia.nome})"


class Chave(models.Model):
    campeonato = models.ForeignKey('Campeonato', on_delete=models.CASCADE, related_name='chaves', verbose_name="Campeonato", null=True, blank=True, help_text="Campeonato ao qual esta chave pertence")
=======
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

    def __str__(self):
        return f"{self.nome} ({self.classe} - {self.categoria_nome})"


class Chave(models.Model):
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
    classe = models.CharField(max_length=20)
    sexo = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')])
    categoria = models.CharField(max_length=100)
    atletas = models.ManyToManyField(Atleta, related_name='chaves')
    estrutura = models.JSONField(default=dict)  # Estrutura da chave (árvore de lutas)

    class Meta:
        verbose_name = "Chave"
        verbose_name_plural = "Chaves"
<<<<<<< HEAD
        ordering = ['-campeonato__data_competicao', 'classe', 'sexo', 'categoria']

    def __str__(self):
        campeonato_nome = f" - {self.campeonato.nome}" if self.campeonato else ""
        return f"{self.classe} - {self.get_sexo_display()} - {self.categoria}{campeonato_nome}"
=======
        ordering = ['classe', 'sexo', 'categoria']

    def __str__(self):
        return f"{self.classe} - {self.get_sexo_display()} - {self.categoria}"
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17


class Luta(models.Model):
    TIPO_VITORIA_CHOICES = [
        ("IPPON", "Ippon"),
        ("WAZARI", "Wazari"),
<<<<<<< HEAD
=======
        ("WAZARI_WAZARI", "Wazari-Wazari"),
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
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


<<<<<<< HEAD
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
    nome = models.CharField(max_length=200, default="Campeonato Padrão")
    data_inicio = models.DateField(null=True, blank=True, help_text="Data de início das inscrições")
    data_competicao = models.DateField(null=True, blank=True, help_text="Data da competição")
    data_limite_inscricao = models.DateField(null=True, blank=True, help_text="Data limite para inscrições")
    ativo = models.BooleanField(default=True)
    regulamento = models.TextField(blank=True, help_text="Regulamento do campeonato")
    valor_inscricao_federado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Valor da inscrição para atletas federados")
    valor_inscricao_nao_federado = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Valor da inscrição para atletas não federados")
    
    # Campos de pagamento
    chave_pix = models.CharField(max_length=200, blank=True, verbose_name="Chave PIX", help_text="Chave PIX para pagamento (CPF, CNPJ, Email, Telefone ou Chave Aleatória)")
    titular_pix = models.CharField(max_length=200, blank=True, verbose_name="Titular da Chave PIX", help_text="Nome do titular da conta PIX")
    formas_pagamento = models.ManyToManyField('FormaPagamento', blank=True, verbose_name="Formas de Pagamento Aceitas", help_text="Selecione as formas de pagamento aceitas para este evento")
=======
class Campeonato(models.Model):
    nome = models.CharField(max_length=200, default="Campeonato Padrão")
    data_inicio = models.DateField(null=True, blank=True)
    data_fim = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17

    class Meta:
        verbose_name = "Campeonato"
        verbose_name_plural = "Campeonatos"
        ordering = ['-data_inicio', 'nome']

    def __str__(self):
        return self.nome


<<<<<<< HEAD
class Inscricao(models.Model):
    """Inscrição de um atleta em um campeonato específico"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]

    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='inscricoes', verbose_name="Atleta")
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='inscricoes', verbose_name="Campeonato")
    
    # Classe e categoria escolhidas na inscrição
    classe_escolhida = models.CharField(max_length=20, verbose_name="Classe Escolhida")
    categoria_escolhida = models.CharField(max_length=100, verbose_name="Categoria Escolhida", blank=True)
    
    # Dados da pesagem (preenchidos após pesagem)
    peso = models.FloatField(null=True, blank=True, verbose_name="Peso Oficial (kg)")
    categoria_ajustada = models.CharField(max_length=100, blank=True, verbose_name="Categoria Ajustada")
    motivo_ajuste = models.TextField(blank=True, verbose_name="Motivo do Ajuste")
    remanejado = models.BooleanField(default=False, verbose_name="Remanejado")
    
    # Status da inscrição
    status_inscricao = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
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
        return self.status_inscricao == 'aprovado' and self.peso is not None


=======
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
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
<<<<<<< HEAD
        return f"{self.academia.nome} - {self.campeonato.nome} ({self.pontos_totais} pts)"


class Despesa(models.Model):
    """Despesas do campeonato"""
    CATEGORIA_CHOICES = [
        ('arbitros', 'Árbitros'),
        ('mesarios', 'Mesários'),
        ('coordenadores', 'Coordenadores'),
        ('oficiais_pesagem', 'Oficiais de Pesagem'),
        ('oficiais_mesa', 'Oficiais de Mesa'),
        ('insumos', 'Insumos'),
        ('ambulancia', 'Ambulância'),
        ('patrocinios', 'Patrocínios (entrada)'),
        ('estrutura', 'Estrutura'),
        ('limpeza', 'Limpeza'),
        ('outras', 'Outras'),
    ]
    
    STATUS_CHOICES = [
        ('pago', 'Pago'),
        ('pendente', 'Pendente'),
    ]
    
    campeonato = models.ForeignKey(Campeonato, on_delete=models.CASCADE, related_name='despesas', verbose_name="Campeonato")
    categoria = models.CharField(max_length=50, choices=CATEGORIA_CHOICES, verbose_name="Categoria")
    nome = models.CharField(max_length=200, verbose_name="Nome da Despesa")
    valor = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente', verbose_name="Status")
    observacao = models.TextField(blank=True, verbose_name="Observação")
    contato_nome = models.CharField(max_length=200, blank=True, verbose_name="Contato Responsável")
    contato_whatsapp = models.CharField(max_length=20, blank=True, verbose_name="WhatsApp do Contato")
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    
    class Meta:
        verbose_name = "Despesa"
        verbose_name_plural = "Despesas"
        ordering = ['-data_cadastro']
    
    def __str__(self):
        return f"{self.nome} - {self.get_categoria_display()} - R$ {self.valor}"


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


class UsuarioOperacional(models.Model):
    """Perfil de usuário operacional com permissões e expiração"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_operacional', verbose_name="Usuário")
    pode_resetar_campeonato = models.BooleanField(default=False, verbose_name="Pode Resetar Campeonato", help_text="Permissão para resetar campeonato (apenas usuário principal)")
    pode_criar_usuarios = models.BooleanField(default=False, verbose_name="Pode Criar Usuários", help_text="Permissão para criar novos usuários operacionais (apenas usuário principal)")
    data_expiracao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Expiração", help_text="Data de expiração do acesso (null = vitalício)")
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios_criados', verbose_name="Criado Por")
    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
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
        help_text="Comprovante de pagamento (JPG, PNG ou PDF)"
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
=======
        return f"{self.academia.nome} - {self.campeonato.nome} ({self.pontos_totais} pts)"
>>>>>>> dd494c57289dd9cfb039519c18e2065bb3b48a17
