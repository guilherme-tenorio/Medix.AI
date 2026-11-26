from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from core.integrations.geolocation import EmergencyUnit, get_hospital_directory_adapter
from core.integrations.llm import (
    AnamnesisPromptPayload,
    LlmIntegrationUnavailable,
    get_llm_adapter,
)
from patients.models import ClinicalProfile, Dependent, PatientProfile
from patients.services import (
    DependentService,
    DependenteNaoEncontrado,
    PatientService,
    PermissaoPacienteNegada,
)

from .models import EmergencyDispatch, TriageSession


class PermissaoTriagemNegada(Exception):
    pass


class TriagemNaoEncontrada(Exception):
    pass


class TriagemImutavel(Exception):
    pass


class TriagemIndisponivel(Exception):
    pass


class EmergenciaNaoEncontrada(Exception):
    pass


@dataclass(frozen=True, slots=True)
class TriageSubjectInfo:
    patient: PatientProfile | None
    dependent: Dependent | None
    full_name: str
    age_years: int
    relationship_label: str
    gender: str
    clinical_profile: ClinicalProfile


@dataclass(frozen=True, slots=True)
class ManchesterResult:
    risk_color: str
    red_flags: list[str]
    routing_destination: str


def _calcular_idade(birth_date: date) -> int:
    hoje = timezone.localdate()
    anos = hoje.year - birth_date.year
    if (hoje.month, hoje.day) < (birth_date.month, birth_date.day):
        anos -= 1
    return max(anos, 0)


def _faixa_etaria(idade: int) -> str:
    if idade < 2:
        return 'lactente (0-1 ano)'
    if idade < 12:
        return 'crianca (2-11 anos)'
    if idade < 18:
        return 'adolescente (12-17 anos)'
    if idade < 60:
        return 'adulto (18-59 anos)'
    return 'idoso (60+ anos)'


class ManchesterClassifierService:
    """Classificador determinístico baseado no Protocolo de Manchester (5 cores).

    A IA nunca escolhe nem altera a cor de risco. Red flags determinísticas têm
    prioridade absoluta sobre qualquer fila virtual.
    """

    RED_FLAG_KEYWORDS: tuple[tuple[str, str], ...] = (
        ('dor no peito', 'Dor torácica intensa / suspeita cardiovascular'),
        ('dor toracica', 'Dor torácica intensa / suspeita cardiovascular'),
        ('falta de ar intensa', 'Insuficiência respiratória aguda'),
        ('nao consigo respirar', 'Insuficiência respiratória aguda'),
        ('não consigo respirar', 'Insuficiência respiratória aguda'),
        ('desmaio', 'Síncope / perda de consciência'),
        ('perda de consciencia', 'Síncope / perda de consciência'),
        ('perda de consciência', 'Síncope / perda de consciência'),
        ('convulsao', 'Crise convulsiva'),
        ('convulsão', 'Crise convulsiva'),
        ('sangramento intenso', 'Hemorragia grave'),
        ('hemorragia', 'Hemorragia grave'),
        ('paralisia', 'Déficit neurológico agudo / suspeita de AVC'),
        ('boca torta', 'Déficit neurológico agudo / suspeita de AVC'),
        ('fala enrolada', 'Déficit neurológico agudo / suspeita de AVC'),
        ('ideacao suicida', 'Risco imediato à integridade / crise aguda'),
        ('ideação suicida', 'Risco imediato à integridade / crise aguda'),
    )

    ORANGE_KEYWORDS: tuple[str, ...] = (
        'febre alta',
        'falta de ar',
        'falta de ar moderada',
        'vomito persistente',
        'vômito persistente',
        'dor abdominal forte',
        'tontura intensa',
        'pressao muito alta',
        'pressão muito alta',
    )

    YELLOW_KEYWORDS: tuple[str, ...] = (
        'febre',
        'dor persistente',
        'infec',
        'infecção',
        'garganta inflamada',
        'tosse persistente',
        'diarreia',
    )

    @classmethod
    def detectar_red_flags(cls, texto_combinado: str) -> list[str]:
        normalizado = (texto_combinado or '').casefold()
        detectadas: list[str] = []
        for termo, descricao in cls.RED_FLAG_KEYWORDS:
            if termo in normalizado and descricao not in detectadas:
                detectadas.append(descricao)
        return detectadas

    @staticmethod
    def _contem_keyword_positiva(texto: str, keywords: tuple[str, ...]) -> bool:
        for termo in keywords:
            if termo in texto and f'sem {termo}' not in texto and f'não tem {termo}' not in texto and f'nao tem {termo}' not in texto:
                return True
        return False

    @classmethod
    def classificar(
        cls,
        *,
        symptoms_description: str,
        answers: dict,
        pain_intensity: int,
        suggested_medication: str = '',
        has_comorbidity: bool = False,
    ) -> ManchesterResult:
        respostas_texto = ' '.join(str(v) for v in (answers or {}).values())
        texto_total = f'{symptoms_description} {respostas_texto}'.casefold()

        red_flags = cls.detectar_red_flags(texto_total)
        if red_flags:
            return ManchesterResult(
                risk_color=TriageSession.RiskColor.RED,
                red_flags=red_flags,
                routing_destination=TriageSession.RoutingDestination.EMERGENCY,
            )

        if pain_intensity >= 8 or cls._contem_keyword_positiva(texto_total, cls.ORANGE_KEYWORDS):
            return ManchesterResult(
                risk_color=TriageSession.RiskColor.ORANGE,
                red_flags=[],
                routing_destination=TriageSession.RoutingDestination.SYNCHRONOUS_CHAT,
            )

        if (
            pain_intensity >= 5
            or cls._contem_keyword_positiva(texto_total, cls.YELLOW_KEYWORDS)
            or (has_comorbidity and pain_intensity >= 4)
        ):
            return ManchesterResult(
                risk_color=TriageSession.RiskColor.YELLOW,
                red_flags=[],
                routing_destination=TriageSession.RoutingDestination.SYNCHRONOUS_CHAT,
            )

        if pain_intensity >= 2:
            cor = TriageSession.RiskColor.GREEN
        else:
            cor = TriageSession.RiskColor.WHITE

        destino = (
            TriageSession.RoutingDestination.PRESCRIPTION_REVIEW
            if (suggested_medication or '').strip()
            else TriageSession.RoutingDestination.AI_GUIDANCE
        )
        return ManchesterResult(
            risk_color=cor,
            red_flags=[],
            routing_destination=destino,
        )


class EmergencyService:
    DEFAULT_ALERT_MESSAGE = (
        'EMERGÊNCIA MÉDICA DETECTADA: procure imediatamente o pronto-socorro mais próximo '
        'ou acione o serviço de emergência local (SAMU 192 / Bombeiros 193).'
    )

    @staticmethod
    def _montar_ficha_resumida(triage_session: TriageSession) -> dict:
        if triage_session.patient_id is not None:
            paciente = triage_session.patient
            perfil = paciente.clinical_profile
            nome = paciente.user.get_full_name() or paciente.user.email
            idade = _calcular_idade(paciente.birth_date)
        else:
            dependente = triage_session.dependent
            perfil = dependente.clinical_profile
            nome = dependente.full_name
            idade = _calcular_idade(dependente.birth_date)

        comorbidades: list[str] = []
        if perfil.has_hypertension:
            comorbidades.append('Hipertensão')
        if perfil.has_diabetes:
            comorbidades.append('Diabetes')
        if perfil.has_disability and perfil.disability_description:
            comorbidades.append(f'Deficiência: {perfil.disability_description}')

        return {
            'nome': nome,
            'idade': idade,
            'tipo_sanguineo': perfil.blood_type,
            'alergias': perfil.allergy_description if perfil.has_allergy else 'Nenhuma informada',
            'comorbidades': comorbidades,
            'sintomas': triage_session.symptoms_description[:300],
            'red_flags': list(triage_session.red_flags_detected or []),
        }

    @classmethod
    def registrar_emergencia(
        cls,
        triage_session: TriageSession,
        *,
        trigger_source: str,
        alert_message: str = '',
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        manual_location_query: str = '',
    ) -> EmergencyDispatch:
        mensagem = (alert_message or cls.DEFAULT_ALERT_MESSAGE).strip()[:500]
        ficha = cls._montar_ficha_resumida(triage_session)
        return EmergencyDispatch.objects.create(
            triage_session=triage_session,
            trigger_source=trigger_source,
            alert_message=mensagem,
            patient_summary=ficha,
            latitude=latitude,
            longitude=longitude,
            manual_location_query=(manual_location_query or '').strip()[:120],
        )

    @classmethod
    def obter_emergencia_autorizada(cls, user_id: int, dispatch_id: UUID) -> EmergencyDispatch:
        dispatch = (
            EmergencyDispatch.objects.select_related(
                'triage_session',
                'triage_session__patient__user',
                'triage_session__patient__clinical_profile',
                'triage_session__dependent__guardian__user',
                'triage_session__dependent__clinical_profile',
            )
            .filter(pk=dispatch_id)
            .first()
        )
        if dispatch is None:
            raise EmergenciaNaoEncontrada

        triagem = dispatch.triage_session
        dono_id = (
            triagem.patient.user_id
            if triagem.patient_id is not None
            else triagem.dependent.guardian.user_id
        )
        if dono_id != user_id and triagem.initiated_by_id != user_id:
            raise PermissaoTriagemNegada
        return dispatch

    @classmethod
    def buscar_unidades_proximas(cls, dispatch: EmergencyDispatch) -> list[EmergencyUnit]:
        adapter = get_hospital_directory_adapter()
        lat = float(dispatch.latitude) if dispatch.latitude is not None else None
        lon = float(dispatch.longitude) if dispatch.longitude is not None else None
        return adapter.find_nearby(
            latitude=lat,
            longitude=lon,
            manual_query=dispatch.manual_location_query,
        )

    @classmethod
    def atualizar_localizacao(
        cls,
        user_id: int,
        dispatch_id: UUID,
        *,
        latitude: Decimal | None = None,
        longitude: Decimal | None = None,
        manual_location_query: str = '',
    ) -> tuple[EmergencyDispatch, list[EmergencyUnit]]:
        dispatch = cls.obter_emergencia_autorizada(user_id, dispatch_id)
        if (latitude is None) != (longitude is None):
            raise ValidationError('Informe latitude e longitude juntas ou utilize a busca manual.')

        dispatch.latitude = latitude
        dispatch.longitude = longitude
        dispatch.manual_location_query = (manual_location_query or '').strip()[:120]
        dispatch.save(update_fields=('latitude', 'longitude', 'manual_location_query'))
        unidades = cls.buscar_unidades_proximas(dispatch)
        return dispatch, unidades


class TriageService:
    @staticmethod
    def obter_alvo_autorizado(
        user_id: int,
        *,
        dependent_id: int | None = None,
    ) -> TriageSubjectInfo:
        paciente = PatientService.obter_perfil_por_usuario(user_id)
        if paciente is None:
            raise PermissaoTriagemNegada

        if dependent_id is None:
            if not hasattr(paciente, 'clinical_profile'):
                raise ValidationError('Complete os dados clínicos do perfil antes de iniciar a triagem.')
            return TriageSubjectInfo(
                patient=paciente,
                dependent=None,
                full_name=paciente.user.get_full_name() or paciente.user.email,
                age_years=_calcular_idade(paciente.birth_date),
                relationship_label='Titular',
                gender=paciente.gender,
                clinical_profile=paciente.clinical_profile,
            )

        try:
            dependente = DependentService.obter_dependente(user_id, dependent_id)
        except (PermissaoPacienteNegada, DependenteNaoEncontrado) as erro:
            raise PermissaoTriagemNegada from erro

        if not hasattr(dependente, 'clinical_profile'):
            raise ValidationError('Complete os dados clínicos do dependente antes de iniciar a triagem.')

        return TriageSubjectInfo(
            patient=None,
            dependent=dependente,
            full_name=dependente.full_name,
            age_years=_calcular_idade(dependente.birth_date),
            relationship_label=dependente.get_legal_relationship_display(),
            gender=dependente.gender,
            clinical_profile=dependente.clinical_profile,
        )

    @staticmethod
    def montar_payload_desidentificado(
        sujeito: TriageSubjectInfo,
        *,
        symptoms_description: str,
        symptom_onset: str,
        pain_intensity: int,
    ) -> AnamnesisPromptPayload:
        perfil = sujeito.clinical_profile
        return AnamnesisPromptPayload(
            age_group=_faixa_etaria(sujeito.age_years),
            gender=sujeito.gender,
            symptoms_description=symptoms_description,
            symptom_onset=symptom_onset,
            pain_intensity=pain_intensity,
            allergies=perfil.allergy_description if perfil.has_allergy else '',
            has_hypertension=perfil.has_hypertension,
            has_diabetes=perfil.has_diabetes,
            continuous_medications=perfil.continuous_medications,
        )

    @classmethod
    def iniciar_triagem(
        cls,
        user_id: int,
        *,
        symptoms_description: str,
        symptom_onset: str,
        pain_intensity: int,
        dependent_id: int | None = None,
        identity_confirmed: bool = False,
    ) -> tuple[TriageSession, EmergencyDispatch | None]:
        if not identity_confirmed:
            raise ValidationError('Confirme o nome, a idade e o vínculo do paciente antes de iniciar a triagem.')

        relato = (symptoms_description or '').strip()
        inicio = (symptom_onset or '').strip()
        if len(relato) < 5:
            raise ValidationError('Descreva os sintomas com pelo menos 5 caracteres.')
        if not inicio or len(inicio) > 120:
            raise ValidationError('Informe o início ou duração do sintoma (até 120 caracteres).')
        if pain_intensity < 0 or pain_intensity > 10:
            raise ValidationError('A intensidade deve estar entre 0 e 10.')

        sujeito = cls.obter_alvo_autorizado(user_id, dependent_id=dependent_id)

        # Red flags determinísticas têm prioridade absoluta e interrompem o fluxo comum imediatamente.
        red_flags_iniciais = ManchesterClassifierService.detectar_red_flags(relato)
        if red_flags_iniciais:
            with transaction.atomic():
                sessao = TriageSession.objects.create(
                    patient=sujeito.patient,
                    dependent=sujeito.dependent,
                    initiated_by_id=user_id,
                    symptoms_description=relato,
                    symptom_onset=inicio,
                    pain_intensity=pain_intensity,
                    answers={'questions': [], 'responses': {}},
                    ai_summary=f'Alerta imediato de emergência por red flag: {", ".join(red_flags_iniciais)}.',
                    red_flags_detected=red_flags_iniciais,
                    risk_color=TriageSession.RiskColor.RED,
                    routing_destination=TriageSession.RoutingDestination.EMERGENCY,
                    is_completed=True,
                    completed_at=timezone.now(),
                )
                dispatch = EmergencyService.registrar_emergencia(
                    sessao,
                    trigger_source=EmergencyDispatch.TriggerSource.TRIAGE,
                )
                return sessao, dispatch

        payload = cls.montar_payload_desidentificado(
            sujeito,
            symptoms_description=relato,
            symptom_onset=inicio,
            pain_intensity=pain_intensity,
        )
        try:
            resultado_ia = get_llm_adapter().analyze_anamnesis(payload)
        except LlmIntegrationUnavailable as erro:
            raise TriagemIndisponivel(
                'Serviço de triagem assistida temporariamente indisponível. '
                'Em caso de urgência, procure atendimento presencial imediatamente.',
            ) from erro

        sessao = TriageSession.objects.create(
            patient=sujeito.patient,
            dependent=sujeito.dependent,
            initiated_by_id=user_id,
            symptoms_description=relato,
            symptom_onset=inicio,
            pain_intensity=pain_intensity,
            answers={
                'questions': list(resultado_ia.adaptive_questions),
                'responses': {},
            },
            ai_summary=resultado_ia.summary,
            ai_guidance_text=resultado_ia.guidance_text,
            suggested_medication=resultado_ia.suggested_medication[:200],
            is_completed=False,
        )
        return sessao, None

    @classmethod
    def concluir_triagem(
        cls,
        user_id: int,
        triage_id: UUID,
        *,
        responses: dict[str, str],
    ) -> tuple[TriageSession, EmergencyDispatch | None]:
        with transaction.atomic():
            sessao = (
                TriageSession.objects.select_for_update(of=('self',))
                .select_related(
                    'patient__user',
                    'patient__clinical_profile',
                    'dependent__guardian__user',
                    'dependent__clinical_profile',
                )
                .filter(pk=triage_id)
                .first()
            )
            if sessao is None:
                raise TriagemNaoEncontrada

            dono_id = (
                sessao.patient.user_id
                if sessao.patient_id is not None
                else sessao.dependent.guardian.user_id
            )
            if dono_id != user_id and sessao.initiated_by_id != user_id:
                raise PermissaoTriagemNegada

            if sessao.is_completed:
                raise TriagemImutavel('Triagem concluída é imutável. Inicie uma nova triagem se necessário.')

            perfil_clinico = (
                sessao.patient.clinical_profile
                if sessao.patient_id is not None
                else sessao.dependent.clinical_profile
            )
            has_comorbidity = bool(
                perfil_clinico.has_hypertension or perfil_clinico.has_diabetes
            )

            respostas_limpas = {
                str(k): str(v).strip()
                for k, v in (responses or {}).items()
                if str(v).strip()
            }
            resultado_manchester = ManchesterClassifierService.classificar(
                symptoms_description=sessao.symptoms_description,
                answers=respostas_limpas,
                pain_intensity=sessao.pain_intensity,
                suggested_medication=sessao.suggested_medication,
                has_comorbidity=has_comorbidity,
            )

            answers_payload = dict(sessao.answers or {})
            answers_payload['responses'] = respostas_limpas

            sessao.answers = answers_payload
            sessao.red_flags_detected = resultado_manchester.red_flags
            sessao.risk_color = resultado_manchester.risk_color
            sessao.routing_destination = resultado_manchester.routing_destination
            sessao.is_completed = True
            sessao.completed_at = timezone.now()
            sessao.save(
                update_fields=(
                    'answers',
                    'red_flags_detected',
                    'risk_color',
                    'routing_destination',
                    'is_completed',
                    'completed_at',
                ),
            )

            dispatch = None
            if sessao.risk_color == TriageSession.RiskColor.RED:
                dispatch = EmergencyService.registrar_emergencia(
                    sessao,
                    trigger_source=EmergencyDispatch.TriggerSource.TRIAGE,
                )
            elif sessao.routing_destination in {
                TriageSession.RoutingDestination.SYNCHRONOUS_CHAT,
                TriageSession.RoutingDestination.PRESCRIPTION_REVIEW,
            }:
                from care.services import QueueService

                QueueService.enfileirar_triagem(sessao)
            return sessao, dispatch

    @classmethod
    def obter_triagem(cls, user_id: int, triage_id: UUID) -> TriageSession:
        sessao = (
            TriageSession.objects.select_related(
                'patient__user',
                'patient__clinical_profile',
                'dependent__guardian__user',
                'dependent__clinical_profile',
            )
            .filter(pk=triage_id)
            .first()
        )
        if sessao is None:
            raise TriagemNaoEncontrada

        dono_id = (
            sessao.patient.user_id
            if sessao.patient_id is not None
            else sessao.dependent.guardian.user_id
        )
        if dono_id != user_id and sessao.initiated_by_id != user_id:
            raise PermissaoTriagemNegada
        return sessao

    @classmethod
    def obter_contexto_detalhe(cls, user_id: int, triage_id: UUID) -> dict:
        sessao = cls.obter_triagem(user_id, triage_id)
        return {
            'sessao': sessao,
            'perguntas': (sessao.answers or {}).get('questions', []),
            'chat_session': sessao.chat_sessions.order_by('-created_at').first(),
            'emergency_dispatch': sessao.emergency_dispatches.order_by('-created_at').first(),
            'digital_prescription': sessao.digital_prescriptions.order_by('-issued_at').first(),
        }

    @classmethod
    def listar_triagens_usuario(cls, user_id: int) -> QuerySet[TriageSession]:
        return (
            TriageSession.objects.select_related('patient__user', 'dependent')
            .filter(
                Q(patient__user_id=user_id)
                | Q(dependent__guardian__user_id=user_id)
                | Q(initiated_by_id=user_id)
            )
            .order_by('-created_at')
        )
