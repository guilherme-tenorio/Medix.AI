from __future__ import annotations

import smtplib
from datetime import datetime, timedelta
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core.integrations.email import EmailIntegrationDisabled
from core.integrations.sms import SmsIntegrationDisabled, get_sms_adapter
from users.services import UserService

from .models import NotificationOutbox, NotificationPreference

PUSH_FALLBACK_SECONDS = 30


class PermissaoNotificacaoNegada(Exception):
    pass


class NotificacaoService:
    @staticmethod
    def obter_ou_criar_preferencias(user_id: int) -> NotificationPreference:
        pref, _ = NotificationPreference.objects.get_or_create(user_id=user_id)
        return pref

    @classmethod
    def atualizar_preferencias(cls, user_id: int, dados: dict) -> NotificationPreference:
        pref = cls.obter_ou_criar_preferencias(user_id)
        pref.allow_push = bool(dados.get('allow_push', pref.allow_push))
        pref.allow_sms = bool(dados.get('allow_sms', pref.allow_sms))
        pref.allow_email = bool(dados.get('allow_email', pref.allow_email))
        pref.allow_whatsapp = bool(dados.get('allow_whatsapp', pref.allow_whatsapp))
        pref.allow_informative = bool(dados.get('allow_informative', pref.allow_informative))
        pref.save()
        return pref

    @staticmethod
    def _canal_habilitado(pref: NotificationPreference, channel: str) -> bool:
        mapa = {
            NotificationOutbox.Channel.PUSH: pref.allow_push,
            NotificationOutbox.Channel.SMS: pref.allow_sms,
            NotificationOutbox.Channel.EMAIL: pref.allow_email,
            NotificationOutbox.Channel.WHATSAPP: pref.allow_whatsapp,
        }
        return mapa.get(channel, False)

    @classmethod
    def enviar_notificacao(
        cls,
        recipient_id: int,
        *,
        event_key: str,
        title: str,
        masked_body: str,
        channel: str = NotificationOutbox.Channel.PUSH,
        priority: str = NotificationOutbox.Priority.INFORMATIVE,
        deep_link: str = '',
        phone: str = '',
    ) -> NotificationOutbox | None:
        titulo = (title or '').strip()
        corpo = (masked_body or '').strip()
        link = (deep_link or '').strip()

        if not titulo or len(titulo) > 80:
            raise ValidationError('O título da notificação deve ter entre 1 e 80 caracteres.')
        if not corpo or len(corpo) > 300:
            raise ValidationError('A mensagem mascarada deve ter entre 1 e 300 caracteres.')
        if len(link) > 200:
            raise ValidationError('O link profundo deve ter no máximo 200 caracteres.')
        if channel not in NotificationOutbox.Channel.values:
            raise ValidationError('Canal de notificação inválido.')
        if priority not in NotificationOutbox.Priority.values:
            raise ValidationError('Prioridade de notificação inválida.')

        # Eventos urgentes nunca são descartados por preferência do usuário (Spec 0013).
        if priority != NotificationOutbox.Priority.URGENT:
            pref = cls.obter_ou_criar_preferencias(recipient_id)
            if priority == NotificationOutbox.Priority.INFORMATIVE and not pref.allow_informative:
                return None
            if not cls._canal_habilitado(pref, channel):
                return None

        notificacao, criada = NotificationOutbox.objects.get_or_create(
            event_key=event_key,
            defaults={
                'recipient_id': recipient_id,
                'channel': channel,
                'priority': priority,
                'subject': titulo,
                'body': corpo,
                'deep_link': link,
            },
        )
        if not criada:
            return notificacao

        if channel == NotificationOutbox.Channel.EMAIL:
            cls.despachar_email(notificacao.pk)
        elif channel == NotificationOutbox.Channel.SMS:
            cls._despachar_sms(notificacao, phone=phone)
        else:
            # Push e WhatsApp em modo sandbox/MVP marcam envio imediato.
            notificacao.status = NotificationOutbox.Status.SENT
            notificacao.sent_at = timezone.now()
            notificacao.save(update_fields=('status', 'sent_at'))
        notificacao.refresh_from_db()
        return notificacao

    @staticmethod
    def _despachar_sms(notificacao: NotificationOutbox, *, phone: str = '') -> bool:
        destino = (phone or '').strip()
        if not destino:
            paciente = getattr(notificacao.recipient, 'patient_profile', None)
            medico = getattr(notificacao.recipient, 'professional_profile', None)
            if paciente is not None:
                destino = paciente.phone
            elif medico is not None:
                destino = medico.operational_phone or medico.phone
        try:
            get_sms_adapter().send_sms(destino or '00000000000', notificacao.body)
        except SmsIntegrationDisabled:
            return False
        notificacao.status = NotificationOutbox.Status.SENT
        notificacao.sent_at = timezone.now()
        notificacao.save(update_fields=('status', 'sent_at'))
        return True

    @classmethod
    def verificar_e_disparar_fallback_sms(
        cls,
        notificacao_id: UUID,
        *,
        phone: str = '',
    ) -> NotificationOutbox | None:
        notificacao = (
            NotificationOutbox.objects.select_related('recipient')
            .filter(
                pk=notificacao_id,
                channel=NotificationOutbox.Channel.PUSH,
                read_at__isnull=True,
                fallback_triggered_at__isnull=True,
            )
            .first()
        )
        if notificacao is None:
            return None

        referencia = notificacao.sent_at or notificacao.created_at
        if timezone.now() - referencia < timedelta(seconds=PUSH_FALLBACK_SECONDS):
            return None

        fallback_key = f'{notificacao.event_key}:sms-fallback'
        sms_fallback = cls.enviar_notificacao(
            notificacao.recipient_id,
            event_key=fallback_key,
            title=notificacao.subject,
            masked_body=notificacao.body,
            channel=NotificationOutbox.Channel.SMS,
            priority=NotificationOutbox.Priority.URGENT,
            deep_link=notificacao.deep_link,
            phone=phone,
        )
        notificacao.status = NotificationOutbox.Status.FALLBACK_SENT
        notificacao.fallback_triggered_at = timezone.now()
        notificacao.save(update_fields=('status', 'fallback_triggered_at'))
        return sms_fallback

    @staticmethod
    def marcar_como_lida(user_id: int, notificacao_id: UUID) -> NotificationOutbox:
        notificacao = NotificationOutbox.objects.filter(
            pk=notificacao_id,
            recipient_id=user_id,
        ).first()
        if notificacao is None:
            raise PermissaoNotificacaoNegada
        if notificacao.read_at is None:
            notificacao.read_at = timezone.now()
            if notificacao.status == NotificationOutbox.Status.SENT:
                notificacao.status = NotificationOutbox.Status.READ
            notificacao.save(update_fields=('read_at', 'status'))
        return notificacao

    @staticmethod
    def limpar_informativas_lidas(user_id: int) -> int:
        # Limpa da central apenas notificações informativas já lidas; críticas permanecem visíveis e auditáveis.
        return NotificationOutbox.objects.filter(
            recipient_id=user_id,
            priority=NotificationOutbox.Priority.INFORMATIVE,
            read_at__isnull=False,
            dismissed_from_center=False,
        ).update(dismissed_from_center=True)

    @staticmethod
    def listar_central_usuario(user_id: int) -> QuerySet[NotificationOutbox]:
        return NotificationOutbox.objects.filter(
            recipient_id=user_id,
            dismissed_from_center=False,
        ).order_by('-created_at')

    @staticmethod
    def pesquisar_historico_admin(
        actor_id: int,
        *,
        recipient_id: int | None = None,
        channel: str = '',
        status: str = '',
        occurred_from: datetime | None = None,
        occurred_until: datetime | None = None,
    ) -> QuerySet[NotificationOutbox]:
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoNotificacaoNegada
        qs = NotificationOutbox.objects.select_related('recipient').order_by('-created_at')
        if recipient_id is not None:
            qs = qs.filter(recipient_id=recipient_id)
        if channel:
            qs = qs.filter(channel=channel)
        if status:
            qs = qs.filter(status=status)
        if occurred_from:
            qs = qs.filter(created_at__gte=occurred_from)
        if occurred_until:
            qs = qs.filter(created_at__lte=occurred_until)
        return qs

    @staticmethod
    def enfileirar_alerta_bloqueio_login(usuario_id: int, tentativa_id: int) -> NotificationOutbox:
        notificacao, criada = NotificationOutbox.objects.get_or_create(
            event_key=f'login-lockout:{tentativa_id}',
            defaults={
                'recipient_id': usuario_id,
                'channel': NotificationOutbox.Channel.EMAIL,
                'priority': NotificationOutbox.Priority.URGENT,
                'subject': 'Alerta de segurança da conta MEDIX.AI',
                'body': 'A conta foi bloqueada temporariamente após várias tentativas de acesso. Se você não reconhece essa atividade, proteja sua conta.',
            },
        )
        if criada:
            transaction.on_commit(
                lambda: NotificacaoService.despachar_email(notificacao.pk),
                robust=True,
            )
        return notificacao

    @staticmethod
    def despachar_email(notificacao_id: UUID) -> bool:
        notificacao = NotificationOutbox.objects.select_related('recipient').filter(
            pk=notificacao_id,
            channel=NotificationOutbox.Channel.EMAIL,
            status=NotificationOutbox.Status.PENDING,
        ).first()
        if notificacao is None:
            return False

        try:
            enviada = send_mail(
                notificacao.subject,
                notificacao.body,
                settings.DEFAULT_FROM_EMAIL,
                [notificacao.recipient.email],
                fail_silently=False,
            )
        except EmailIntegrationDisabled:
            return False
        except (OSError, smtplib.SMTPException):
            notificacao.status = NotificationOutbox.Status.FAILED
            notificacao.save(update_fields=('status',))
            return False

        if not enviada:
            notificacao.status = NotificationOutbox.Status.FAILED
            notificacao.save(update_fields=('status',))
            return False

        notificacao.status = NotificationOutbox.Status.SENT
        notificacao.sent_at = timezone.now()
        notificacao.save(update_fields=('status', 'sent_at'))
        return True
