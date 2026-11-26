from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    REQUIRED_FIELDS = ['email', 'cpf', 'role']

    class Role(models.TextChoices):
        PATIENT = 'patient', 'Paciente/responsável'
        PROFESSIONAL = 'professional', 'Médico'
        ADMINISTRATOR = 'administrator', 'Administrador'

    email = models.EmailField('e-mail', unique=True)
    cpf = models.CharField('CPF', max_length=11, unique=True)
    role = models.CharField(
        'papel',
        max_length=20,
        choices=Role.choices,
    )
    failed_login_attempts = models.PositiveSmallIntegerField(
        'tentativas de login malsucedidas',
        default=0,
    )
    locked_until = models.DateTimeField('bloqueado até', blank=True, null=True)
    must_change_password = models.BooleanField(
        'deve trocar a senha no próximo acesso',
        default=False,
    )

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self) -> str:
        return self.get_full_name() or self.email
