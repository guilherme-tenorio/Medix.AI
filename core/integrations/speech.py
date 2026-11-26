from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string


class SpeechIntegrationDisabled(RuntimeError):
    """Indica que o adaptador de voz (STT/TTS) está desativado."""


@dataclass(frozen=True, slots=True)
class TranscriptionResult:
    text: str
    confidence: float
    needs_confirmation: bool
    audio_discarded: bool = True


class BaseSpeechAdapter:
    CONFIDENCE_THRESHOLD = 0.75

    def transcribe(self, audio_bytes: bytes, *, language: str = 'pt-BR') -> TranscriptionResult:
        raise NotImplementedError

    def synthesize(self, text: str, *, language: str = 'pt-BR') -> bytes | None:
        raise NotImplementedError


class DisabledSpeechAdapter(BaseSpeechAdapter):
    def transcribe(self, audio_bytes: bytes, *, language: str = 'pt-BR') -> TranscriptionResult:
        raise SpeechIntegrationDisabled('O adaptador de transcrição por voz está desativado.')

    def synthesize(self, text: str, *, language: str = 'pt-BR') -> bytes | None:
        raise SpeechIntegrationDisabled('O adaptador de síntese de voz está desativado.')


class SandboxSpeechAdapter(BaseSpeechAdapter):
    """Adaptador simulado para STT/TTS em pt-BR sem retenção de áudio bruto."""

    def transcribe(self, audio_bytes: bytes, *, language: str = 'pt-BR') -> TranscriptionResult:
        if not audio_bytes:
            return TranscriptionResult(
                text='',
                confidence=0.0,
                needs_confirmation=True,
                audio_discarded=True,
            )
        # Áudio bruto é descartado imediatamente após leitura em memória.
        del audio_bytes
        return TranscriptionResult(
            text='[Transcrição de áudio em pt-BR]',
            confidence=0.85,
            needs_confirmation=False,
            audio_discarded=True,
        )

    def synthesize(self, text: str, *, language: str = 'pt-BR') -> bytes | None:
        return None


def get_speech_adapter() -> BaseSpeechAdapter:
    backend_path = getattr(
        settings,
        'MEDIX_SPEECH_BACKEND',
        'core.integrations.speech.SandboxSpeechAdapter',
    )
    adapter_cls = import_string(backend_path)
    return adapter_cls()
