"""C5: confere o envio de e-mail (SPF/DKIM) e mede a taxa de entrega (RNF07).

Uso:
    python manage.py enviar_email_teste --para voce@exemplo.com
    python manage.py enviar_email_teste --para voce@exemplo.com --quantidade 20
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.services import email


class Command(BaseCommand):
    help = "Envia e-mail(s) de teste pelo backend configurado (Resend em produção)."

    def add_arguments(self, parser):
        parser.add_argument("--para", required=True, help="Destinatário do teste")
        parser.add_argument(
            "--quantidade", type=int, default=1, help="Quantos e-mails (RNF07)"
        )

    def handle(self, *args, para, quantidade, **options):
        if quantidade < 1:
            raise CommandError("--quantidade precisa ser pelo menos 1.")
        self.stdout.write(f"Backend: {settings.EMAIL_BACKEND}")
        aceitos = 0
        for n in range(1, quantidade + 1):
            ok = email.enviar_agora(
                para=[para],
                assunto=f"Teste de envio {n}/{quantidade}",
                texto=(
                    "Este é um e-mail de teste do SIGATCC.\n\n"
                    f"Enviado em {timezone.localtime():%d/%m/%Y %H:%M:%S}. "
                    "Se chegou na caixa de entrada (e não no spam), SPF e DKIM "
                    "estão funcionando."
                ),
            )
            aceitos += ok
        self.stdout.write(
            self.style.SUCCESS(f"{aceitos} de {quantidade} aceito(s) pelo servidor.")
        )
        if aceitos < quantidade:
            raise CommandError("Houve falha no envio. Veja o log acima.")
