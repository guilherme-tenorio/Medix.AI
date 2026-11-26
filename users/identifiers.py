import re

from django.core.exceptions import ValidationError


def normalizar_identificador(identificador: str) -> str:
    valor = identificador.strip()
    if re.fullmatch(r'[\d\s.-]+', valor):
        cpf = ''.join(caractere for caractere in valor if caractere.isdigit())
        if len(cpf) == 11:
            return cpf
    return valor.casefold()


def validar_cpf(valor: str) -> str:
    digitos = ''.join(caractere for caractere in (valor or '') if caractere.isdigit())
    if len(digitos) != 11 or len(set(digitos)) == 1:
        raise ValidationError('Informe um CPF válido.', code='invalid_cpf')

    for indice in (9, 10):
        soma = sum(int(digitos[pos]) * ((indice + 1) - pos) for pos in range(indice))
        resto = (soma * 10) % 11
        digito_esperado = 0 if resto == 10 else resto
        if int(digitos[indice]) != digito_esperado:
            raise ValidationError('Informe um CPF válido.', code='invalid_cpf')

    return digitos


def normalizar_celular(valor: str) -> str:
    digitos = ''.join(caractere for caractere in (valor or '') if caractere.isdigit())
    if len(digitos) not in {10, 11} or digitos.startswith('0'):
        raise ValidationError(
            'Informe um número de celular brasileiro válido com DDD.',
            code='invalid_phone',
        )
    return digitos
