from django.conf import settings
from django.db import models


class LoginAttempt(models.Model):
    class Role(models.TextChoices):
        PATIENT = 'patient', 'Paciente/responsável'
        PROFESSIONAL = 'professional', 'Médico'
        ADMINISTRATOR = 'administrator', 'Administrador'

    class Result(models.TextChoices):
        SUCCESS = 'success', 'Sucesso'
        INVALID_CREDENTIALS = 'invalid', 'Credenciais inválidas'
        LOCKED = 'locked', 'Conta temporariamente bloqueada'
        PORTAL_DENIED = 'portal_denied', 'Portal incompatível'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='login_attempts',
        verbose_name='usuário',
    )
    identifier_fingerprint = models.CharField('identificador protegido', max_length=64, db_index=True)
    role = models.CharField('perfil', max_length=20, choices=Role.choices, blank=True)
    result = models.CharField('resultado', max_length=20, choices=Result.choices)
    occurred_at = models.DateTimeField('ocorrido em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'tentativa de acesso'
        verbose_name_plural = 'tentativas de acesso'
        ordering = ('-occurred_at',)

    def __str__(self) -> str:
        return f'{self.get_result_display()} — {self.occurred_at:%Y-%m-%d %H:%M}'


class AuditQuery(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_queries',
        verbose_name='administrador',
    )
    ip_address = models.GenericIPAddressField('endereço IP', blank=True, null=True)
    identifier_fingerprint = models.CharField(
        'identificador pesquisado protegido',
        max_length=64,
        blank=True,
    )
    role_filter = models.CharField('perfil filtrado', max_length=20, blank=True)
    result_filter = models.CharField('resultado filtrado', max_length=20, blank=True)
    occurred_from = models.DateTimeField('período inicial', blank=True, null=True)
    occurred_until = models.DateTimeField('período final', blank=True, null=True)
    occurred_at = models.DateTimeField('consulta em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'consulta de auditoria'
        verbose_name_plural = 'consultas de auditoria'
        ordering = ('-occurred_at',)
        indexes = [
            models.Index(fields=('actor', '-occurred_at'), name='audit_query_actor_time_idx'),
        ]

    def __str__(self) -> str:
        return f'Consulta administrativa {self.pk} — {self.occurred_at:%Y-%m-%d %H:%M}'


class AdministrativeAction(models.Model):
    class Action(models.TextChoices):
        ADMIN_PASSWORD_RESET_REQUESTED = (
            'admin_password_reset_requested',
            'Redefinição de senha administrativa solicitada',
        )
        PROFESSIONAL_TEMP_PASSWORD_REQUESTED = (
            'professional_temp_password_requested',
            'Senha provisória médica solicitada',
        )
        USER_INACTIVATED = (
            'user_inactivated',
            'Conta de usuário inativada',
        )
        PROFESSIONAL_CREATED = (
            'professional_created',
            'Cadastro médico criado',
        )
        PROFESSIONAL_APPROVED = (
            'professional_approved',
            'Cadastro médico homologado',
        )
        PROFESSIONAL_SUSPENDED = (
            'professional_suspended',
            'Cadastro médico suspenso',
        )
        ADMIN_CREATED = (
            'admin_created',
            'Conta administrativa criada',
        )
        ADMIN_DEACTIVATED = (
            'admin_deactivated',
            'Conta administrativa desativada',
        )
        PRESCRIPTION_ISSUED = (
            'prescription_issued',
            'Receita digital emitida',
        )
        PRESCRIPTION_REVOKED = (
            'prescription_revoked',
            'Receita digital revogada',
        )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='administrative_actions_performed',
        verbose_name='administrador responsável',
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='administrative_actions_received',
        verbose_name='conta afetada',
    )
    action = models.CharField('ação', max_length=50, choices=Action.choices)
    ip_address = models.GenericIPAddressField('endereço IP', blank=True, null=True)
    occurred_at = models.DateTimeField('ocorrido em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'ação administrativa'
        verbose_name_plural = 'ações administrativas'
        ordering = ('-occurred_at',)
        indexes = [
            models.Index(fields=('actor', '-occurred_at'), name='audit_admin_action_actor_idx'),
            models.Index(fields=('target', '-occurred_at'), name='audit_admin_action_target_idx'),
        ]

    def __str__(self) -> str:
        return f'{self.get_action_display()} — {self.occurred_at:%Y-%m-%d %H:%M}'
