from django.contrib.auth.base_user import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class PasswordComplexityValidator:
    def validate(self, password: str, user: AbstractBaseUser | None = None) -> None:
        errors = []

        if not any(character.isupper() for character in password):
            errors.append(
                ValidationError(
                    _('A senha deve conter pelo menos uma letra maiúscula.'),
                    code='password_no_uppercase',
                )
            )
        if not any(character.isdigit() for character in password):
            errors.append(
                ValidationError(
                    _('A senha deve conter pelo menos um número.'),
                    code='password_no_number',
                )
            )
        if not any(not character.isalnum() for character in password):
            errors.append(
                ValidationError(
                    _('A senha deve conter pelo menos um símbolo.'),
                    code='password_no_symbol',
                )
            )

        if errors:
            raise ValidationError(errors)

    def get_help_text(self) -> str:
        return _('A senha deve conter uma letra maiúscula, um número e um símbolo.')
