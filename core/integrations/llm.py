from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings
from django.utils.module_loading import import_string


class LlmIntegrationUnavailable(RuntimeError):
    """Indica indisponibilidade ou timeout do provedor externo de LLM."""


@dataclass(frozen=True, slots=True)
class AnamnesisPromptPayload:
    """Payload estritamente desidentificado conforme ADR 0003 (sem nome ou CPF)."""

    age_group: str
    gender: str
    symptoms_description: str
    symptom_onset: str
    pain_intensity: int
    allergies: str
    has_hypertension: bool
    has_diabetes: bool
    continuous_medications: str

    def to_dict(self) -> dict:
        return {
            'age_group': self.age_group,
            'gender': self.gender,
            'symptoms_description': self.symptoms_description,
            'symptom_onset': self.symptom_onset,
            'pain_intensity': self.pain_intensity,
            'allergies': self.allergies,
            'has_hypertension': self.has_hypertension,
            'has_diabetes': self.has_diabetes,
            'continuous_medications': self.continuous_medications,
        }


@dataclass(frozen=True, slots=True)
class LlmAnamnesisResult:
    summary: str
    adaptive_questions: list[str]
    suggested_medication: str = ''
    guidance_text: str = ''


class BaseLlmAdapter:
    def analyze_anamnesis(self, payload: AnamnesisPromptPayload) -> LlmAnamnesisResult:
        raise NotImplementedError


class DisabledLlmAdapter(BaseLlmAdapter):
    def analyze_anamnesis(self, payload: AnamnesisPromptPayload) -> LlmAnamnesisResult:
        raise LlmIntegrationUnavailable('O adaptador de LLM externo está desativado.')


class SandboxLlmAdapter(BaseLlmAdapter):
    """Adaptador simulado de anamnese para desenvolvimento e MVP acadêmico."""

    def analyze_anamnesis(self, payload: AnamnesisPromptPayload) -> LlmAnamnesisResult:
        resumo = (
            f'Paciente ({payload.age_group}, {payload.gender}) relata: '
            f'{payload.symptoms_description[:200]} (início/duração: {payload.symptom_onset}, '
            f'intensidade {payload.pain_intensity}/10).'
        )
        perguntas = [
            'Os sintomas pioram ao esforço ou em repouso?',
            'Houve febre aferida ou outros sintomas associados nas últimas 24 horas?',
        ]
        texto_sintomas = payload.symptoms_description.casefold()
        sugestao = ''
        orientacao = 'Mantenha hidratação adequada, repouso e observe evolução dos sintomas.'
        if payload.pain_intensity <= 5 and any(
            termo in texto_sintomas for termo in ('dor de cabeça', 'cefaleia', 'febre leve')
        ):
            sugestao = 'Analgésico/antitérmico simples sujeito à validação médica'
        return LlmAnamnesisResult(
            summary=resumo,
            adaptive_questions=perguntas,
            suggested_medication=sugestao,
            guidance_text=orientacao,
        )


class HttpsRestLlmAdapter(BaseLlmAdapter):
    """Cliente REST sobre HTTPS com JSON estruturado (ADR 0003)."""

    def analyze_anamnesis(self, payload: AnamnesisPromptPayload) -> LlmAnamnesisResult:
        endpoint = getattr(settings, 'MEDIX_LLM_ENDPOINT_URL', '')
        api_key = getattr(settings, 'MEDIX_LLM_API_KEY', '')
        timeout_seconds = getattr(settings, 'MEDIX_LLM_TIMEOUT_SECONDS', 4.5)
        if not endpoint or not endpoint.startswith('https://') or not api_key:
            raise LlmIntegrationUnavailable('Endpoint HTTPS ou chave do provedor LLM não configurados.')

        body = json.dumps(payload.to_dict()).encode('utf-8')
        req = urllib.request.Request(
            endpoint,
            data=body,
            method='POST',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                dados = json.loads(resp.read().decode('utf-8'))
        except (urllib.error.URLError, TimeoutError, ValueError) as erro:
            raise LlmIntegrationUnavailable('Falha ao consultar provedor externo de LLM.') from erro

        return LlmAnamnesisResult(
            summary=str(dados.get('summary', '')),
            adaptive_questions=list(dados.get('adaptive_questions', [])),
            suggested_medication=str(dados.get('suggested_medication', '')),
            guidance_text=str(dados.get('guidance_text', '')),
        )


def get_llm_adapter() -> BaseLlmAdapter:
    backend_path = getattr(
        settings,
        'MEDIX_LLM_BACKEND',
        'core.integrations.llm.SandboxLlmAdapter',
    )
    adapter_cls = import_string(backend_path)
    return adapter_cls()
