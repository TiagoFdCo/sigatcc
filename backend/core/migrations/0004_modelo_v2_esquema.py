# C9 (3.2): modelo de dados atualizado pelo DER v2 de 08/11 (D4, D5, D15, D16, D17).
#
# A mudanca vem em tres migrations, para nao perder dados e nao misturar
# ALTER TABLE com UPDATE na mesma transacao do PostgreSQL:
#   0004 (esta) cria as colunas novas, ainda opcionais, e renomeia data_hora;
#   0005 preenche as colunas novas a partir dos dados que ja existem;
#   0006 torna obrigatorio o que o DER exige, remove BANCA.local e cria as
#        restricoes novas.

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0003_logs_somente_acrescimo"),
    ]

    operations = [
        # HISTORICO_STATUS: quem mudou o status (fica obrigatorio na 0006)
        migrations.AddField(
            model_name="historicostatus",
            name="alterado_por",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="alteracoes_status",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        # PUBLICACAO: comprovante opcional (D15); a regra "comprovante ou link"
        # entra como restricao na 0006
        migrations.AlterField(
            model_name="publicacao",
            name="comprovante_arquivo_path",
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        # BANCA: inicio da defesa (D5) e local em bloco e sala ou link (D17)
        migrations.RenameField(
            model_name="banca",
            old_name="data_hora",
            new_name="data_hora_inicio",
        ),
        migrations.AddField(
            model_name="banca",
            name="bloco",
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AddField(
            model_name="banca",
            name="sala",
            field=models.CharField(blank=True, max_length=60, null=True),
        ),
        migrations.AddField(
            model_name="banca",
            name="link_remoto",
            field=models.URLField(blank=True, max_length=300, null=True),
        ),
        # AVALIACAO: nota de 0 a 10, parecer e data do lancamento (D4)
        migrations.AlterField(
            model_name="avaliacao",
            name="nota",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=4,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(10),
                ],
            ),
        ),
        migrations.AddField(
            model_name="avaliacao",
            name="parecer",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="avaliacao",
            name="lancada_em",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        # CONVITE: datas de envio e resposta (D16)
        migrations.AddField(
            model_name="convite",
            name="enviado_em",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="convite",
            name="respondido_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # SOLICITACAO_ORIENTACAO: mensagem e motivo opcionais, datas (D15, D16)
        migrations.RemoveConstraint(
            model_name="solicitacaoorientacao",
            name="ck_solicitacao_motivo_recusa",
        ),
        migrations.AlterField(
            model_name="solicitacaoorientacao",
            name="mensagem",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="solicitacaoorientacao",
            name="enviada_em",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name="solicitacaoorientacao",
            name="respondida_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        # REUNIAO_ALINHAMENTO: tipo de local; a 0005 corrige as remotas
        migrations.AddField(
            model_name="reuniaoalinhamento",
            name="tipo_local",
            field=models.CharField(
                choices=[("PRESENCIAL", "Presencial"), ("REMOTO", "Remoto")],
                default="PRESENCIAL",
                max_length=10,
            ),
            preserve_default=False,
        ),
    ]
