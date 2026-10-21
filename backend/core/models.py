import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


# ---------------------------------------------------------------- Enumeracoes
class TipoUsuario(models.TextChoices):
    ADMINISTRADOR = "ADMINISTRADOR"
    DOCENTE = "DOCENTE"
    SECRETARIA = "SECRETARIA"
    ALUNO = "ALUNO"
    MEMBRO_EXTERNO = "MEMBRO_EXTERNO"


class Departamento(models.TextChoices):
    SI = "SI"
    ECP = "ECP"
    LIC = "LIC"


class NomeCurso(models.TextChoices):
    ENG_COMPUTACAO = "ENG_COMPUTACAO"
    SISTEMAS_INFORMACAO = "SISTEMAS_INFORMACAO"
    LICENCIATURA_COMPUTACAO = "LICENCIATURA_COMPUTACAO"


class ModalidadeConclusao(models.TextChoices):
    DEFESA_EM_BANCA = "DEFESA_EM_BANCA"
    PUBLICACAO_APROVADA = "PUBLICACAO_APROVADA"


class StatusTCC(models.TextChoices):
    EM_DESENVOLVIMENTO = "EM_DESENVOLVIMENTO"
    APRESENTADO = "APRESENTADO"
    NAO_APRESENTADO = "NAO_APRESENTADO"
    APROVADO_POR_PUBLICACAO = "APROVADO_POR_PUBLICACAO"


class Visibilidade(models.TextChoices):
    PUBLICO_TEXTO_COMPLETO = "PUBLICO_TEXTO_COMPLETO"
    PUBLICO_METADADOS = "PUBLICO_METADADOS"
    RESTRITO = "RESTRITO"


class MotivoNaoApresentacao(models.TextChoices):
    DESISTENCIA = "DESISTENCIA"
    TRANCAMENTO = "TRANCAMENTO"
    TRANSFERENCIA = "TRANSFERENCIA"
    OUTRO = "OUTRO"


class TipoLocal(models.TextChoices):
    PRESENCIAL = "PRESENCIAL"
    REMOTO = "REMOTO"


class TipoMembroBanca(models.TextChoices):
    TITULAR = "TITULAR"
    SUPLENTE = "SUPLENTE"


class TipoConvite(models.TextChoices):
    BANCA = "BANCA"
    AUDIENCIA = "AUDIENCIA"


class StatusConvite(models.TextChoices):
    PENDENTE = "PENDENTE"
    ACEITO = "ACEITO"
    RECUSADO = "RECUSADO"


class StatusSolicitacao(models.TextChoices):
    PENDENTE = "PENDENTE"
    ACEITA = "ACEITA"
    RECUSADA = "RECUSADA"


# ------------------------------------------------------- Usuarios e perfis
class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError("email obrigatorio")
        user = self.model(email=self.normalize_email(email), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("tipo_usuario", TipoUsuario.ADMINISTRADOR)
        return self.create_user(email, password, **extra)


class Usuario(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome_completo = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    # A coluna do banco segue o DER (senha_hash); o Django guarda o hash aqui.
    password = models.CharField(max_length=128, db_column="senha_hash")
    tipo_usuario = models.CharField(max_length=20, choices=TipoUsuario.choices)
    ativo = models.BooleanField(default=True)
    tentativas_falhas = models.PositiveSmallIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)

    objects = UsuarioManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome_completo", "tipo_usuario"]

    @property
    def is_active(self):
        return self.ativo

    class Meta:
        db_table = "usuario"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo_usuario__in=TipoUsuario.values),
                name="ck_usuario_tipo_usuario",
            ),
        ]


class AreaConhecimento(UUIDModel):
    nome = models.CharField(max_length=120, unique=True)

    class Meta:
        db_table = "area_conhecimento"


class Curso(UUIDModel):
    nome = models.CharField(max_length=40, unique=True, choices=NomeCurso.choices)

    class Meta:
        db_table = "curso"
        constraints = [
            models.CheckConstraint(
                condition=Q(nome__in=NomeCurso.values), name="ck_curso_nome"
            ),
        ]


class Docente(models.Model):
    usuario = models.OneToOneField(
        Usuario, primary_key=True, on_delete=models.CASCADE, related_name="docente"
    )
    matricula_institucional = models.CharField(max_length=30, unique=True)
    cpf = models.CharField(max_length=11, unique=True)
    departamento = models.CharField(max_length=3, choices=Departamento.choices)
    professor_tcc = models.BooleanField(default=False)
    aceita_orientacoes = models.BooleanField(default=True)
    areas_interesse = models.ManyToManyField(
        AreaConhecimento, blank=True, db_table="docente_area_interesse"
    )

    class Meta:
        db_table = "docente"
        constraints = [
            models.CheckConstraint(
                condition=Q(departamento__in=Departamento.values),
                name="ck_docente_departamento",
            ),
        ]


class Aluno(models.Model):
    usuario = models.OneToOneField(
        Usuario, primary_key=True, on_delete=models.CASCADE, related_name="aluno"
    )
    matricula = models.CharField(max_length=30, unique=True)
    cpf = models.CharField(max_length=11, unique=True)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="alunos")
    cadastro_confirmado = models.BooleanField(default=False)
    areas_interesse = models.ManyToManyField(
        AreaConhecimento, blank=True, db_table="aluno_area_interesse"
    )

    class Meta:
        db_table = "aluno"


class MembroExterno(models.Model):
    usuario = models.OneToOneField(
        Usuario, primary_key=True, on_delete=models.CASCADE, related_name="membro_externo"
    )
    instituicao_origem = models.CharField(max_length=200)

    class Meta:
        db_table = "membro_externo"


# ------------------------------------------------------------- TCC
class TCC(UUIDModel):
    titulo = models.CharField(max_length=300)
    subtitulo = models.CharField(max_length=300, null=True, blank=True)
    curso = models.ForeignKey(Curso, on_delete=models.PROTECT, related_name="tccs")
    area_conhecimento = models.ForeignKey(
        AreaConhecimento, on_delete=models.PROTECT, related_name="tccs"
    )
    modalidade = models.CharField(max_length=20, choices=ModalidadeConclusao.choices)
    status = models.CharField(
        max_length=25, choices=StatusTCC.choices, default=StatusTCC.EM_DESENVOLVIMENTO
    )
    visibilidade = models.CharField(
        max_length=25, choices=Visibilidade.choices, default=Visibilidade.RESTRITO
    )
    motivo_nao_apresentacao = models.CharField(
        max_length=15, choices=MotivoNaoApresentacao.choices, null=True, blank=True
    )
    motivo_outro = models.TextField(null=True, blank=True)
    link_externo = models.URLField(null=True, blank=True)
    arquivo_tcc_path = models.CharField(max_length=500, null=True, blank=True)
    ativo = models.BooleanField(default=True)
    motivo_inativacao = models.TextField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(Aluno, on_delete=models.PROTECT, related_name="tccs")
    orientador = models.ForeignKey(
        Docente, on_delete=models.PROTECT, related_name="tccs_orientados"
    )
    coorientador = models.ForeignKey(
        Docente,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="tccs_coorientados",
    )

    class Meta:
        db_table = "tcc"
        constraints = [
            # RD05: 1 TCC ativo por aluno e curso
            models.UniqueConstraint(
                fields=["autor", "curso"],
                condition=Q(ativo=True),
                name="uq_tcc_ativo_por_aluno_curso",
            ),
            # RD04: coorientador diferente do orientador
            models.CheckConstraint(
                condition=Q(coorientador__isnull=True)
                | ~Q(coorientador=models.F("orientador")),
                name="ck_tcc_coorientador_diferente",
            ),
            # RD11: motivo obrigatorio em NAO_APRESENTADO
            models.CheckConstraint(
                condition=~Q(status="NAO_APRESENTADO")
                | Q(motivo_nao_apresentacao__isnull=False),
                name="ck_tcc_motivo_nao_apresentacao",
            ),
            # RD11: "outro" exige descricao
            models.CheckConstraint(
                condition=~Q(motivo_nao_apresentacao="OUTRO")
                | Q(motivo_outro__isnull=False),
                name="ck_tcc_motivo_outro",
            ),
            # RD13: inativar exige motivo
            models.CheckConstraint(
                condition=Q(ativo=True) | Q(motivo_inativacao__isnull=False),
                name="ck_tcc_motivo_inativacao",
            ),
            # Valores permitidos das listas fixas (NULL passa; a regra de
            # obrigatoriedade esta nas restricoes acima)
            models.CheckConstraint(
                condition=Q(modalidade__in=ModalidadeConclusao.values),
                name="ck_tcc_modalidade",
            ),
            models.CheckConstraint(
                condition=Q(status__in=StatusTCC.values), name="ck_tcc_status"
            ),
            models.CheckConstraint(
                condition=Q(visibilidade__in=Visibilidade.values),
                name="ck_tcc_visibilidade",
            ),
            models.CheckConstraint(
                condition=Q(motivo_nao_apresentacao__in=MotivoNaoApresentacao.values),
                name="ck_tcc_motivo_lista",
            ),
        ]


class HistoricoStatus(UUIDModel):
    tcc = models.ForeignKey(TCC, on_delete=models.CASCADE, related_name="historico_status")
    status = models.CharField(max_length=25, choices=StatusTCC.choices)
    data_alteracao = models.DateTimeField(auto_now_add=True)
    justificativa = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "historico_status"
        ordering = ["-data_alteracao"]
        constraints = [
            models.CheckConstraint(
                condition=Q(status__in=StatusTCC.values),
                name="ck_historico_status_status",
            ),
        ]


class Publicacao(UUIDModel):
    tcc = models.OneToOneField(TCC, on_delete=models.CASCADE, related_name="publicacao")
    periodico = models.CharField(max_length=300)
    issn_doi = models.CharField(max_length=100)
    data_publicacao = models.DateField()
    comprovante_arquivo_path = models.CharField(max_length=500)
    link_artigo = models.URLField(null=True, blank=True)

    class Meta:
        db_table = "publicacao"


# ------------------------------------------------------ Bancas e defesas
class Banca(UUIDModel):
    tcc = models.OneToOneField(TCC, on_delete=models.CASCADE, related_name="banca")
    data_hora = models.DateTimeField()
    tipo_local = models.CharField(max_length=10, choices=TipoLocal.choices)
    local = models.CharField(max_length=300)

    class Meta:
        db_table = "banca"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo_local__in=TipoLocal.values), name="ck_banca_tipo_local"
            ),
        ]


class ParticipacaoBanca(UUIDModel):
    banca = models.ForeignKey(Banca, on_delete=models.CASCADE, related_name="participacoes")
    usuario = models.ForeignKey(
        Usuario, on_delete=models.PROTECT, related_name="participacoes_banca"
    )
    tipo_membro = models.CharField(max_length=10, choices=TipoMembroBanca.choices)
    presente = models.BooleanField(null=True, blank=True)
    substituiu_titular = models.BooleanField(default=False)

    class Meta:
        db_table = "participacao_banca"
        constraints = [
            # RBN10: a mesma pessoa nao repete na banca
            models.UniqueConstraint(
                fields=["banca", "usuario"], name="uq_participacao_banca_usuario"
            ),
            # RD28: so suplente pode ter substituido um titular
            models.CheckConstraint(
                condition=Q(substituiu_titular=False) | Q(tipo_membro="SUPLENTE"),
                name="ck_participacao_substituiu_so_suplente",
            ),
            models.CheckConstraint(
                condition=Q(tipo_membro__in=TipoMembroBanca.values),
                name="ck_participacao_tipo_membro",
            ),
        ]


class Avaliacao(UUIDModel):
    participacao = models.OneToOneField(
        ParticipacaoBanca, on_delete=models.CASCADE, related_name="avaliacao"
    )
    nota = models.DecimalField(max_digits=4, decimal_places=2)

    class Meta:
        db_table = "avaliacao"


class Convite(UUIDModel):
    banca = models.ForeignKey(Banca, on_delete=models.CASCADE, related_name="convites")
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="convites")
    tipo = models.CharField(max_length=10, choices=TipoConvite.choices)
    status = models.CharField(
        max_length=10, choices=StatusConvite.choices, default=StatusConvite.PENDENTE
    )

    class Meta:
        db_table = "convite"
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo__in=TipoConvite.values), name="ck_convite_tipo"
            ),
            models.CheckConstraint(
                condition=Q(status__in=StatusConvite.values), name="ck_convite_status"
            ),
        ]


class TokenAcesso(UUIDModel):
    membro_externo = models.ForeignKey(
        MembroExterno, on_delete=models.CASCADE, related_name="tokens"
    )
    banca = models.ForeignKey(Banca, on_delete=models.CASCADE, related_name="tokens")
    token_hash = models.CharField(max_length=128)
    gerado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    invalidado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "token_acesso"
        constraints = [
            models.UniqueConstraint(
                fields=["membro_externo", "banca"], name="uq_token_membro_banca"
            ),
        ]


# ------------------------------------------------------ Orientacao academica
class SolicitacaoOrientacao(UUIDModel):
    aluno = models.ForeignKey(Aluno, on_delete=models.PROTECT, related_name="solicitacoes")
    docente = models.ForeignKey(
        Docente, on_delete=models.PROTECT, related_name="solicitacoes_recebidas"
    )
    mensagem = models.TextField()
    status = models.CharField(
        max_length=10, choices=StatusSolicitacao.choices, default=StatusSolicitacao.PENDENTE
    )
    motivo_recusa = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "solicitacao_orientacao"
        constraints = [
            models.CheckConstraint(
                condition=~Q(status="RECUSADA") | Q(motivo_recusa__isnull=False),
                name="ck_solicitacao_motivo_recusa",
            ),
            models.CheckConstraint(
                condition=Q(status__in=StatusSolicitacao.values),
                name="ck_solicitacao_status",
            ),
        ]


class ReuniaoAlinhamento(UUIDModel):
    solicitacao = models.OneToOneField(
        SolicitacaoOrientacao, on_delete=models.CASCADE, related_name="reuniao"
    )
    data_hora = models.DateTimeField()
    local = models.CharField(max_length=300)

    class Meta:
        db_table = "reuniao_alinhamento"


# ------------------------------------------------------------ Auditoria
class LogAuditoria(UUIDModel):
    responsavel = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="logs_auditoria")
    data_hora = models.DateTimeField(auto_now_add=True)
    entidade = models.CharField(max_length=60)
    registro_id = models.UUIDField()
    campo = models.CharField(max_length=60)
    valor_anterior = models.TextField(null=True, blank=True)
    valor_novo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "log_auditoria"
        indexes = [models.Index(fields=["entidade", "registro_id"])]


class LogAcesso(UUIDModel):
    usuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name="logs_acesso")
    data_hora = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField()

    class Meta:
        db_table = "log_acesso"
