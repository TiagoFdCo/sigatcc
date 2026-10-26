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


def so_digitos(valor):
    return re.sub(r"\D", "", valor or "")


def cpf_valido(cpf):
    """Confere os dois digitos verificadores do CPF (11 digitos, sem mascara)."""
    if len(cpf) != 11 or not cpf.isdigit() or cpf == cpf[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(cpf[i]) * (n + 1 - i) for i in range(n))
        if (soma * 10) % 11 % 10 != int(cpf[n]):
            return False
    return True


def mascarar_cpf(cpf):
    """RNF12: o CPF completo nunca sai pela API; so os digitos do meio."""
    if not cpf or len(cpf) != 11:
        return None
    return f"***.{cpf[3:6]}.{cpf[6:9]}-**"
