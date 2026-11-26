from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core.integrations.speech import SpeechIntegrationDisabled, get_speech_adapter
from professionals.models import ProfessionalProfile
from triage.models import EmergencyDispatch, TriageSession
from triage.services import EmergencyService

from .models import (
    ChatAttachment,
    ChatMessage,
    ChatSession,
    ClinicalOutcome,
    ClinicalQueueItem,
)

ALLOWED_ATTACHMENT_TYPES = {'application/pdf', 'image/png', 'image/jpeg'}
ALLOWED_ATTACHMENT_EXTENSIONS = ('.pdf', '.png', '.jpg', '.jpeg')
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_AUDIO_DURATION_SECONDS = 120


class PermissaoAtendimentoNegada(Exception):
    pass


class ChamadoNaoEncontrado(Exception):
    pass


class SessaoChatNaoEncontrada(Exception):
    pass


class ChatEncerrado(Exception):
    pass


@dataclass(frozen=True, slots=True)
class AnonymizedQueueEntry:
    queue_item_id: UUID
    queue_type: str
    queue_type_label: str
    risk_color: str
    risk_color_label: str
    status: str
    status_label: str
    abbreviated_name: str
    age_years: int
    gender: str
    wait_minutes: int
    enqueued_at: object


def _calcular_idade(birth_date: date) -> int:
    hoje = timezone.localdate()
    anos = hoje.year - birth_date.year
    if (hoje.month, hoje.day) < (birth_date.month, birth_date.day):
        anos -= 1
    return max(anos, 0)


def _abreviar_nome(nome_completo: str) -> str:
    partes = [p for p in (nome_completo or '').strip().split() if p]
    if not partes:
        return 'Paciente'
    return ' '.join(f'{p[0].upper()}.' for p in partes[:3])


def _obter_medico_habilitado(user_id: int, *, exigir_online: bool = True) -> ProfessionalProfile:
    medico = (
        ProfessionalProfile.objects.select_related('user')
        .filter(user_id=user_id, user__is_active=True)
        .first()
    )
    if medico is None:
        raise PermissaoAtendimentoNegada('Perfil médico não encontrado.')
    if medico.homologation_status != ProfessionalProfile.HomologationStatus.APPROVED:
        raise PermissaoAtendimentoNegada('Médico não está homologado para atendimentos.')
    if not medico.crm_regular or not medico.icp_brasil_active:
        raise PermissaoAtendimentoNegada('CRM regular e certificado ICP-Brasil ativo são obrigatórios.')
    if exigir_online and medico.availability != ProfessionalProfile.Availability.ONLINE:
        raise PermissaoAtendimentoNegada('Fique Online no plantão para aceitar novos chamados.')
    return medico


def _dono_da_triagem(triage_session: TriageSession) -> int:
    if triage_session.patient_id is not None:
        return triage_session.patient.user_id
    return triage_session.dependent.guardian.user_id


class QueueService:
    @classmethod
    def enfileirar_triagem(
        cls,
        triage_session: TriageSession,
        *,
        queue_type: str | None = None,
    ) -> ClinicalQueueItem:
        if not triage_session.is_completed:
            raise ValidationError('Apenas triagens concluídas podem entrar na fila clínica.')
        if triage_session.risk_color == TriageSession.RiskColor.RED:
            raise ValidationError('Casos Vermelhos seguem encaminhamento de emergência e não entram em fila virtual.')

        tipo = queue_type
        if tipo is None:
            if triage_session.routing_destination == TriageSession.RoutingDestination.SYNCHRONOUS_CHAT:
                tipo = ClinicalQueueItem.QueueType.SYNCHRONOUS_CHAT
            elif triage_session.routing_destination == TriageSession.RoutingDestination.PRESCRIPTION_REVIEW:
                tipo = ClinicalQueueItem.QueueType.PRESCRIPTION_REVIEW
            else:
                raise ValidationError('Esta triagem não é elegível para fila médica.')

        if tipo not in ClinicalQueueItem.QueueType.values:
            raise ValidationError('Tipo de fila inválido.')

        prioridade = ClinicalQueueItem.PRIORITY_MAP.get(triage_session.risk_color)
        if prioridade is None:
            raise ValidationError('Cor de risco inválida para fila.')

        return ClinicalQueueItem.objects.create(
            triage_session=triage_session,
            queue_type=tipo,
            risk_color=triage_session.risk_color,
            priority_rank=prioridade,
            status=ClinicalQueueItem.Status.WAITING,
        )

    @classmethod
    def listar_fila_anonimizada(
        cls,
        professional_user_id: int,
        *,
        queue_type: str | None = None,
        risk_color: str | None = None,
    ) -> list[AnonymizedQueueEntry]:
        _obter_medico_habilitado(professional_user_id, exigir_online=False)
        qs = (
            ClinicalQueueItem.objects.select_related(
                'triage_session__patient__user',
                'triage_session__dependent',
            )
            .filter(status=ClinicalQueueItem.Status.WAITING)
            .order_by('priority_rank', 'enqueued_at')
        )
        if queue_type:
            qs = qs.filter(queue_type=queue_type)
        if risk_color:
            qs = qs.filter(risk_color=risk_color)

        agora = timezone.now()
        entradas: list[AnonymizedQueueEntry] = []
        for item in qs:
            triagem = item.triage_session
            if triagem.patient_id is not None:
                nome = triagem.patient.user.get_full_name() or triagem.patient.user.email
                idade = _calcular_idade(triagem.patient.birth_date)
                genero = triagem.patient.get_gender_display()
            else:
                nome = triagem.dependent.full_name
                idade = _calcular_idade(triagem.dependent.birth_date)
                genero = triagem.dependent.get_gender_display()

            espera_min = max(int((agora - item.enqueued_at).total_seconds() // 60), 0)
            entradas.append(
                AnonymizedQueueEntry(
                    queue_item_id=item.pk,
                    queue_type=item.queue_type,
                    queue_type_label=item.get_queue_type_display(),
                    risk_color=item.risk_color,
                    risk_color_label=item.get_risk_color_display(),
                    status=item.status,
                    status_label=item.get_status_display(),
                    abbreviated_name=_abreviar_nome(nome),
                    age_years=idade,
                    gender=genero,
                    wait_minutes=espera_min,
                    enqueued_at=item.enqueued_at,
                )
            )
        return entradas

    @classmethod
    def aceitar_chamado(
        cls,
        professional_user_id: int,
        queue_item_id: UUID,
    ) -> tuple[ClinicalQueueItem, ChatSession | None]:
        medico = _obter_medico_habilitado(professional_user_id, exigir_online=True)

        with transaction.atomic():
            item = (
                ClinicalQueueItem.objects.select_for_update(of=('self',))
                .select_related('triage_session')
                .filter(pk=queue_item_id)
                .first()
            )
            if item is None:
                raise ChamadoNaoEncontrado
            if item.status != ClinicalQueueItem.Status.WAITING:
                raise ValidationError('Este chamado já foi aceito ou finalizado.')

            item.status = ClinicalQueueItem.Status.IN_PROGRESS
            item.assigned_professional = medico
            item.accepted_at = timezone.now()
            item.save(update_fields=('status', 'assigned_professional', 'accepted_at'))

            sessao_chat = None
            if item.queue_type == ClinicalQueueItem.QueueType.SYNCHRONOUS_CHAT:
                sessao_chat = ChatSession.objects.create(
                    queue_item=item,
                    triage_session=item.triage_session,
                    professional=medico,
                )
            return item, sessao_chat

    @classmethod
    def listar_meus_atendimentos(cls, professional_user_id: int) -> QuerySet[ClinicalQueueItem]:
        medico = _obter_medico_habilitado(professional_user_id, exigir_online=False)
        return (
            ClinicalQueueItem.objects.select_related(
                'triage_session__patient__user',
                'triage_session__dependent',
                'chat_session',
            )
            .filter(assigned_professional=medico)
            .order_by('-accepted_at')
        )


class ChatService:
    @classmethod
    def obter_sessao_autorizada(cls, user_id: int, session_id: UUID) -> ChatSession:
        sessao = (
            ChatSession.objects.select_related(
                'queue_item',
                'professional__user',
                'triage_session__patient__user',
                'triage_session__patient__clinical_profile',
                'triage_session__dependent__guardian__user',
                'triage_session__dependent__clinical_profile',
            )
            .filter(pk=session_id)
            .first()
        )
        if sessao is None:
            raise SessaoChatNaoEncontrada

        dono_id = _dono_da_triagem(sessao.triage_session)
        participantes = {
            sessao.professional.user_id,
            dono_id,
            sessao.triage_session.initiated_by_id,
        }
        if user_id not in participantes:
            raise PermissaoAtendimentoNegada('Usuário não autorizado nesta sessão de chat.')
        return sessao

    @classmethod
    def obter_resumo_clinico_para_chat(cls, user_id: int, session_id: UUID) -> dict:
        sessao = cls.obter_sessao_autorizada(user_id, session_id)
        triagem = sessao.triage_session
        if triagem.patient_id is not None:
            paciente = triagem.patient
            perfil = paciente.clinical_profile
            nome = paciente.user.get_full_name() or paciente.user.email
            idade = _calcular_idade(paciente.birth_date)
            genero = paciente.get_gender_display()
        else:
            dep = triagem.dependent
            perfil = dep.clinical_profile
            nome = dep.full_name
            idade = _calcular_idade(dep.birth_date)
            genero = dep.get_gender_display()

        return {
            'nome': nome,
            'idade': idade,
            'genero': genero,
            'cor_manchester': triagem.get_risk_color_display(),
            'sintomas': triagem.symptoms_description,
            'resumo_ia': triagem.ai_summary,
            'tipo_sanguineo': perfil.blood_type,
            'alergias': perfil.allergy_description if perfil.has_allergy else 'Nenhuma informada',
            'hipertensao': perfil.has_hypertension,
            'diabetes': perfil.has_diabetes,
            'medicamentos_continuos': perfil.continuous_medications or 'Nenhum informado',
        }

    @classmethod
    def listar_mensagens(cls, user_id: int, session_id: UUID) -> QuerySet[ChatMessage]:
        sessao = cls.obter_sessao_autorizada(user_id, session_id)
        ChatMessage.objects.filter(
            session=sessao,
            read_at__isnull=True,
        ).exclude(sender_id=user_id).update(read_at=timezone.now())
        return (
            ChatMessage.objects.select_related('sender')
            .prefetch_related('attachments')
            .filter(session=sessao)
            .order_by('created_at')
        )

    @classmethod
    def enviar_mensagem(
        cls,
        user_id: int,
        session_id: UUID,
        *,
        content: str = '',
        attachment=None,
        audio_bytes: bytes | None = None,
        audio_duration_seconds: int = 0,
    ) -> ChatMessage:
        with transaction.atomic():
            sessao = cls.obter_sessao_autorizada(user_id, session_id)
            if sessao.is_closed:
                raise ChatEncerrado('Esta sessão de chat foi encerrada e o diálogo é imutável.')

            texto = (content or '').strip()
            veio_de_audio = False

            if audio_bytes is not None:
                if audio_duration_seconds <= 0 or audio_duration_seconds > MAX_AUDIO_DURATION_SECONDS:
                    raise ValidationError(
                        f'O áudio deve ter duração máxima de {MAX_AUDIO_DURATION_SECONDS} segundos.',
                    )
                try:
                    transcricao = get_speech_adapter().transcribe(audio_bytes)
                except SpeechIntegrationDisabled as erro:
                    raise ValidationError(str(erro)) from erro
                texto = transcricao.text.strip()
                veio_de_audio = True
                # Áudio bruto não é persistido em disco nem banco (RF015/RS009).

            if not texto and attachment is None:
                raise ValidationError('Envie uma mensagem de texto, áudio transcrito ou anexo.')
            if len(texto) > 1000:
                raise ValidationError('A mensagem de texto deve ter no máximo 1000 caracteres.')

            if attachment is not None:
                content_type = getattr(attachment, 'content_type', '') or ''
                nome_arquivo = (getattr(attachment, 'name', '') or '').lower()
                tamanho = getattr(attachment, 'size', 0) or 0
                if (
                    content_type not in ALLOWED_ATTACHMENT_TYPES
                    or not nome_arquivo.endswith(ALLOWED_ATTACHMENT_EXTENSIONS)
                ):
                    raise ValidationError('Formato de anexo não permitido. Envie PDF, PNG ou JPEG.')
                if tamanho <= 0 or tamanho > MAX_ATTACHMENT_BYTES:
                    raise ValidationError('O anexo deve ter no máximo 10 MB.')

            mensagem = ChatMessage.objects.create(
                session=sessao,
                sender_id=user_id,
                content=texto or '[Anexo enviado]',
                is_from_audio_transcription=veio_de_audio,
            )

            if attachment is not None:
                ChatAttachment.objects.create(
                    message=mensagem,
                    file=attachment,
                    original_name=getattr(attachment, 'name', 'anexo')[:255],
                    content_type=getattr(attachment, 'content_type', ''),
                    size_bytes=getattr(attachment, 'size', 0),
                )

            return mensagem

    @classmethod
    def encerrar_sessao(
        cls,
        professional_user_id: int,
        session_id: UUID,
        *,
        outcome_type: str,
        summary_and_conduct: str,
        warning_signs: str = '',
        reclassified_to_red: bool = False,
    ) -> tuple[ClinicalOutcome, EmergencyDispatch | None]:
        conduta = (summary_and_conduct or '').strip()
        if not conduta or len(conduta) > 1000:
            raise ValidationError('O resumo e conduta clínica é obrigatório (até 1000 caracteres).')
        if outcome_type not in ClinicalOutcome.OutcomeType.values:
            raise ValidationError('Selecione um tipo de desfecho válido.')

        eh_emergencia = (
            reclassified_to_red
            or outcome_type == ClinicalOutcome.OutcomeType.EMERGENCY_RECLASSIFICATION
        )

        with transaction.atomic():
            sessao = (
                ChatSession.objects.select_for_update(of=('self',))
                .select_related(
                    'queue_item',
                    'professional',
                    'triage_session__patient__user',
                    'triage_session__patient__clinical_profile',
                    'triage_session__dependent__guardian__user',
                    'triage_session__dependent__clinical_profile',
                )
                .filter(pk=session_id)
                .first()
            )
            if sessao is None:
                raise SessaoChatNaoEncontrada
            if sessao.professional.user_id != professional_user_id:
                raise PermissaoAtendimentoNegada('Apenas o médico responsável pode encerrar o atendimento.')
            if sessao.is_closed:
                raise ChatEncerrado('Esta sessão já foi encerrada.')

            desfecho = ClinicalOutcome.objects.create(
                chat_session=sessao,
                outcome_type=(
                    ClinicalOutcome.OutcomeType.EMERGENCY_RECLASSIFICATION
                    if eh_emergencia
                    else outcome_type
                ),
                summary_and_conduct=conduta,
                warning_signs=(warning_signs or '').strip(),
                reclassified_to_red=eh_emergencia,
                recorded_by=sessao.professional,
            )

            agora = timezone.now()
            sessao.is_closed = True
            sessao.closed_at = agora
            sessao.save(update_fields=('is_closed', 'closed_at'))

            item_fila = sessao.queue_item
            if outcome_type == ClinicalOutcome.OutcomeType.PRESCRIPTION_ISSUED and not eh_emergencia:
                item_fila.status = ClinicalQueueItem.Status.AWAITING_PRESCRIPTION
                item_fila.save(update_fields=('status',))
            else:
                item_fila.status = ClinicalQueueItem.Status.FINISHED
                item_fila.finished_at = agora
                item_fila.save(update_fields=('status', 'finished_at'))

            dispatch = None
            if eh_emergencia:
                dispatch = EmergencyService.registrar_emergencia(
                    sessao.triage_session,
                    trigger_source=EmergencyDispatch.TriggerSource.CHAT_RECLASSIFICATION,
                )

            return desfecho, dispatch
