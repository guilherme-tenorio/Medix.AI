from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from audit.models import LoginAttempt
from audit.services import AuditService
from notifications.models import NotificationOutbox
from notifications.services import NotificacaoService
from users.models import User


class NotificationOutboxTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.usuario = User.objects.create_user(
            username='notif-user',
            email='notif@example.test',
            cpf='12345678909',
            role=User.Role.PATIENT,
            password='SenhaPaciente9!',
        )
        cls.tentativa = AuditService.registrar_tentativa_login(
            '12345678909',
            LoginAttempt.Result.LOCKED,
            cls.usuario,
            User.Role.PATIENT,
        )

    @override_settings(EMAIL_BACKEND='core.integrations.email.DisabledEmailBackend')
    def test_backend_desligado_mantem_notificacao_pendente(self) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            notificacao = NotificacaoService.enfileirar_alerta_bloqueio_login(
                self.usuario.pk,
                self.tentativa.pk,
            )
        notificacao.refresh_from_db()
        self.assertEqual(notificacao.status, NotificationOutbox.Status.PENDING)
        self.assertIsNone(notificacao.sent_at)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_backend_ativo_envia_e_marca_como_enviada(self) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            notificacao = NotificacaoService.enfileirar_alerta_bloqueio_login(
                self.usuario.pk,
                self.tentativa.pk,
            )
        notificacao.refresh_from_db()
        self.assertEqual(notificacao.status, NotificationOutbox.Status.SENT)
        self.assertIsNotNone(notificacao.sent_at)
        self.assertEqual(len(mail.outbox), 1)

    def test_preferencias_fallback_sms_30s_e_limpeza_preserva_urgentes(self) -> None:
        # Desativar avisos informativos impede envio informativo, mas não urgente
        NotificacaoService.atualizar_preferencias(
            self.usuario.pk,
            {'allow_informative': False, 'allow_push': True, 'allow_sms': True},
        )
        suprimida = NotificacaoService.enviar_notificacao(
            self.usuario.pk,
            event_key='info-suprimida',
            title='Lembrete',
            masked_body='Você tem uma atualização disponível no portal.',
            channel=NotificationOutbox.Channel.PUSH,
            priority=NotificationOutbox.Priority.INFORMATIVE,
        )
        self.assertIsNone(suprimida)

        # Urgente é enviada mesmo com informativos desativados
        urgente = NotificacaoService.enviar_notificacao(
            self.usuario.pk,
            event_key='chamada-medica-1',
            title='Atendimento médico disponível',
            masked_body='Seu médico iniciou o atendimento. Acesse o portal com segurança.',
            channel=NotificationOutbox.Channel.PUSH,
            priority=NotificationOutbox.Priority.URGENT,
            deep_link='/chat/123/',
        )
        self.assertIsNotNone(urgente)

        # Simular passagem de 35s sem leitura -> dispara fallback SMS
        NotificationOutbox.objects.filter(pk=urgente.pk).update(
            sent_at=timezone.now() - timedelta(seconds=35),
        )
        fallback = NotificacaoService.verificar_e_disparar_fallback_sms(
            urgente.pk,
            phone='11999990000',
        )
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback.channel, NotificationOutbox.Channel.SMS)
        urgente.refresh_from_db()
        self.assertEqual(urgente.status, NotificationOutbox.Status.FALLBACK_SENT)

        # Reativar informativos, criar informativa lida e urgente lida -> limpar remove só informativa da central
        NotificacaoService.atualizar_preferencias(self.usuario.pk, {'allow_informative': True})
        info = NotificacaoService.enviar_notificacao(
            self.usuario.pk,
            event_key='info-limpavel',
            title='Aviso',
            masked_body='Atualização cadastral confirmada.',
            channel=NotificationOutbox.Channel.PUSH,
            priority=NotificationOutbox.Priority.INFORMATIVE,
        )
        NotificacaoService.marcar_como_lida(self.usuario.pk, info.pk)
        NotificacaoService.marcar_como_lida(self.usuario.pk, urgente.pk)

        removidas = NotificacaoService.limpar_informativas_lidas(self.usuario.pk)
        self.assertEqual(removidas, 1)
        # Registro continua no banco (auditoria imutável)
        self.assertTrue(NotificationOutbox.objects.filter(pk=info.pk).exists())
        # Urgente continua na central
        central_ids = set(
            NotificacaoService.listar_central_usuario(self.usuario.pk).values_list('pk', flat=True)
        )
        self.assertIn(urgente.pk, central_ids)
        self.assertNotIn(info.pk, central_ids)
