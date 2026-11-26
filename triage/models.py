import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q


class TriageSession(models.Model):
    class RiskColor(models.TextChoices):
        WHITE = 'white', 'Branca'
        GREEN = 'green', 'Verde'
        YELLOW = 'yellow', 'Amarela'
        ORANGE = 'orange', 'Laranja'
        RED = 'red', 'Vermelha'

    class RoutingDestination(models.TextChoices):
        AI_GUIDANCE = 'ai_guidance', 'Orientação da IA'
        PRESCRIPTION_REVIEW = 'prescription_review', 'Fila de revisão médica'
        SYNCHRONOUS_CHAT = 'synchronous_chat', 'Fila de chat síncrono'
        EMERGENCY = 'emergency', 'Encaminhamento de emergência'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='triages',
        verbose_name='paciente titular',
    )
    dependent = models.ForeignKey(
        'patients.Dependent',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='triages',
        verbose_name='dependente',
    )
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='triages_initiated',
        verbose_name='iniciada por',
    )
    symptoms_description = models.TextField('relato de sintomas')
    symptom_onset = models.CharField('início/duração do sintoma', max_length=120)
    pain_intensity = models.PositiveSmallIntegerField('intensidade (0 a 10)')
    answers = models.JSONField('respostas da anamnese', default=dict)
    ai_summary = models.TextField('resumo clínico', blank=True)
    ai_guidance_text = models.TextField('orientação da IA', blank=True)
    suggested_medication = models.CharField('sugestão medicamentosa', max_length=200, blank=True)
    red_flags_detected = models.JSONField('red flags detectadas', default=list)
    risk_color = models.CharField(
        'classificação Manchester',
        max_length=12,
        choices=RiskColor.choices,
        blank=True,
    )
    routing_destination = models.CharField(
        'encaminhamento',
        max_length=24,
        choices=RoutingDestination.choices,
        blank=True,
    )
    is_completed = models.BooleanField('concluída', default=False)
    completed_at = models.DateTimeField('concluída em', blank=True, null=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'triagem'
        verbose_name_plural = 'triagens'
        ordering = ('-created_at',)
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(patient__isnull=False) & Q(dependent__isnull=True))
                    | (Q(patient__isnull=True) & Q(dependent__isnull=False))
                ),
                name='triage_exactly_one_subject',
            ),
            models.CheckConstraint(
                condition=Q(pain_intensity__gte=0) & Q(pain_intensity__lte=10),
                name='triage_pain_intensity_0_10',
            ),
        ]

    def __str__(self) -> str:
        alvo = self.patient or self.dependent
        cor = self.get_risk_color_display() if self.risk_color else 'Em andamento'
        return f'Triagem {self.pk} ({alvo}) — {cor}'


class EmergencyDispatch(models.Model):
    class TriggerSource(models.TextChoices):
        TRIAGE = 'triage', 'Triagem Vermelha'
        CHAT_RECLASSIFICATION = 'chat_reclassification', 'Reclassificação no chat'
        PRESCRIPTION_RECLASSIFICATION = 'prescription_reclassification', 'Reclassificação na revisão'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_session = models.ForeignKey(
        TriageSession,
        on_delete=models.PROTECT,
        related_name='emergency_dispatches',
        verbose_name='triagem',
    )
    trigger_source = models.CharField(
        'origem do gatilho',
        max_length=32,
        choices=TriggerSource.choices,
    )
    alert_message = models.CharField('alerta urgente', max_length=500)
    patient_summary = models.JSONField('ficha resumida do paciente')
    latitude = models.DecimalField('latitude', max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField('longitude', max_digits=9, decimal_places=6, blank=True, null=True)
    manual_location_query = models.CharField('busca manual de localização', max_length=120, blank=True)
    created_at = models.DateTimeField('registrado em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'encaminhamento de emergência'
        verbose_name_plural = 'encaminhamentos de emergência'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Emergência {self.pk} — {self.get_trigger_source_display()}'
