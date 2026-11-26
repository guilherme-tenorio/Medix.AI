import logging

from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger('medix.integrations.email')


class EmailIntegrationDisabled(RuntimeError):
    """Indica que nenhum provedor de e-mail foi configurado para o MEDIX.AI."""


class DisabledEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages) -> int:
        if not email_messages:
            return 0
        raise EmailIntegrationDisabled('O adaptador de e-mail está desativado.')


class SandboxEmailBackend(BaseEmailBackend):
    """Adaptador simulado para envio de e-mails em desenvolvimento e MVP acadêmico."""

    def send_messages(self, email_messages) -> int:
        if not email_messages:
            return 0
        for message in email_messages:
            logger.info(
                'Sandbox email enviado para %s | assunto=%s',
                ', '.join(message.to),
                message.subject,
            )
        return len(email_messages)
