from __future__ import annotations

import json
import os
import sys
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

    def assist_clinical_chat(
        self,
        *,
        clinical_context: str,
        messages_history: list[dict[str, str]],
    ) -> str:
        raise NotImplementedError


class DisabledLlmAdapter(BaseLlmAdapter):
    def analyze_anamnesis(self, payload: AnamnesisPromptPayload) -> LlmAnamnesisResult:
        raise LlmIntegrationUnavailable('O adaptador de LLM externo está desativado.')

    def assist_clinical_chat(
        self,
        *,
        clinical_context: str,
        messages_history: list[dict[str, str]],
    ) -> str:
        raise LlmIntegrationUnavailable('O adaptador de LLM externo está desativado.')


class SandboxLlmAdapter(BaseLlmAdapter):
    """Adaptador simulado de anamnese e apoio clínico para desenvolvimento e testes do MVP."""

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

    def assist_clinical_chat(
        self,
        *,
        clinical_context: str,
        messages_history: list[dict[str, str]],
    ) -> str:
        qtd = len(messages_history)
        return (
            f'[Apoio IA Sandbox] Contexto revisado ({qtd} mensagem(ns) no chat). '
            'Pontos sugeridos para investigação clínica: confirmar evolução dos sintomas, '
            'sinais de alarme (dispneia, dor torácica, rebaixamento do sensório), '
            'aderência a medicamentos contínuos e histórico de alergias antes de definir conduta.'
        )


class GeminiLlmAdapter(BaseLlmAdapter):
    """Cliente REST sobre HTTPS para Google Gemini API com payload desidentificado (ADR 0003).

    A IA atua exclusivamente como apoio à anamnese e síntese de chat; nunca escolhe
    a cor de Manchester nem emite prescrição autônoma.
    """

    BASE_URL = 'https://generativelanguage.googleapis.com/v1beta/models'
    FALLBACK_MODELS = ('gemini-3-flash-preview', 'gemini-flash-latest', 'gemini-flash-lite-latest')

    def _call_gemini(self, *, system_instruction: str, user_prompt: str, json_mode: bool) -> str:
        api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        configured_model = (
            getattr(settings, 'GEMINI_MODEL', '')
            or os.environ.get('GEMINI_MODEL', 'gemini-3-flash-preview')
        ).strip()
        timeout_seconds = getattr(settings, 'MEDIX_LLM_TIMEOUT_SECONDS', 20.0)

        if not api_key:
            raise LlmIntegrationUnavailable('Configure GEMINI_API_KEY no arquivo .env para usar o Gemini.')

        generation_config: dict = {'temperature': 0.2}
        if json_mode:
            generation_config['responseMimeType'] = 'application/json'

        body_dict = {
            'systemInstruction': {'parts': [{'text': system_instruction}]},
            'contents': [{'role': 'user', 'parts': [{'text': user_prompt}]}],
            'generationConfig': generation_config,
        }
        body = json.dumps(body_dict).encode('utf-8')

        candidatos = [configured_model] + [m for m in self.FALLBACK_MODELS if m != configured_model]
        dados = None
        ultimo_erro: Exception | None = None
        for model in candidatos:
            endpoint = f'{self.BASE_URL}/{model}:generateContent'
            req = urllib.request.Request(
                endpoint,
                data=body,
                method='POST',
                headers={
                    'Content-Type': 'application/json',
                    'x-goog-api-key': api_key,
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                    dados = json.loads(resp.read().decode('utf-8'))
                    break
            except urllib.error.HTTPError as erro:
                ultimo_erro = erro
                if erro.code in {404, 429, 503}:
                    continue
                raise LlmIntegrationUnavailable('Falha ao consultar a API do Google Gemini.') from erro
            except (urllib.error.URLError, TimeoutError, ValueError) as erro:
                ultimo_erro = erro
                continue

        if dados is None:
            raise LlmIntegrationUnavailable('Falha ao consultar a API do Google Gemini.') from ultimo_erro

        try:
            return str(dados['candidates'][0]['content']['parts'][0]['text']).strip()
        except (KeyError, IndexError, TypeError) as erro:
            raise LlmIntegrationUnavailable('Resposta inesperada da API do Google Gemini.') from erro

    def analyze_anamnesis(self, payload: AnamnesisPromptPayload) -> LlmAnamnesisResult:
        system_prompt = (
            'Você é um assistente de triagem clínica em português do Brasil para o sistema MEDIX.AI. '
            'Os dados recebidos são desidentificados (sem nome nem CPF). '
            'Sua função é APENAS estruturar um resumo objetivo, sugerir 2 perguntas adaptativas relevantes '
            'considerando o perfil clínico, fornecer orientação geral segura e, somente para casos leves '
            'compatíveis, indicar uma classe medicamentosa genérica sujeita à validação médica '
            '(ou string vazia se não aplicável). '
            'NUNCA dê diagnóstico definitivo, NUNCA escolha cor de Manchester e NUNCA prescreva receita. '
            'Responda estritamente em JSON com as chaves: '
            '"summary" (string), "adaptive_questions" (lista de 2 strings), '
            '"suggested_medication" (string), "guidance_text" (string).'
        )
        user_prompt = json.dumps(payload.to_dict(), ensure_ascii=False)
        raw_text = self._call_gemini(
            system_instruction=system_prompt,
            user_prompt=user_prompt,
            json_mode=True,
        )
        try:
            dados = json.loads(raw_text)
        except ValueError as erro:
            raise LlmIntegrationUnavailable('JSON inválido retornado pelo Gemini.') from erro

        perguntas = [str(q).strip() for q in dados.get('adaptive_questions', []) if str(q).strip()][:2]
        if not perguntas:
            perguntas = ['Os sintomas pioram ao esforço ou em repouso?']

        return LlmAnamnesisResult(
            summary=str(dados.get('summary', '')).strip(),
            adaptive_questions=perguntas,
            suggested_medication=str(dados.get('suggested_medication', '')).strip()[:200],
            guidance_text=str(dados.get('guidance_text', '')).strip(),
        )

    def assist_clinical_chat(
        self,
        *,
        clinical_context: str,
        messages_history: list[dict[str, str]],
    ) -> str:
        system_prompt = (
            'Você é um copiloto clínico de apoio ao médico em português do Brasil no MEDIX.AI. '
            'Todos os dados enviados são desidentificados. '
            'Produza uma síntese objetiva em tópicos curtos (máximo 6 linhas) destacando: '
            '1) resumo da evolução no chat, 2) possíveis sinais de alarme a investigar, '
            '3) atenção a alergias/comorbidades informadas. '
            'Não substitua o julgamento médico nem emita prescrição.'
        )
        user_prompt = json.dumps(
            {
                'clinical_context': clinical_context,
                'messages': messages_history[-20:],
            },
            ensure_ascii=False,
        )
        return self._call_gemini(
            system_instruction=system_prompt,
            user_prompt=user_prompt,
            json_mode=False,
        )


class HttpsRestLlmAdapter(BaseLlmAdapter):
    """Cliente REST genérico sobre HTTPS com JSON estruturado (ADR 0003)."""

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

    def assist_clinical_chat(
        self,
        *,
        clinical_context: str,
        messages_history: list[dict[str, str]],
    ) -> str:
        raise LlmIntegrationUnavailable('Apoio de chat não configurado neste adaptador genérico.')


def get_llm_adapter() -> BaseLlmAdapter:
    backend_path = getattr(settings, 'MEDIX_LLM_BACKEND', '')
    if not backend_path:
        em_teste = 'test' in sys.argv
        api_key = getattr(settings, 'GEMINI_API_KEY', '') or os.environ.get('GEMINI_API_KEY', '')
        backend_path = (
            'core.integrations.llm.GeminiLlmAdapter'
            if (api_key and not em_teste)
            else 'core.integrations.llm.SandboxLlmAdapter'
        )
    adapter_cls = import_string(backend_path)
    return adapter_cls()
