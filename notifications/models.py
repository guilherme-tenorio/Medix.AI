import uuid

from django.conf import settings
from django.db import models


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='notification_preference',
        verbose_name='usuário',
    )
    allow_push = models.BooleanField('Web Push', default=True)
    allow_sms = models.BooleanField('SMS', default=True)
    allow_email = models.BooleanField('E-mail', default=True)
    allow_whatsapp = models.BooleanField('WhatsApp', default=False)
    allow_informative = models.BooleanField('receber avisos informativos', default=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'preferência de notificação'
        verbose_name_plural = 'preferências de notificação'

    def __str__(self) -> str:
        return f'Preferências de {self.user}'


class NotificationOutbox(models.Model):
    class Channel(models.TextChoices):
        EMAIL = 'email', 'E-mail'
        PUSH = 'push', 'Web Push'
        SMS = 'sms', 'SMS'
        WHATSAPP = 'whatsapp', 'WhatsApp'

    class Priority(models.TextChoices):
        INFORMATIVE = 'informative', 'Informativo'
        MODERATE = 'moderate', 'Moderado'
        URGENT = 'urgent', 'Urgente'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Aguardando integração'
        SENT = 'sent', 'Enviada'
        READ = 'read', 'Lida'
        FAILED = 'failed', 'Falha'
        FALLBACK_SENT = 'fallback_sent', 'Fallback SMS enviado'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_key = models.CharField('chave do evento', max_length=120, unique=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='notification_outbox',
        verbose_name='destinatário',
    )
    channel = models.CharField('canal', max_length=12, choices=Channel.choices)
    priority = models.CharField(
        'prioridade',
        max_length=16,
        choices=Priority.choices,
        default=Priority.INFORMATIVE,
        db_index=True,
    )
    subject = models.CharField('assunto', max_length=80)
    body = models.CharField('mensagem', max_length=300)
    deep_link = models.CharField('link profundo', max_length=200, blank=True)
    status = models.CharField(
        'status',
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    dismissed_from_center = models.BooleanField('oculta da central', default=False)
    created_at = models.DateTimeField('criada em', auto_now_add=True, db_index=True)
    sent_at = models.DateTimeField('enviada em', blank=True, null=True)
    read_at = models.DateTimeField('lida em', blank=True, null=True)
    fallback_triggered_at = models.DateTimeField('fallback SMS em', blank=True, null=True)

    class Meta:
        verbose_name = 'notificação'
        verbose_name_plural = 'notificações'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'{self.get_channel_display()} — {self.event_key}'
