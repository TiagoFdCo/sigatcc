from rest_framework import serializers

from core.models import (
    TCC,
    Aluno,
    AreaConhecimento,
    Banca,
    Curso,
    Departamento,
    Docente,
    HistoricoStatus,
    MotivoNaoApresentacao,
    ParticipacaoBanca,
    StatusTCC,
    TipoLocal,
    Usuario,
)
from core.services.pessoas import TIPOS_GERAIS
from core.validators import cpf_valido, mascarar_cpf, so_digitos


# ------------------------------------------------------------------ TCC
class TCCSerializer(serializers.ModelSerializer):
    # B9b: nomes prontos para as telas (as FKs continuam vindo como id)
    autor_nome = serializers.CharField(source="autor.usuario.nome_completo", read_only=True)
    autor_matricula = serializers.CharField(source="autor.matricula", read_only=True)
    orientador_nome = serializers.CharField(
        source="orientador.usuario.nome_completo", read_only=True
    )
    coorientador_nome = serializers.CharField(
        source="coorientador.usuario.nome_completo", read_only=True, allow_null=True
    )
    curso_nome = serializers.CharField(source="curso.nome", read_only=True)
    area_nome = serializers.CharField(source="area_conhecimento.nome", read_only=True)

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


class HistoricoStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoStatus
        fields = ["status", "data_alteracao", "justificativa"]


class TCCDetalheSerializer(TCCSerializer):
    """Detalhe do TCC: inclui o historico de situacao, do mais novo ao mais antigo."""

    historico = HistoricoStatusSerializer(
        source="historico_status", many=True, read_only=True
    )

    class Meta(TCCSerializer.Meta):
        fields = [*TCCSerializer.Meta.fields, "historico"]


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


# ---------------------------------------------------------------- Banca
class CadastrarBancaSerializer(serializers.Serializer):
    tcc = serializers.PrimaryKeyRelatedField(queryset=TCC.objects.all())
    titulares = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), many=True
    )
    suplentes = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), many=True, required=False
    )
    data_hora = serializers.DateTimeField()
    tipo_local = serializers.ChoiceField(choices=TipoLocal.choices)
    local = serializers.CharField(max_length=300)


class ParticipacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParticipacaoBanca
        fields = ["usuario", "tipo_membro", "presente"]


class BancaSerializer(serializers.ModelSerializer):
    participacoes = ParticipacaoSerializer(many=True, read_only=True)

    class Meta:
        model = Banca
        fields = ["id", "tcc", "data_hora", "tipo_local", "local", "participacoes"]


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
