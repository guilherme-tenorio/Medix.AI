import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class MedicalRecordAmendment(models.Model):
    class EventType(models.TextChoices):
        TRIAGE = 'triage', 'Triagem'
        REVIEW = 'review', 'Parecer / Revisão'
        CHAT = 'chat', 'Atendimento por chat'
        PRESCRIPTION = 'prescription', 'Receita digital'
        EMERGENCY = 'emergency', 'Emergência'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='record_amendments',
        verbose_name='paciente titular',
    )
    dependent = models.ForeignKey(
        'patients.Dependent',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='record_amendments',
        verbose_name='dependente',
    )
    target_event_type = models.CharField(
        'tipo do evento original',
        max_length=16,
        choices=EventType.choices,
    )
    target_event_id = models.UUIDField('ID do evento original', db_index=True)
    recorded_by = models.ForeignKey(
        'professionals.ProfessionalProfile',
        on_delete=models.PROTECT,
        related_name='record_amendments',
        verbose_name='médico responsável',
    )
    amendment_text = models.TextField('texto da retificação clínica')
    created_at = models.DateTimeField('registrado em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'retificação de prontuário'
        verbose_name_plural = 'retificações de prontuário'
        ordering = ('-created_at',)
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(patient__isnull=False) & Q(dependent__isnull=True))
                    | (Q(patient__isnull=True) & Q(dependent__isnull=False))
                ),
                name='record_amendment_exactly_one_subject',
            ),
        ]

    def __str__(self) -> str:
        return f'Retificação {self.pk} ({self.get_target_event_type_display()})'


class MedicalRecordAccessLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='medical_record_accesses',
        verbose_name='usuário',
    )
    crm_snapshot = models.CharField('CRM no momento do acesso', max_length=32, blank=True)
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='access_logs',
        verbose_name='paciente titular',
    )
    dependent = models.ForeignKey(
        'patients.Dependent',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='access_logs',
        verbose_name='dependente',
    )
    allowed = models.BooleanField('acesso permitido', db_index=True)
    reason = models.CharField('motivo/detalhe', max_length=200, blank=True)
    ip_address = models.GenericIPAddressField('endereço IP', blank=True, null=True)
    accessed_at = models.DateTimeField('acessado em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'registro de acesso a prontuário'
        verbose_name_plural = 'registros de acesso a prontuário'
        ordering = ('-accessed_at',)

    def __str__(self) -> str:
        status = 'Permitido' if self.allowed else 'Negado'
        return f'Acesso {status} por {self.actor_id} em {self.accessed_at}'
