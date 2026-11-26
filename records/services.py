from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.utils import timezone

from care.models import ChatSession, ClinicalQueueItem
from patients.models import Dependent, PatientProfile
from prescriptions.models import DigitalPrescription, PrescriptionReview
from professionals.models import ProfessionalProfile
from triage.models import EmergencyDispatch, TriageSession

from .models import MedicalRecordAccessLog, MedicalRecordAmendment

User = get_user_model()
RETENTION_YEARS = 20


class PermissaoProntuarioNegada(Exception):
    pass


class ProntuarioNaoEncontrado(Exception):
    pass


@dataclass(frozen=True, slots=True)
class MedicalRecordEvent:
    event_id: UUID
    event_type: str
    event_type_label: str
    occurred_at: datetime
    risk_color: str
    risk_color_label: str
    professional_name: str
    summary: str
    amendments: list[MedicalRecordAmendment]


class MedicalRecordService:
    @staticmethod
    def _resolver_sujeito(
        *,
        patient_id: int | None = None,
        dependent_id: int | None = None,
    ) -> tuple[PatientProfile | None, Dependent | None]:
        if bool(patient_id) == bool(dependent_id):
            raise ValidationError('Selecione exatamente um paciente titular ou um dependente.')

        if patient_id is not None:
            paciente = PatientProfile.objects.select_related('user').filter(pk=patient_id).first()
            if paciente is None:
                raise ProntuarioNaoEncontrado
            return paciente, None

        dependente = (
            Dependent.objects.select_related('guardian__user')
            .filter(pk=dependent_id)
            .first()
        )
        if dependente is None:
            raise ProntuarioNaoEncontrado
        return None, dependente

    @staticmethod
    def _profissional_possui_vinculo(
        medico: ProfessionalProfile,
        *,
        patient: PatientProfile | None,
        dependent: Dependent | None,
    ) -> bool:
        filtro_triagem = {'triage_session__patient': patient} if patient else {'triage_session__dependent': dependent}
        if ClinicalQueueItem.objects.filter(assigned_professional=medico, **filtro_triagem).exists():
            return True
        if ChatSession.objects.filter(professional=medico, **filtro_triagem).exists():
            return True
        if PrescriptionReview.objects.filter(professional=medico, **filtro_triagem).exists():
            return True
        if DigitalPrescription.objects.filter(prescriber=medico, **filtro_triagem).exists():
            return True
        return False

    @classmethod
    def _autorizar_e_auditar_acesso(
        cls,
        actor_user_id: int,
        *,
        patient: PatientProfile | None,
        dependent: Dependent | None,
        ip_address: str | None = None,
    ) -> ProfessionalProfile | None:
        usuario = User.objects.filter(pk=actor_user_id, is_active=True).first()
        if usuario is None:
            raise PermissaoProntuarioNegada

        if usuario.role == User.Role.PATIENT:
            autorizado = (
                (patient is not None and patient.user_id == usuario.id)
                or (dependent is not None and dependent.guardian.user_id == usuario.id)
            )
            MedicalRecordAccessLog.objects.create(
                actor=usuario,
                patient=patient,
                dependent=dependent,
                allowed=autorizado,
                reason='Consulta pelo titular/responsável' if autorizado else 'Tentativa sem vínculo familiar',
                ip_address=ip_address,
            )
            if not autorizado:
                raise PermissaoProntuarioNegada('Acesso negado a prontuário sem vínculo autorizado.')
            return None

        if usuario.role == User.Role.PROFESSIONAL:
            medico = ProfessionalProfile.objects.filter(user=usuario).first()
            crm_str = f'{medico.crm_number}/{medico.crm_uf}' if medico else ''
            autorizado = (
                medico is not None
                and medico.homologation_status == ProfessionalProfile.HomologationStatus.APPROVED
                and cls._profissional_possui_vinculo(medico, patient=patient, dependent=dependent)
            )
            MedicalRecordAccessLog.objects.create(
                actor=usuario,
                crm_snapshot=crm_str,
                patient=patient,
                dependent=dependent,
                allowed=autorizado,
                reason='Consulta médica com vínculo de atendimento' if autorizado else 'Médico sem vínculo de atendimento',
                ip_address=ip_address,
            )
            if not autorizado:
                raise PermissaoProntuarioNegada('Médico sem vínculo autorizado para este prontuário.')
            return medico

        # Outros perfis (ex.: admin) não têm acesso livre ao conteúdo clínico do prontuário.
        MedicalRecordAccessLog.objects.create(
            actor=usuario,
            patient=patient,
            dependent=dependent,
            allowed=False,
            reason='Perfil sem autorização clínica para prontuário',
            ip_address=ip_address,
        )
        raise PermissaoProntuarioNegada('Perfil não autorizado para consulta clínica de prontuário.')

    @classmethod
    def consultar_prontuario(
        cls,
        actor_user_id: int,
        *,
        patient_id: int | None = None,
        dependent_id: int | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        event_type: str = '',
        risk_color: str = '',
        keyword: str = '',
        ip_address: str | None = None,
    ) -> list[MedicalRecordEvent]:
        if start_date and end_date and start_date > end_date:
            raise ValidationError('A data inicial do período não pode ser posterior à data final.')

        termo = (keyword or '').strip()
        if len(termo) > 100:
            raise ValidationError('A palavra-chave deve ter no máximo 100 caracteres.')

        patient, dependent = cls._resolver_sujeito(patient_id=patient_id, dependent_id=dependent_id)
        cls._autorizar_e_auditar_acesso(
            actor_user_id,
            patient=patient,
            dependent=dependent,
            ip_address=ip_address,
        )

        filtro_direto = {'patient': patient} if patient else {'dependent': dependent}
        filtro_triagem = {'triage_session__patient': patient} if patient else {'triage_session__dependent': dependent}

        retificacoes = list(
            MedicalRecordAmendment.objects.select_related('recorded_by__user').filter(**filtro_direto)
        )
        retificacoes_por_alvo: dict[UUID, list[MedicalRecordAmendment]] = {}
        for ret in retificacoes:
            retificacoes_por_alvo.setdefault(ret.target_event_id, []).append(ret)

        eventos: list[MedicalRecordEvent] = []

        # 1. Triagens
        for t in TriageSession.objects.filter(**filtro_direto):
            eventos.append(
                MedicalRecordEvent(
                    event_id=t.pk,
                    event_type='triage',
                    event_type_label='Triagem',
                    occurred_at=t.completed_at or t.created_at,
                    risk_color=t.risk_color,
                    risk_color_label=t.get_risk_color_display() if t.risk_color else 'Em andamento',
                    professional_name='Triagem assistida',
                    summary=f'{t.symptoms_description} | {t.ai_summary}'.strip(' |'),
                    amendments=retificacoes_por_alvo.get(t.pk, []),
                )
            )

        # 2. Pareceres / revisões médicas
        for rev in PrescriptionReview.objects.select_related('professional__user', 'triage_session').filter(**filtro_triagem):
            nome_med = rev.professional.user.get_full_name() or rev.professional.user.email
            eventos.append(
                MedicalRecordEvent(
                    event_id=rev.pk,
                    event_type='review',
                    event_type_label='Parecer médico',
                    occurred_at=rev.created_at,
                    risk_color=rev.triage_session.risk_color,
                    risk_color_label=rev.triage_session.get_risk_color_display(),
                    professional_name=f'{nome_med} (CRM {rev.professional.crm_number}/{rev.professional.crm_uf})',
                    summary=f'{rev.get_decision_display()}: {rev.clinical_opinion}',
                    amendments=retificacoes_por_alvo.get(rev.pk, []),
                )
            )

        # 3. Atendimentos por chat
        for chat in (
            ChatSession.objects.select_related('professional__user', 'triage_session', 'clinical_outcome')
            .filter(**filtro_triagem)
        ):
            nome_med = chat.professional.user.get_full_name() or chat.professional.user.email
            desfecho = getattr(chat, 'clinical_outcome', None)
            resumo_chat = (
                f'{desfecho.get_outcome_type_display()}: {desfecho.summary_and_conduct}'
                if desfecho
                else 'Atendimento por chat em andamento'
            )
            eventos.append(
                MedicalRecordEvent(
                    event_id=chat.pk,
                    event_type='chat',
                    event_type_label='Consulta por chat',
                    occurred_at=chat.closed_at or chat.created_at,
                    risk_color=chat.triage_session.risk_color,
                    risk_color_label=chat.triage_session.get_risk_color_display(),
                    professional_name=f'{nome_med} (CRM {chat.professional.crm_number}/{chat.professional.crm_uf})',
                    summary=resumo_chat,
                    amendments=retificacoes_por_alvo.get(chat.pk, []),
                )
            )

        # 4. Receitas digitais
        for rx in DigitalPrescription.objects.select_related('prescriber__user', 'triage_session').filter(**filtro_direto):
            nome_med = rx.prescriber.user.get_full_name() or rx.prescriber.user.email
            eventos.append(
                MedicalRecordEvent(
                    event_id=rx.pk,
                    event_type='prescription',
                    event_type_label='Receita digital',
                    occurred_at=rx.issued_at,
                    risk_color=rx.triage_session.risk_color,
                    risk_color_label=rx.triage_session.get_risk_color_display(),
                    professional_name=f'{nome_med} (CRM {rx.prescriber.crm_number}/{rx.prescriber.crm_uf})',
                    summary=f'{rx.medication_name} — {rx.dosage_and_route} ({rx.get_status_display()})',
                    amendments=retificacoes_por_alvo.get(rx.pk, []),
                )
            )

        # 5. Emergências
        for em in EmergencyDispatch.objects.select_related('triage_session').filter(**filtro_triagem):
            eventos.append(
                MedicalRecordEvent(
                    event_id=em.pk,
                    event_type='emergency',
                    event_type_label='Emergência',
                    occurred_at=em.created_at,
                    risk_color=TriageSession.RiskColor.RED,
                    risk_color_label='Vermelha',
                    professional_name='Protocolo de Emergência',
                    summary=f'{em.get_trigger_source_display()}: {em.alert_message}',
                    amendments=retificacoes_por_alvo.get(em.pk, []),
                )
            )

        # Aplicar filtros
        filtrados: list[MedicalRecordEvent] = []
        termo_lower = termo.casefold()
        for ev in eventos:
            data_evento = timezone.localtime(ev.occurred_at).date()
            if start_date and data_evento < start_date:
                continue
            if end_date and data_evento > end_date:
                continue
            if event_type and ev.event_type != event_type:
                continue
            if risk_color and ev.risk_color != risk_color:
                continue
            if termo_lower and termo_lower not in ev.summary.casefold():
                continue
            filtrados.append(ev)

        filtrados.sort(key=lambda item: item.occurred_at, reverse=True)
        return filtrados

    @classmethod
    def registrar_retificacao(
        cls,
        professional_user_id: int,
        *,
        target_event_type: str,
        target_event_id: UUID,
        amendment_text: str,
        patient_id: int | None = None,
        dependent_id: int | None = None,
    ) -> MedicalRecordAmendment:
        texto = (amendment_text or '').strip()
        if not texto:
            raise ValidationError('Informe o texto da retificação clínica.')
        if target_event_type not in MedicalRecordAmendment.EventType.values:
            raise ValidationError('Tipo de evento inválido para retificação.')

        patient, dependent = cls._resolver_sujeito(patient_id=patient_id, dependent_id=dependent_id)
        medico = cls._autorizar_e_auditar_acesso(
            professional_user_id,
            patient=patient,
            dependent=dependent,
        )
        if medico is None:
            raise PermissaoProntuarioNegada('Apenas médicos autorizados podem registrar retificação clínica.')

        return MedicalRecordAmendment.objects.create(
            patient=patient,
            dependent=dependent,
            target_event_type=target_event_type,
            target_event_id=target_event_id,
            recorded_by=medico,
            amendment_text=texto,
        )

    @classmethod
    def listar_logs_acesso(cls) -> QuerySet[MedicalRecordAccessLog]:
        return MedicalRecordAccessLog.objects.select_related('actor', 'patient__user', 'dependent').order_by('-accessed_at')
