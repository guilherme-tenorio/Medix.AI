from __future__ import annotations

import logging

from django.conf import settings
from django.utils.module_loading import import_string

logger = logging.getLogger('medix.integrations.sms')


class SmsIntegrationDisabled(RuntimeError):
    """Indica que nenhum provedor de SMS foi configurado para o MEDIX.AI."""


class BaseSmsAdapter:
    def send_verification_code(self, phone: str, code: str) -> bool:
        raise NotImplementedError

    def send_sms(self, phone: str, message: str) -> bool:
        raise NotImplementedError


class DisabledSmsAdapter(BaseSmsAdapter):
    def send_verification_code(self, phone: str, code: str) -> bool:
        raise SmsIntegrationDisabled('O adaptador de SMS está desativado.')

    def send_sms(self, phone: str, message: str) -> bool:
        raise SmsIntegrationDisabled('O adaptador de SMS está desativado.')


class SandboxSmsAdapter(BaseSmsAdapter):
    """Adaptador simulado de SMS para desenvolvimento e testes do MVP acadêmico."""

    sent_codes: dict[str, str] = {}
    sent_messages: list[tuple[str, str]] = []

    def send_verification_code(self, phone: str, code: str) -> bool:
        SandboxSmsAdapter.sent_codes[phone] = code
        logger.info('Sandbox SMS enviado para ****%s', phone[-4:])
        return True

    def send_sms(self, phone: str, message: str) -> bool:
        SandboxSmsAdapter.sent_messages.append((phone, message))
        logger.info('Sandbox SMS de notificação enviado para ****%s', phone[-4:])
        return True


def get_sms_adapter() -> BaseSmsAdapter:
    backend_path = getattr(
        settings,
        'MEDIX_SMS_BACKEND',
        'core.integrations.sms.SandboxSmsAdapter',
    )
    adapter_cls = import_string(backend_path)
    return adapter_cls()
