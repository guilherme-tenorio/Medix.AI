import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from triage.models import TriageSession


class ClinicalQueueItem(models.Model):
    class QueueType(models.TextChoices):
        SYNCHRONOUS_CHAT = 'synchronous_chat', 'Fila de chat síncrono'
        PRESCRIPTION_REVIEW = 'prescription_review', 'Fila de revisão de prescrição'

    class Status(models.TextChoices):
        WAITING = 'waiting', 'Aguardando Atendimento'
        IN_PROGRESS = 'in_progress', 'Em Atendimento'
        AWAITING_PRESCRIPTION = 'awaiting_prescription', 'Aguardando Validação de Receita'
        FINISHED = 'finished', 'Finalizado'

    PRIORITY_MAP = {
        TriageSession.RiskColor.ORANGE: 1,
        TriageSession.RiskColor.YELLOW: 2,
        TriageSession.RiskColor.GREEN: 3,
        TriageSession.RiskColor.WHITE: 4,
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_session = models.ForeignKey(
        TriageSession,
        on_delete=models.PROTECT,
        related_name='queue_items',
        verbose_name='triagem',
    )
    queue_type = models.CharField(
        'tipo de fila',
        max_length=24,
        choices=QueueType.choices,
        db_index=True,
    )
    risk_color = models.CharField(
        'cor Manchester',
        max_length=12,
        choices=TriageSession.RiskColor.choices,
        db_index=True,
    )
    priority_rank = models.PositiveSmallIntegerField('prioridade numérica', db_index=True)
    status = models.CharField(
        'status',
        max_length=24,
        choices=Status.choices,
        default=Status.WAITING,
        db_index=True,
    )
    assigned_professional = models.ForeignKey(
        'professionals.ProfessionalProfile',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='queue_items',
        verbose_name='médico responsável',
    )
    enqueued_at = models.DateTimeField('entrada na fila', auto_now_add=True, db_index=True)
    accepted_at = models.DateTimeField('aceito em', blank=True, null=True)
    finished_at = models.DateTimeField('finalizado em', blank=True, null=True)

    class Meta:
        verbose_name = 'chamado da fila clínica'
        verbose_name_plural = 'chamados da fila clínica'
        ordering = ('priority_rank', 'enqueued_at')
        constraints = [
            models.CheckConstraint(
                condition=~Q(risk_color=TriageSession.RiskColor.RED),
                name='queue_forbids_red_emergency_cases',
            ),
        ]

    def __str__(self) -> str:
        return f'Fila {self.get_queue_type_display()} — {self.get_risk_color_display()} ({self.get_status_display()})'


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    queue_item = models.OneToOneField(
        ClinicalQueueItem,
        on_delete=models.PROTECT,
        related_name='chat_session',
        verbose_name='chamado da fila',
    )
    triage_session = models.ForeignKey(
        TriageSession,
        on_delete=models.PROTECT,
        related_name='chat_sessions',
        verbose_name='triagem',
    )
    professional = models.ForeignKey(
        'professionals.ProfessionalProfile',
        on_delete=models.PROTECT,
        related_name='chat_sessions',
        verbose_name='médico',
    )
    is_closed = models.BooleanField('encerrada', default=False, db_index=True)
    closed_at = models.DateTimeField('encerrada em', blank=True, null=True)
    created_at = models.DateTimeField('criada em', auto_now_add=True)

    class Meta:
        verbose_name = 'sessão de chat médico'
        verbose_name_plural = 'sessões de chat médico'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Chat {self.pk} ({self.professional})'


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.PROTECT,
        related_name='messages',
        verbose_name='sessão de chat',
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='chat_messages_sent',
        verbose_name='remetente',
    )
    content = models.CharField('conteúdo', max_length=1000)
    is_from_audio_transcription = models.BooleanField('origem por transcrição de áudio', default=False)
    delivered_at = models.DateTimeField('entregue em', auto_now_add=True)
    read_at = models.DateTimeField('lida em', blank=True, null=True)
    created_at = models.DateTimeField('enviada em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'mensagem de chat'
        verbose_name_plural = 'mensagens de chat'
        ordering = ('created_at',)

    def __str__(self) -> str:
        return f'Mensagem {self.pk} em {self.session_id}'


class ChatAttachment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.PROTECT,
        related_name='attachments',
        verbose_name='mensagem',
    )
    file = models.FileField('arquivo', upload_to='care/chat_attachments/')
    original_name = models.CharField('nome original', max_length=255)
    content_type = models.CharField('tipo MIME', max_length=100)
    size_bytes = models.PositiveIntegerField('tamanho em bytes')
    uploaded_at = models.DateTimeField('enviado em', auto_now_add=True)

    class Meta:
        verbose_name = 'anexo de chat'
        verbose_name_plural = 'anexos de chat'
        ordering = ('uploaded_at',)

    def __str__(self) -> str:
        return self.original_name


class ClinicalOutcome(models.Model):
    class OutcomeType(models.TextChoices):
        GUIDANCE = 'guidance', 'Orientação clínica'
        PRESCRIPTION_ISSUED = 'prescription_issued', 'Encaminhado para receita'
        REFERRAL = 'referral', 'Encaminhamento presencial'
        EMERGENCY_RECLASSIFICATION = 'emergency_reclassification', 'Reclassificação de emergência (Vermelho)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat_session = models.OneToOneField(
        ChatSession,
        on_delete=models.PROTECT,
        related_name='clinical_outcome',
        verbose_name='sessão de chat',
    )
    outcome_type = models.CharField(
        'tipo de desfecho',
        max_length=32,
        choices=OutcomeType.choices,
    )
    summary_and_conduct = models.CharField('resumo e conduta clínica', max_length=1000)
    warning_signs = models.TextField('sinais de alerta', blank=True)
    reclassified_to_red = models.BooleanField('reclassificado para Vermelho', default=False)
    recorded_by = models.ForeignKey(
        'professionals.ProfessionalProfile',
        on_delete=models.PROTECT,
        related_name='clinical_outcomes',
        verbose_name='registrado por',
    )
    created_at = models.DateTimeField('registrado em', auto_now_add=True)

    class Meta:
        verbose_name = 'desfecho clínico'
        verbose_name_plural = 'desfechos clínicos'

    def __str__(self) -> str:
        return f'Desfecho {self.get_outcome_type_display()} ({self.chat_session_id})'
