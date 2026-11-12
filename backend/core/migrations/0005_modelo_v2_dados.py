# C9 (3.2): preenche as colunas criadas na 0004 com os dados que ja existem,
# para que a 0006 possa torna-las obrigatorias sem perder nada.

import re
from datetime import timedelta

from django.db import migrations

A_DEFINIR = "A definir"
TAMANHO_BLOCO_SALA = 60
TAMANHO_LINK = 300


def dividir_local(texto):
    """Separa o antigo BANCA.local ("Sala 10, bloco NUCOMP") em (bloco, sala).

    Reconhece as partes que comecam com "bloco" ou "sala"; o que sobra vai
    para o campo que ficou vazio. Sem nenhuma pista, o texto inteiro vira a
    sala e o bloco fica "A definir", para o docente corrigir depois.
    """
    texto = (texto or "").strip()
    partes = [p.strip() for p in re.split(r"[,;/]|\s-\s", texto) if p.strip()]
    bloco = sala = None
    resto = []
    for parte in partes:
        achou_bloco = re.match(r"^bloco\b\s*[:\-]?\s*(.+)$", parte, re.IGNORECASE)
        achou_sala = re.match(r"^sala\b\s*[:\-]?\s*(.+)$", parte, re.IGNORECASE)
        if achou_bloco and bloco is None:
            bloco = achou_bloco.group(1).strip()
        elif achou_sala and sala is None:
            sala = achou_sala.group(1).strip()
        else:
            resto.append(parte)
    sobra = ", ".join(resto) or None

    if bloco is None and sala is None:
        bloco, sala = A_DEFINIR, texto or A_DEFINIR
    elif bloco is None:
        bloco = sobra or A_DEFINIR
    elif sala is None:
        sala = sobra or A_DEFINIR
    return bloco[:TAMANHO_BLOCO_SALA], sala[:TAMANHO_BLOCO_SALA]


def preencher_local_da_banca(apps, schema_editor):
    Banca = apps.get_model("core", "Banca")
    for banca in Banca.objects.all():
        if banca.tipo_local == "REMOTO":
            banca.link_remoto = (banca.local or "").strip()[:TAMANHO_LINK]
            banca.bloco = banca.sala = None
        else:
            banca.bloco, banca.sala = dividir_local(banca.local)
            banca.link_remoto = None
        banca.save(update_fields=["bloco", "sala", "link_remoto"])


def preencher_alterado_por(apps, schema_editor):
    """Quem mudou o status: o responsavel do LOG_AUDITORIA gravado no mesmo
    instante; sem log, o orientador do TCC (DOCENTE.pk e o id do usuario)."""
    HistoricoStatus = apps.get_model("core", "HistoricoStatus")
    LogAuditoria = apps.get_model("core", "LogAuditoria")
    janela = timedelta(minutes=1)
    pendentes = HistoricoStatus.objects.filter(alterado_por__isnull=True)
    for item in pendentes.select_related("tcc"):
        log = (
            LogAuditoria.objects.filter(
                entidade="TCC",
                registro_id=item.tcc_id,
                campo="status",
                valor_novo=item.status,
                data_hora__gte=item.data_alteracao - janela,
                data_hora__lte=item.data_alteracao + janela,
            )
            .order_by("data_hora")
            .first()
        )
        item.alterado_por_id = log.responsavel_id if log else item.tcc.orientador_id
        item.save(update_fields=["alterado_por"])


def preencher_envio_dos_convites(apps, schema_editor):
    """Os convites nasceram com a banca: usa a data do log de cadastro da banca."""
    Banca = apps.get_model("core", "Banca")
    Convite = apps.get_model("core", "Convite")
    LogAuditoria = apps.get_model("core", "LogAuditoria")
    for banca_id in Banca.objects.filter(convites__isnull=False).values_list(
        "id", flat=True
    ).distinct():
        log = (
            LogAuditoria.objects.filter(entidade="BANCA", registro_id=banca_id)
            .order_by("data_hora")
            .first()
        )
        if log:
            Convite.objects.filter(banca_id=banca_id).update(enviado_em=log.data_hora)


def marcar_reunioes_remotas(apps, schema_editor):
    ReuniaoAlinhamento = apps.get_model("core", "ReuniaoAlinhamento")
    ReuniaoAlinhamento.objects.filter(local__istartswith="http").update(
        tipo_local="REMOTO"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_modelo_v2_esquema"),
    ]

    operations = [
        migrations.RunPython(preencher_local_da_banca, migrations.RunPython.noop),
        migrations.RunPython(preencher_alterado_por, migrations.RunPython.noop),
        migrations.RunPython(preencher_envio_dos_convites, migrations.RunPython.noop),
        migrations.RunPython(marcar_reunioes_remotas, migrations.RunPython.noop),
    ]
