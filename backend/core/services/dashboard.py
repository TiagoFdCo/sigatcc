from django.db.models import Count, Q

from core.models import TCC, Docente


def obter_metricas_dashboard(usuario):
    """Retorna os indicadores calculados conforme RBN20-RBN23 e RD19.

    Compatível com os perfis do C17.
    """
    # RBN20: TCCs em desenvolvimento
    em_desenvolvimento = TCC.objects.filter(status="EM_DESENVOLVIMENTO").count()

    # RBN21: Apresentados vs Não Apresentados
    apresentados = TCC.objects.filter(status="APRESENTADO").count()
    nao_apresentados = TCC.objects.filter(status="NAO_APRESENTADO").count()

    # RD19: Conclusão por Banca vs Conclusão por Publicação
    aprovados_publicacao = TCC.objects.filter(status="APROVADO_POR_PUBLICACAO").count()

    # RBN22: Carga de orientação por docente (usa usuario_id e usuario__nome_completo)
    orientacoes_por_docente = [
        {
            "id": str(d["usuario_id"]),
            "nome": d["usuario__nome_completo"],
            "qtd_orientacoes": d["qtd_orientacoes"],
        }
        for d in Docente.objects.annotate(
            qtd_orientacoes=Count(
                "tccs_orientados",
                filter=Q(tccs_orientados__status="EM_DESENVOLVIMENTO"),
            )
        ).values("usuario_id", "usuario__nome_completo", "qtd_orientacoes")
    ]

    # RBN23: Carga de bancas por docente
    bancas_por_docente = [
        {
            "id": str(d["usuario_id"]),
            "nome": d["usuario__nome_completo"],
            "qtd_bancas": d["qtd_bancas"],
        }
        for d in Docente.objects.annotate(
            qtd_bancas=Count("usuario__participacoes_banca")
        ).values("usuario_id", "usuario__nome_completo", "qtd_bancas")
    ]

    return {
        "em_desenvolvimento": em_desenvolvimento,
        "apresentados": apresentados,
        "nao_apresentados": nao_apresentados,
        "aprovados_publicacao": aprovados_publicacao,
        "orientacoes_por_docente": orientacoes_por_docente,
        "bancas_por_docente": bancas_por_docente,
    }
