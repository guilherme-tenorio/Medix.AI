from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View

from users.models import User

from .forms import ChatMessageForm, ClinicalOutcomeForm
from .models import ClinicalOutcome, ClinicalQueueItem
from .services import (
    ChamadoNaoEncontrado,
    ChatEncerrado,
    ChatService,
    PermissaoAtendimentoNegada,
    QueueService,
    SessaoChatNaoEncontrada,
)


def _garantir_medico(request: HttpRequest) -> None:
    if request.user.role != User.Role.PROFESSIONAL:
        raise PermissionDenied


class MedicalQueueDashboardView(LoginRequiredMixin, View):
    template_name = 'care/queue_dashboard.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        _garantir_medico(request)
        cor_filtro = request.GET.get('risk_color') or None
        try:
            fila_chat = QueueService.listar_fila_anonimizada(
                request.user.id,
                queue_type=ClinicalQueueItem.QueueType.SYNCHRONOUS_CHAT,
                risk_color=cor_filtro,
            )
            fila_revisao = QueueService.listar_fila_anonimizada(
                request.user.id,
                queue_type=ClinicalQueueItem.QueueType.PRESCRIPTION_REVIEW,
                risk_color=cor_filtro,
            )
            meus_atendimentos = QueueService.listar_meus_atendimentos(request.user.id)
        except PermissaoAtendimentoNegada as erro:
            raise PermissionDenied(str(erro)) from None

        return render(
            request,
            self.template_name,
            {
                'fila_chat': fila_chat,
                'fila_revisao': fila_revisao,
                'meus_atendimentos': meus_atendimentos,
                'cor_filtro': cor_filtro or '',
            },
        )


class AcceptQueueItemView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, queue_item_id: UUID) -> HttpResponse:
        _garantir_medico(request)
        try:
            item, sessao_chat = QueueService.aceitar_chamado(request.user.id, queue_item_id)
        except PermissaoAtendimentoNegada as erro:
            messages.error(request, str(erro))
            return redirect(reverse('care:queue_dashboard'))
        except ChamadoNaoEncontrado:
            raise Http404 from None
        except ValidationError as erro:
            messages.error(request, '; '.join(erro.messages))
            return redirect(reverse('care:queue_dashboard'))

        messages.success(request, 'Chamado aceito com sucesso.')
        if sessao_chat is not None:
            return redirect(reverse('care:chat_room', kwargs={'session_id': sessao_chat.pk}))
        if item.queue_type == ClinicalQueueItem.QueueType.PRESCRIPTION_REVIEW:
            url = reverse('prescriptions:review', kwargs={'triage_id': item.triage_session_id})
            return redirect(f'{url}?queue_item_id={item.pk}')
        return redirect(reverse('care:queue_dashboard'))


class ChatRoomView(LoginRequiredMixin, View):
    template_name = 'care/chat_room.html'

    def get(self, request: HttpRequest, session_id: UUID) -> HttpResponse:
        try:
            sessao = ChatService.obter_sessao_autorizada(request.user.id, session_id)
            resumo = ChatService.obter_resumo_clinico_para_chat(request.user.id, session_id)
            mensagens = ChatService.listar_mensagens(request.user.id, session_id)
        except SessaoChatNaoEncontrada:
            raise Http404 from None
        except PermissaoAtendimentoNegada:
            raise PermissionDenied from None

        return render(
            request,
            self.template_name,
            {
                'sessao': sessao,
                'resumo': resumo,
                'mensagens': mensagens,
                'message_form': ChatMessageForm(),
                'outcome_form': ClinicalOutcomeForm(),
                'eh_medico': request.user.id == sessao.professional.user_id,
            },
        )

    def post(self, request: HttpRequest, session_id: UUID) -> HttpResponse:
        form = ChatMessageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                ChatService.enviar_mensagem(
                    request.user.id,
                    session_id,
                    content=form.cleaned_data.get('content', ''),
                    attachment=form.cleaned_data.get('attachment'),
                )
            except SessaoChatNaoEncontrada:
                raise Http404 from None
            except PermissaoAtendimentoNegada:
                raise PermissionDenied from None
            except (ValidationError, ChatEncerrado) as erro:
                msg = '; '.join(erro.messages) if isinstance(erro, ValidationError) else str(erro)
                messages.error(request, msg)
        else:
            messages.error(request, 'Verifique o conteúdo da mensagem ou do anexo.')
        return redirect(reverse('care:chat_room', kwargs={'session_id': session_id}))


class ChatMessagesPollView(LoginRequiredMixin, View):
    """Endpoint JSON para sincronização periódica das mensagens do chat."""

    def get(self, request: HttpRequest, session_id: UUID) -> JsonResponse:
        try:
            sessao = ChatService.obter_sessao_autorizada(request.user.id, session_id)
            mensagens = ChatService.listar_mensagens(request.user.id, session_id)
        except SessaoChatNaoEncontrada:
            return JsonResponse({'error': 'Sessão não encontrada.'}, status=404)
        except PermissaoAtendimentoNegada:
            return JsonResponse({'error': 'Acesso negado.'}, status=403)

        dados = [
            {
                'id': str(msg.pk),
                'sender_name': msg.sender.get_full_name() or msg.sender.email,
                'is_mine': msg.sender_id == request.user.id,
                'content': msg.content,
                'is_audio': msg.is_from_audio_transcription,
                'created_at': timezone.localtime(msg.created_at).strftime('%d/%m/%Y %H:%M:%S'),
                'status': 'lida' if msg.read_at else 'entregue',
                'attachments': [
                    {'name': a.original_name, 'type': a.content_type}
                    for a in msg.attachments.all()
                ],
            }
            for msg in mensagens
        ]
        return JsonResponse({'is_closed': sessao.is_closed, 'messages': dados})


class ChatAiAssistView(LoginRequiredMixin, View):
    """Síntese clínica assistida por LLM (Gemini / Sandbox) desidentificada para o médico."""

    def post(self, request: HttpRequest, session_id: UUID) -> JsonResponse:
        _garantir_medico(request)
        try:
            sintese = ChatService.gerar_apoio_ia(request.user.id, session_id)
        except SessaoChatNaoEncontrada:
            return JsonResponse({'error': 'Sessão não encontrada.'}, status=404)
        except PermissaoAtendimentoNegada as erro:
            return JsonResponse({'error': str(erro)}, status=403)
        except ValidationError as erro:
            return JsonResponse({'error': '; '.join(erro.messages)}, status=503)
        return JsonResponse({'summary': sintese})


class CloseChatSessionView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, session_id: UUID) -> HttpResponse:
        _garantir_medico(request)
        form = ClinicalOutcomeForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Preencha o tipo de desfecho e o resumo/conduta clínica.')
            return redirect(reverse('care:chat_room', kwargs={'session_id': session_id}))

        try:
            desfecho, dispatch = ChatService.encerrar_sessao(
                request.user.id,
                session_id,
                outcome_type=form.cleaned_data['outcome_type'],
                summary_and_conduct=form.cleaned_data['summary_and_conduct'],
                warning_signs=form.cleaned_data.get('warning_signs', ''),
                reclassified_to_red=form.cleaned_data.get('reclassified_to_red', False),
            )
        except SessaoChatNaoEncontrada:
            raise Http404 from None
        except PermissaoAtendimentoNegada:
            raise PermissionDenied from None
        except (ValidationError, ChatEncerrado) as erro:
            msg = '; '.join(erro.messages) if isinstance(erro, ValidationError) else str(erro)
            messages.error(request, msg)
            return redirect(reverse('care:chat_room', kwargs={'session_id': session_id}))

        if dispatch is not None:
            messages.warning(request, 'Atendimento reclassificado para Vermelho. Alerta de emergência disparado.')
            return redirect(reverse('care:chat_room', kwargs={'session_id': session_id}))

        if desfecho.outcome_type == ClinicalOutcome.OutcomeType.PRESCRIPTION_ISSUED:
            messages.success(request, 'Chat encerrado. Preencha e assine a receita digital.')
            return redirect(
                reverse('prescriptions:review', kwargs={'triage_id': desfecho.chat_session.triage_session_id})
            )

        messages.success(request, 'Atendimento encerrado com desfecho registrado.')
        return redirect(reverse('care:chat_room', kwargs={'session_id': session_id}))
