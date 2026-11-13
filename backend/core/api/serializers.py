from rest_framework import serializers

from core.models import (
    TCC,
    Aluno,
    AreaConhecimento,
    Banca,
    Convite,
    Curso,
    Departamento,
    Docente,
    HistoricoStatus,
    MotivoNaoApresentacao,
    ParticipacaoBanca,
    Publicacao,
    ReuniaoAlinhamento,
    SolicitacaoOrientacao,
    StatusTCC,
    TipoLocal,
    Usuario,
)
from core.services import escopo
from core.services.pessoas import TIPOS_GERAIS
from core.services.solicitacao import RESPOSTAS
from core.validators import cpf_valido, mascarar_cpf, so_digitos


# ------------------------------------------------------------------ TCC
class TCCSerializer(serializers.ModelSerializer):
    # B9b: nomes prontos para as telas (as FKs continuam vindo como id)
    autor_nome = serializers.CharField(
        source="autor.usuario.nome_completo", read_only=True
    )
    autor_matricula = serializers.CharField(source="autor.matricula", read_only=True)
    orientador_nome = serializers.CharField(
        source="orientador.usuario.nome_completo", read_only=True
    )
    coorientador_nome = serializers.CharField(
        source="coorientador.usuario.nome_completo", read_only=True, allow_null=True
    )
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    area_nome = serializers.CharField(source="area_conhecimento.nome", read_only=True)
    # C17: a tela so mostra editar, mudar situacao e banca para quem pode
    pode_editar = serializers.SerializerMethodField()

    class Meta:
        model = TCC
        fields = [
            "id",
            "titulo",
            "subtitulo",
            "curso",
            "curso_nome",
            "area_conhecimento",
            "area_nome",
            "modalidade",
            "visibilidade",
            "status",
            "motivo_nao_apresentacao",
            "motivo_outro",
            "ativo",
            "data_cadastro",
            "autor",
            "autor_nome",
            "autor_matricula",
            "orientador",
            "orientador_nome",
            "coorientador",
            "coorientador_nome",
            "pode_editar",
        ]
        # status so muda pela rota /situacao/ (B7b); curso vem do aluno
        read_only_fields = [
            "id",
            "curso",
            "status",
            "motivo_nao_apresentacao",
            "motivo_outro",
            "ativo",
            "data_cadastro",
        ]

    def get_pode_editar(self, obj):
        request = self.context.get("request")
        usuario = getattr(request, "user", None)
        if not (usuario and usuario.is_authenticated):
            return False
        return escopo.pode_editar_tcc(usuario, obj)


class HistoricoStatusSerializer(serializers.ModelSerializer):
    # DER v2: quem mudou o status
    alterado_por_nome = serializers.CharField(
        source="alterado_por.nome_completo", read_only=True
    )

    class Meta:
        model = HistoricoStatus
        fields = [
            "status",
            "data_alteracao",
            "alterado_por",
            "alterado_por_nome",
            "justificativa",
        ]


class PublicacaoSerializer(serializers.ModelSerializer):
    """C1: dados da publicacao que aprovou o TCC."""

    class Meta:
        model = Publicacao
        fields = [
            "periodico",
            "issn_doi",
            "data_publicacao",
            "comprovante_arquivo_path",
            "link_artigo",
        ]


class TCCDetalheSerializer(TCCSerializer):
    """Detalhe do TCC: historico de situacao (do mais novo ao mais antigo), banca e publicacao."""

    historico = HistoricoStatusSerializer(
        source="historico_status", many=True, read_only=True
    )
    banca = serializers.SerializerMethodField()
    publicacao = serializers.SerializerMethodField()

    class Meta(TCCSerializer.Meta):
        fields = [*TCCSerializer.Meta.fields, "historico", "banca", "publicacao"]

    def get_banca(self, obj):
        banca = getattr(obj, "banca", None)
        return BancaSerializer(banca).data if banca else None

    def get_publicacao(self, obj):
        publicacao = getattr(obj, "publicacao", None)
        return PublicacaoSerializer(publicacao).data if publicacao else None


class MudarSituacaoSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=StatusTCC.choices)
    motivo_nao_apresentacao = serializers.ChoiceField(
        choices=MotivoNaoApresentacao.choices, required=False, allow_null=True
    )
    motivo_outro = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    justificativa = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )


class RegistrarPublicacaoSerializer(serializers.Serializer):
    """Entrada de POST /api/tccs/{id}/publicacao/ (C1)."""

    periodico = serializers.CharField(max_length=300)
    issn_doi = serializers.CharField(max_length=100)
    data_publicacao = serializers.DateField()
    comprovante_arquivo_path = serializers.CharField(max_length=500)
    link_artigo = serializers.URLField(
        required=False, allow_null=True, allow_blank=True
    )


# ---------------------------------------------------------------- Banca
class CadastrarBancaSerializer(serializers.Serializer):
    tcc = serializers.PrimaryKeyRelatedField(queryset=TCC.objects.all())
    titulares = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), many=True
    )
    suplentes = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), many=True, required=False
    )
    data_hora_inicio = serializers.DateTimeField()
    tipo_local = serializers.ChoiceField(choices=TipoLocal.choices)
    # D17: bloco e sala (presencial) ou link (remota); o servico confere qual
    bloco = serializers.CharField(
        max_length=60, required=False, allow_blank=True, allow_null=True
    )
    sala = serializers.CharField(
        max_length=60, required=False, allow_blank=True, allow_null=True
    )
    link_remoto = serializers.CharField(
        max_length=300, required=False, allow_blank=True, allow_null=True
    )


class ParticipacaoSerializer(serializers.ModelSerializer):
    # B9c: nome e perfil de quem compoe a banca, para a tela
    usuario_nome = serializers.CharField(source="usuario.nome_completo", read_only=True)
    tipo_usuario = serializers.CharField(source="usuario.tipo_usuario", read_only=True)

    class Meta:
        model = ParticipacaoBanca
        fields = ["usuario", "usuario_nome", "tipo_usuario", "tipo_membro", "presente"]


class ConviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convite
        fields = ["usuario", "tipo", "status", "enviado_em", "respondido_em"]


class BancaSerializer(serializers.ModelSerializer):
    participacoes = ParticipacaoSerializer(many=True, read_only=True)
    convites = ConviteSerializer(many=True, read_only=True)
    tcc_titulo = serializers.CharField(source="tcc.titulo", read_only=True)
    # D5: termino calculado (inicio + 2 h), nunca guardado
    data_hora_fim = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Banca
        fields = [
            "id",
            "tcc",
            "tcc_titulo",
            "data_hora_inicio",
            "data_hora_fim",
            "tipo_local",
            "bloco",
            "sala",
            "link_remoto",
            "participacoes",
            "convites",
        ]


# -------------------------------------------------------------- Docentes
class DocenteSerializer(serializers.ModelSerializer):
    """Saida: CPF sempre mascarado (RNF12) e as contagens de RBN15 e RBN16."""

    id = serializers.UUIDField(source="pk", read_only=True)
    nome_completo = serializers.CharField(source="usuario.nome_completo")
    email = serializers.EmailField(source="usuario.email")
    ativo = serializers.BooleanField(source="usuario.ativo")
    cpf = serializers.SerializerMethodField()
    qtd_orientacoes = serializers.IntegerField(read_only=True)
    qtd_bancas = serializers.IntegerField(read_only=True)

    class Meta:
        model = Docente
        fields = [
            "id",
            "nome_completo",
            "email",
            "matricula_institucional",
            "cpf",
            "departamento",
            "professor_tcc",
            "aceita_orientacoes",
            "areas_interesse",
            "ativo",
            "qtd_orientacoes",
            "qtd_bancas",
        ]

    def get_cpf(self, obj):
        return mascarar_cpf(obj.cpf)


class CpfField(serializers.CharField):
    """Aceita com ou sem mascara; guarda so os 11 digitos e confere os verificadores."""

    def to_internal_value(self, data):
        cpf = so_digitos(super().to_internal_value(data))
        if not cpf_valido(cpf):
            raise serializers.ValidationError("CPF inválido.")
        return cpf


class DocenteEntradaSerializer(serializers.Serializer):
    nome_completo = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    matricula_institucional = serializers.CharField(max_length=30)
    cpf = CpfField(max_length=14)
    departamento = serializers.ChoiceField(choices=Departamento.choices)
    professor_tcc = serializers.BooleanField(required=False)
    aceita_orientacoes = serializers.BooleanField(required=False)
    areas_interesse = serializers.PrimaryKeyRelatedField(
        queryset=AreaConhecimento.objects.all(), many=True, required=False
    )
    senha_inicial = serializers.CharField(
        required=False, write_only=True, trim_whitespace=False
    )


# ------------------------------------------------------- Alunos (B14)
class AlunoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="pk", read_only=True)
    nome_completo = serializers.CharField(source="usuario.nome_completo")
    email = serializers.EmailField(source="usuario.email")
    ativo = serializers.BooleanField(source="usuario.ativo")
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    cpf = serializers.SerializerMethodField()

    class Meta:
        model = Aluno
        fields = [
            "id",
            "nome_completo",
            "email",
            "matricula",
            "cpf",
            "curso",
            "curso_nome",
            "cadastro_confirmado",
            "ativo",
        ]

    def get_cpf(self, obj):
        return mascarar_cpf(obj.cpf)


class AlunoEntradaSerializer(serializers.Serializer):
    nome_completo = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    matricula = serializers.CharField(max_length=30)
    cpf = CpfField(max_length=14)
    curso = serializers.PrimaryKeyRelatedField(queryset=Curso.objects.all())
    senha_inicial = serializers.CharField(
        required=False, write_only=True, trim_whitespace=False
    )


# --------------------------- Secretaria, administrador e membro externo (B14)
class UsuarioSerializer(serializers.ModelSerializer):
    instituicao_origem = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            "id",
            "nome_completo",
            "email",
            "tipo_usuario",
            "ativo",
            "instituicao_origem",
        ]

    def get_instituicao_origem(self, obj):
        externo = getattr(obj, "membro_externo", None)
        return externo.instituicao_origem if externo else None


class UsuarioEntradaSerializer(serializers.Serializer):
    nome_completo = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    tipo_usuario = serializers.ChoiceField(choices=[(t, t) for t in TIPOS_GERAIS])
    instituicao_origem = serializers.CharField(max_length=200, required=False)
    senha_inicial = serializers.CharField(
        required=False, write_only=True, trim_whitespace=False
    )


# ------------------------------------------------------ Catalogos (B14)
class CursoSerializer(serializers.ModelSerializer):
    rotulo = serializers.CharField(source="get_nome_display", read_only=True)

    class Meta:
        model = Curso
        fields = ["id", "nome", "rotulo"]


class AreaConhecimentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = AreaConhecimento
        fields = ["id", "nome"]


# ------------------------------------------- C3a: orientacao academica (7.2)
class OrientadorSerializer(serializers.ModelSerializer):
    """PF63: busca de orientador pelo aluno. Sem CPF nem matricula (RNF12)."""

    id = serializers.UUIDField(source="pk", read_only=True)
    nome_completo = serializers.CharField(source="usuario.nome_completo")
    email = serializers.EmailField(source="usuario.email")
    areas_interesse = AreaConhecimentoSerializer(many=True, read_only=True)
    qtd_orientacoes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Docente
        fields = [
            "id",
            "nome_completo",
            "email",
            "departamento",
            "aceita_orientacoes",
            "areas_interesse",
            "qtd_orientacoes",
        ]


class ReuniaoSerializer(serializers.ModelSerializer):
    """C3b (PF45): reuniao de alinhamento, com quem participa."""

    aluno_nome = serializers.CharField(
        source="solicitacao.aluno.usuario.nome_completo", read_only=True
    )
    docente_nome = serializers.CharField(
        source="solicitacao.docente.usuario.nome_completo", read_only=True
    )

    class Meta:
        model = ReuniaoAlinhamento
        fields = [
            "id",
            "solicitacao",
            "aluno_nome",
            "docente_nome",
            "data_hora",
            "tipo_local",
            "local",
        ]


class AgendarReuniaoSerializer(serializers.Serializer):
    data_hora = serializers.DateTimeField()
    tipo_local = serializers.ChoiceField(choices=TipoLocal.choices)
    local = serializers.CharField(max_length=300)


class SolicitacaoOrientacaoSerializer(serializers.ModelSerializer):
    aluno_nome = serializers.CharField(
        source="aluno.usuario.nome_completo", read_only=True
    )
    aluno_email = serializers.EmailField(source="aluno.usuario.email", read_only=True)
    aluno_curso = serializers.CharField(source="aluno.curso.nome", read_only=True)
    docente_nome = serializers.CharField(
        source="docente.usuario.nome_completo", read_only=True
    )
    # C3b: a reuniao agendada depois do aceite (ou null)
    reuniao = serializers.SerializerMethodField()

    class Meta:
        model = SolicitacaoOrientacao
        fields = [
            "id",
            "aluno",
            "aluno_nome",
            "aluno_email",
            "aluno_curso",
            "docente",
            "docente_nome",
            "mensagem",
            "status",
            "motivo_recusa",
            "enviada_em",
            "respondida_em",
            "reuniao",
        ]

    def get_reuniao(self, obj):
        reuniao = getattr(obj, "reuniao", None)
        if reuniao is None:
            return None
        return {
            "id": str(reuniao.id),
            "data_hora": serializers.DateTimeField().to_representation(
                reuniao.data_hora
            ),
            "tipo_local": reuniao.tipo_local,
            "local": reuniao.local,
        }


class EnviarSolicitacaoSerializer(serializers.Serializer):
    docente = serializers.PrimaryKeyRelatedField(
        queryset=Docente.objects.select_related("usuario")
    )
    mensagem = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, allow_null=True
    )


class ResponderSolicitacaoSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=sorted(RESPOSTAS))
    motivo_recusa = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, allow_null=True
    )
