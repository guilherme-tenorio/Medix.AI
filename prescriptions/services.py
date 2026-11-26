from __future__ import annotations

import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from care.models import ClinicalQueueItem
from care.services import QueueService
from core.integrations.pdf import PrescriptionPdfData, render_prescription_pdf
from professionals.models import ProfessionalProfile
from triage.models import EmergencyDispatch, TriageSession
from triage.services import EmergencyService

from .models import DigitalPrescription, PrescriptionDispensation, PrescriptionReview

PRESCRIPTION_VALIDITY_DAYS = 30


class PermissaoReceitaNegada(Exception):
    pass


class ReceitaNaoEncontrada(Exception):
    pass


class ConflitoAlergiaCritico(Exception):
    pass


class DispensacaoRecusada(Exception):
    pass


@dataclass(frozen=True, slots=True)
class PublicPrescriptionVerification:
    prescription_id: UUID
    is_valid_for_dispensation: bool
    effective_status: str
    effective_status_label: str
    prescriber_name: str
    prescriber_crm: str
    medication_name: str
    dosage_and_route: str
    issued_at: object
    valid_until: object
    icp_signature_valid: bool
    dispensed_at: object | None


def _obter_medico_prescritor(user_id: int) -> ProfessionalProfile:
    medico = (
        ProfessionalProfile.objects.select_related('user')
        .filter(user_id=user_id, user__is_active=True)
        .first()
    )
    if medico is None:
        raise PermissaoReceitaNegada('Perfil médico não encontrado.')
    if medico.homologation_status != ProfessionalProfile.HomologationStatus.APPROVED:
        raise PermissaoReceitaNegada('Apenas médicos homologados podem validar prescrições.')
    if not medico.crm_regular or not medico.icp_brasil_active:
        raise PermissaoReceitaNegada('CRM ativo/regular e certificado ICP-Brasil válido são obrigatórios.')
    return medico


def _normalizar_cnpj(cnpj: str) -> str:
    digitos = re.sub(r'\D+', '', cnpj or '')
    if len(digitos) != 14 or len(set(digitos)) == 1:
        raise ValidationError('Informe um CNPJ válido com 14 dígitos.')
    return digitos


def _gerar_hash_icp(
    *,
    triage_id: UUID,
    crm_number: str,
    crm_uf: str,
    medication_name: str,
    dosage_and_route: str,
    issued_iso: str,
) -> str:
    material = f'{triage_id}|{crm_number}/{crm_uf}|{medication_name}|{dosage_and_route}|{issued_iso}'
    return hashlib.sha256(material.encode('utf-8')).hexdigest()


class PrescriptionReviewService:
    @classmethod
    def obter_contexto_revisao(cls, professional_user_id: int, triage_id: UUID) -> dict:
        _obter_medico_prescritor(professional_user_id)
        triagem = (
            TriageSession.objects.select_related(
                'patient__user',
                'patient__clinical_profile',
                'dependent__guardian__user',
                'dependent__clinical_profile',
            )
            .filter(pk=triage_id)
            .first()
        )
        if triagem is None:
            raise ReceitaNaoEncontrada('Triagem não encontrada.')

        if triagem.patient_id is not None:
            perfil = triagem.patient.clinical_profile
            nome = triagem.patient.user.get_full_name() or triagem.patient.user.email
            genero = triagem.patient.get_gender_display()
        else:
            perfil = triagem.dependent.clinical_profile
            nome = triagem.dependent.full_name
            genero = triagem.dependent.get_gender_display()

        conflito, detalhe_conflito = cls.verificar_conflito_alergia(
            triagem,
            triagem.suggested_medication,
        )
        return {
            'triagem': triagem,
            'paciente_nome': nome,
            'paciente_genero': genero,
            'perfil_clinico': perfil,
            'conflito_alergia': conflito,
            'detalhe_conflito': detalhe_conflito,
        }

    @staticmethod
    def verificar_conflito_alergia(
        triage_session: TriageSession,
        medication_name: str,
    ) -> tuple[bool, str]:
        perfil = (
            triage_session.patient.clinical_profile
            if triage_session.patient_id is not None
            else triage_session.dependent.clinical_profile
        )
        if not perfil.has_allergy or not perfil.allergy_description.strip():
            return False, ''

        medicamento_norm = (medication_name or '').casefold()
        alergias_brutas = re.split(r'[,;/\n]+', perfil.allergy_description)
        for termo in alergias_brutas:
            limpo = termo.strip().casefold()
            if len(limpo) >= 3 and limpo in medicamento_norm:
                return (
                    True,
                    f'ALERTA CRÍTICO: o fármaco "{medication_name}" conflita com alergia registrada ({termo.strip()}).',
                )
        return False, ''

    @classmethod
    def registrar_revisao(
        cls,
        professional_user_id: int,
        triage_id: UUID,
        *,
        decision: str,
        clinical_opinion: str,
        prescribed_medication: str = '',
        dosage_and_route: str = '',
        instructions: str = '',
        queue_item_id: UUID | None = None,
    ) -> tuple[PrescriptionReview, DigitalPrescription | None, EmergencyDispatch | None]:
        medico = _obter_medico_prescritor(professional_user_id)
        parecer = (clinical_opinion or '').strip()
        if not parecer:
            raise ValidationError('O parecer clínico é obrigatório.')
        if decision not in PrescriptionReview.Decision.values:
            raise ValidationError('Decisão clínica inválida.')

        with transaction.atomic():
            triagem = (
                TriageSession.objects.select_related(
                    'patient__user',
                    'patient__clinical_profile',
                    'dependent__guardian__user',
                    'dependent__clinical_profile',
                )
                .filter(pk=triage_id)
                .first()
            )
            if triagem is None:
                raise ReceitaNaoEncontrada('Triagem não encontrada.')
            if not triagem.is_completed:
                raise ValidationError('A triagem precisa estar concluída para revisão.')
            if triagem.risk_color == TriageSession.RiskColor.RED:
                raise ValidationError('Casos Vermelhos seguem fluxo de emergência e não passam por prescrição.')

            # Para fluxo direto da Spec 0010, exigir Branco/Verde (a menos que haja atendimento em chat)
            possui_chat = triagem.chat_sessions.exists()
            if (
                triagem.risk_color not in {TriageSession.RiskColor.WHITE, TriageSession.RiskColor.GREEN}
                and not possui_chat
            ):
                raise ValidationError(
                    'A revisão direta de prescrição atende casos Brancos/Verdes ou atendimentos em chat.',
                )

            queue_item = None
            if queue_item_id is not None:
                queue_item = (
                    ClinicalQueueItem.objects.select_for_update(of=('self',))
                    .filter(pk=queue_item_id, triage_session=triagem)
                    .first()
                )

            farmaco = (prescribed_medication or '').strip()
            posologia = (dosage_and_route or '').strip()
            orientacoes = (instructions or '').strip()

            eh_aprovacao = decision in {
                PrescriptionReview.Decision.APPROVED,
                PrescriptionReview.Decision.APPROVED_WITH_CHANGES,
            }

            conflito, detalhe_conflito = cls.verificar_conflito_alergia(
                triagem,
                farmaco or triagem.suggested_medication,
            )

            if eh_aprovacao:
                if not farmaco or not posologia:
                    raise ValidationError('Informe fármaco e posologia/via para aprovar e assinar a receita.')
                if conflito:
                    raise ConflitoAlergiaCritico(detalhe_conflito)

            revisao = PrescriptionReview.objects.create(
                triage_session=triagem,
                queue_item=queue_item,
                professional=medico,
                decision=decision,
                clinical_opinion=parecer,
                allergy_conflict_detected=conflito,
                allergy_conflict_details=detalhe_conflito[:300],
                prescribed_medication=farmaco[:200],
                dosage_and_route=posologia[:300],
                instructions=orientacoes,
            )

            receita = None
            dispatch = None
            agora = timezone.now()

            if eh_aprovacao:
                assinatura_hash = _gerar_hash_icp(
                    triage_id=triagem.pk,
                    crm_number=medico.crm_number,
                    crm_uf=medico.crm_uf,
                    medication_name=farmaco,
                    dosage_and_route=posologia,
                    issued_iso=agora.isoformat(),
                )
                receita = DigitalPrescription.objects.create(
                    review=revisao,
                    triage_session=triagem,
                    patient=triagem.patient,
                    dependent=triagem.dependent,
                    prescriber=medico,
                    medication_name=farmaco[:200],
                    dosage_and_route=posologia[:300],
                    instructions=orientacoes,
                    icp_signature_hash=assinatura_hash,
                    icp_signature_valid=True,
                    verification_token=secrets.token_urlsafe(32)[:64],
                    status=DigitalPrescription.Status.ACTIVE,
                    valid_until=agora + timedelta(days=PRESCRIPTION_VALIDITY_DAYS),
                )
                if queue_item is not None:
                    queue_item.status = ClinicalQueueItem.Status.FINISHED
                    queue_item.finished_at = agora
                    queue_item.save(update_fields=('status', 'finished_at'))

                from notifications.models import NotificationOutbox
                from notifications.services import NotificacaoService

                dono_id = (
                    triagem.patient.user_id
                    if triagem.patient_id is not None
                    else triagem.dependent.guardian.user_id
                )
                NotificacaoService.enviar_notificacao(
                    dono_id,
                    event_key=f'prescription-issued:{receita.pk}',
                    title='Nova receita digital disponível',
                    masked_body='Sua receita digital assinada está disponível no portal MEDIX.AI.',
                    channel=NotificationOutbox.Channel.PUSH,
                    priority=NotificationOutbox.Priority.MODERATE,
                    deep_link=f'/receitas/{receita.pk}/',
                )

            elif decision == PrescriptionReview.Decision.REJECTED_TO_CHAT:
                if queue_item is not None:
                    queue_item.status = ClinicalQueueItem.Status.FINISHED
                    queue_item.finished_at = agora
                    queue_item.save(update_fields=('status', 'finished_at'))
                QueueService.enfileirar_triagem(
                    triagem,
                    queue_type=ClinicalQueueItem.QueueType.SYNCHRONOUS_CHAT,
                )

            elif decision == PrescriptionReview.Decision.RECLASSIFIED_TO_RED:
                if queue_item is not None:
                    queue_item.status = ClinicalQueueItem.Status.FINISHED
                    queue_item.finished_at = agora
                    queue_item.save(update_fields=('status', 'finished_at'))
                dispatch = EmergencyService.registrar_emergencia(
                    triagem,
                    trigger_source=EmergencyDispatch.TriggerSource.PRESCRIPTION_RECLASSIFICATION,
                )

            return revisao, receita, dispatch


class PrescriptionService:
    @classmethod
    def _dono_da_receita(cls, receita: DigitalPrescription) -> int:
        if receita.patient_id is not None:
            return receita.patient.user_id
        return receita.dependent.guardian.user_id

    @classmethod
    def obter_receita_autorizada(cls, user_id: int, prescription_id: UUID) -> DigitalPrescription:
        receita = (
            DigitalPrescription.objects.select_related(
                'prescriber__user',
                'patient__user',
                'dependent__guardian__user',
                'triage_session',
            )
            .filter(pk=prescription_id)
            .first()
        )
        if receita is None:
            raise ReceitaNaoEncontrada

        autorizados = {
            cls._dono_da_receita(receita),
            receita.prescriber.user_id,
            receita.triage_session.initiated_by_id,
        }
        if user_id not in autorizados:
            raise PermissaoReceitaNegada('Você não tem permissão para acessar esta receita.')
        return receita

    @classmethod
    def listar_receitas_paciente(cls, user_id: int) -> QuerySet[DigitalPrescription]:
        return (
            DigitalPrescription.objects.select_related('prescriber__user', 'patient__user', 'dependent')
            .filter(
                Q(patient__user_id=user_id)
                | Q(dependent__guardian__user_id=user_id)
                | Q(triage_session__initiated_by_id=user_id)
            )
            .order_by('-issued_at')
        )

    @classmethod
    def gerar_pdf_receita(
        cls,
        user_id: int,
        prescription_id: UUID,
        *,
        verification_url: str = '',
    ) -> bytes:
        receita = cls.obter_receita_autorizada(user_id, prescription_id)
        if not receita.icp_signature_valid or not receita.icp_signature_hash:
            raise ValidationError('Receita sem assinatura ICP-Brasil válida não pode gerar PDF.')

        nome_paciente = (
            receita.patient.user.get_full_name() or receita.patient.user.email
            if receita.patient_id is not None
            else receita.dependent.full_name
        )
        nome_medico = receita.prescriber.user.get_full_name() or receita.prescriber.user.email
        dados_pdf = PrescriptionPdfData(
            prescription_id=str(receita.pk),
            verification_url=verification_url or f'/receitas/verificar/{receita.verification_token}/',
            patient_name=nome_paciente,
            prescriber_name=nome_medico,
            prescriber_crm=f'{receita.prescriber.crm_number}/{receita.prescriber.crm_uf}',
            medication_name=receita.medication_name,
            dosage_and_route=receita.dosage_and_route,
            instructions=receita.instructions,
            issued_at_str=timezone.localtime(receita.issued_at).strftime('%d/%m/%Y %H:%M'),
            valid_until_str=timezone.localtime(receita.valid_until).strftime('%d/%m/%Y %H:%M'),
            icp_signature_hash=receita.icp_signature_hash,
        )
        return render_prescription_pdf(dados_pdf)

    @classmethod
    def revogar_receita(
        cls,
        professional_user_id: int,
        prescription_id: UUID,
        *,
        reason: str,
    ) -> DigitalPrescription:
        motivo = (reason or '').strip()
        if not motivo or len(motivo) > 300:
            raise ValidationError('Informe a justificativa para revogar a receita (até 300 caracteres).')

        with transaction.atomic():
            receita = (
                DigitalPrescription.objects.select_for_update(of=('self',))
                .select_related('prescriber')
                .filter(pk=prescription_id)
                .first()
            )
            if receita is None:
                raise ReceitaNaoEncontrada
            if receita.prescriber.user_id != professional_user_id:
                raise PermissaoReceitaNegada('Apenas o médico prescritor pode revogar esta receita.')
            if receita.status == DigitalPrescription.Status.DISPENSED:
                raise ValidationError('Receita já dispensada não pode ser revogada.')
            if receita.status == DigitalPrescription.Status.REVOKED:
                return receita

            receita.status = DigitalPrescription.Status.REVOKED
            receita.revoked_at = timezone.now()
            receita.revocation_reason = motivo
            receita.save(update_fields=('status', 'revoked_at', 'revocation_reason'))
            return receita

    @classmethod
    def consultar_autenticidade_publica(cls, verification_token: str) -> PublicPrescriptionVerification:
        receita = (
            DigitalPrescription.objects.select_related('prescriber__user')
            .filter(verification_token=verification_token)
            .first()
        )
        if receita is None:
            raise ReceitaNaoEncontrada('Código de receita inválido ou não encontrado.')

        dispensacao = PrescriptionDispensation.objects.filter(prescription=receita).first()
        agora = timezone.now()

        if receita.status == DigitalPrescription.Status.REVOKED:
            status_efetivo = DigitalPrescription.Status.REVOKED
            label = 'Revogada'
            valida = False
        elif receita.status == DigitalPrescription.Status.DISPENSED or dispensacao is not None:
            status_efetivo = DigitalPrescription.Status.DISPENSED
            label = 'Utilizada / Dispensada'
            valida = False
        elif receita.valid_until < agora:
            status_efetivo = DigitalPrescription.Status.EXPIRED
            label = 'Expirada'
            valida = False
        elif not receita.icp_signature_valid:
            status_efetivo = DigitalPrescription.Status.REVOKED
            label = 'Assinatura inválida'
            valida = False
        else:
            status_efetivo = DigitalPrescription.Status.ACTIVE
            label = 'Ativa / Válida'
            valida = True

        nome_medico = receita.prescriber.user.get_full_name() or receita.prescriber.user.email
        return PublicPrescriptionVerification(
            prescription_id=receita.pk,
            is_valid_for_dispensation=valida,
            effective_status=status_efetivo,
            effective_status_label=label,
            prescriber_name=nome_medico,
            prescriber_crm=f'{receita.prescriber.crm_number}/{receita.prescriber.crm_uf}',
            medication_name=receita.medication_name,
            dosage_and_route=receita.dosage_and_route,
            issued_at=receita.issued_at,
            valid_until=receita.valid_until,
            icp_signature_valid=receita.icp_signature_valid,
            dispensed_at=dispensacao.dispensed_at if dispensacao else None,
        )

    @classmethod
    def dispensar_receita(
        cls,
        verification_token: str,
        *,
        pharmacist_name: str,
        crf_number: str,
        crf_uf: str,
        pharmacy_cnpj: str,
    ) -> PrescriptionDispensation:
        nome_farm = (pharmacist_name or '').strip()
        crf = (crf_number or '').strip()
        uf = (crf_uf or '').strip().upper()
        if len(nome_farm) < 3 or len(nome_farm) > 120:
            raise ValidationError('Informe o nome completo do farmacêutico.')
        if not crf or len(crf) > 20:
            raise ValidationError('Informe o número do CRF.')
        if len(uf) != 2 or not uf.isalpha():
            raise ValidationError('Informe a UF do CRF com 2 letras.')
        cnpj = _normalizar_cnpj(pharmacy_cnpj)

        with transaction.atomic():
            receita = (
                DigitalPrescription.objects.select_for_update()
                .filter(verification_token=verification_token)
                .first()
            )
            if receita is None:
                raise DispensacaoRecusada('Receita não encontrada.')
            if receita.status == DigitalPrescription.Status.REVOKED:
                raise DispensacaoRecusada('Receita revogada não pode ser dispensada.')
            if receita.status == DigitalPrescription.Status.DISPENSED:
                raise DispensacaoRecusada('Esta receita já foi dispensada anteriormente.')
            if not receita.icp_signature_valid:
                raise DispensacaoRecusada('Assinatura ICP-Brasil inválida.')
            if receita.valid_until < timezone.now():
                receita.status = DigitalPrescription.Status.EXPIRED
                receita.save(update_fields=('status',))
                raise DispensacaoRecusada('Receita expirada não pode ser dispensada.')

            try:
                dispensacao = PrescriptionDispensation.objects.create(
                    prescription=receita,
                    pharmacist_name=nome_farm,
                    crf_number=crf,
                    crf_uf=uf,
                    pharmacy_cnpj=cnpj,
                )
            except IntegrityError as erro:
                raise DispensacaoRecusada('Esta receita já foi dispensada.') from erro

            receita.status = DigitalPrescription.Status.DISPENSED
            receita.save(update_fields=('status',))
            return dispensacao
