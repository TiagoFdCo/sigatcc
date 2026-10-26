from rest_framework import serializers

from core.models import (
    TCC,
    Banca,
    MotivoNaoApresentacao,
    ParticipacaoBanca,
    StatusTCC,
    TipoLocal,
    Usuario,
)


# ------------------------------------------------------------------ TCC
class TCCSerializer(serializers.ModelSerializer):
    class Meta:
        model = TCC
        fields = [
            "id",
            "titulo",
            "subtitulo",
            "curso",
            "area_conhecimento",
            "modalidade",
            "visibilidade",
            "status",
            "motivo_nao_apresentacao",
            "motivo_outro",
            "ativo",
            "data_cadastro",
            "autor",
            "orientador",
            "coorientador",
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
