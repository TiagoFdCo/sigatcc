# C9 (3.2): com os dados preenchidos pela 0005, torna obrigatorio o que o
# DER v2 exige, remove BANCA.local (substituido por bloco, sala e link_remoto)
# e cria as restricoes novas.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def restaurar_local_da_banca(apps, schema_editor):
    """Volta da migration: remonta BANCA.local a partir de bloco, sala e link."""
    Banca = apps.get_model("core", "Banca")
    for banca in Banca.objects.all():
        if banca.tipo_local == "REMOTO":
            banca.local = banca.link_remoto or ""
        else:
            banca.local = f"Sala {banca.sala or ''}, bloco {banca.bloco or ''}"
        banca.save(update_fields=["local"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_modelo_v2_dados"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historicostatus",
            name="alterado_por",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="alteracoes_status",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # BANCA.local: fica opcional, e remontado se a migration for desfeita
        # e so entao sai do modelo
        migrations.AlterField(
            model_name="banca",
            name="local",
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.RunPython(migrations.RunPython.noop, restaurar_local_da_banca),
        migrations.RemoveField(
            model_name="banca",
            name="local",
        ),
        migrations.AddConstraint(
            model_name="banca",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("tipo_local", "PRESENCIAL"), _negated=True),
                    models.Q(("bloco__isnull", False), ("sala__isnull", False)),
                    _connector="OR",
                ),
                name="ck_banca_presencial_bloco_sala",
            ),
        ),
        migrations.AddConstraint(
            model_name="banca",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    models.Q(("tipo_local", "REMOTO"), _negated=True),
                    ("link_remoto__isnull", False),
                    _connector="OR",
                ),
                name="ck_banca_remota_link",
            ),
        ),
        migrations.AddConstraint(
            model_name="publicacao",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("comprovante_arquivo_path__isnull", False),
                    ("link_artigo__isnull", False),
                    _connector="OR",
                ),
                name="ck_publicacao_comprovante_ou_link",
            ),
        ),
        migrations.AddConstraint(
            model_name="avaliacao",
            constraint=models.CheckConstraint(
                condition=models.Q(("nota__gte", 0), ("nota__lte", 10)),
                name="ck_avaliacao_nota_0_10",
            ),
        ),
        migrations.AddConstraint(
            model_name="reuniaoalinhamento",
            constraint=models.CheckConstraint(
                condition=models.Q(("tipo_local__in", ["PRESENCIAL", "REMOTO"])),
                name="ck_reuniao_tipo_local",
            ),
        ),
    ]
