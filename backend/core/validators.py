import re

from django.core.exceptions import ValidationError


class SenhaForteValidator:
    """RBN29: a senha precisa de letra maiuscula, numero e caractere especial.

    O tamanho minimo (8) fica com o MinimumLengthValidator do Django.
    """

    def validate(self, password, user=None):
        faltando = []
        if not re.search(r"[A-Z]", password):
            faltando.append("uma letra maiúscula")
        if not re.search(r"\d", password):
            faltando.append("um número")
        if not re.search(r"[^A-Za-z0-9]", password):
            faltando.append("um caractere especial")
        if faltando:
            raise ValidationError(
                "A senha precisa ter " + ", ".join(faltando) + ".", code="senha_fraca"
            )

    def get_help_text(self):
        return (
            "A senha precisa ter ao menos uma letra maiúscula, um número "
            "e um caractere especial."
        )
