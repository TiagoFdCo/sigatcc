from rest_framework import serializers

from core.models import TCC


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
        # status so muda pela rota de situacao (B7b); curso vem do aluno
        read_only_fields = [
            "id",
            "curso",
            "status",
            "motivo_nao_apresentacao",
            "motivo_outro",
            "ativo",
            "data_cadastro",
        ]
