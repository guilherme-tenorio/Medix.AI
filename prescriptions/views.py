from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from users.models import User

from .forms import (
    PrescriptionDispensationForm,
    PrescriptionReviewForm,
    PrescriptionRevokeForm,
)
from .services import (
    ConflitoAlergiaCritico,
    DispensacaoRecusada,
    PermissaoReceitaNegada,
    PrescriptionReviewService,
    PrescriptionService,
    ReceitaNaoEncontrada,
)


class PatientPrescriptionListView(LoginRequiredMixin, View):
    template_name = 'prescriptions/list.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.role != User.Role.PATIENT:
            raise PermissionDenied
        receitas = PrescriptionService.listar_receitas_paciente(request.user.id)
        return render(request, self.template_name, {'receitas': receitas})


class PrescriptionDetailView(LoginRequiredMixin, View):
    template_name = 'prescriptions/detail.html'

    def get(self, request: HttpRequest, prescription_id: UUID) -> HttpResponse:
        try:
            receita = PrescriptionService.obter_receita_autorizada(request.user.id, prescription_id)
        except ReceitaNaoEncontrada:
            raise Http404 from None
        except PermissaoReceitaNegada:
            raise PermissionDenied from None

        return render(
            request,
            self.template_name,
            {
                'receita': receita,
                'eh_prescritor': request.user.id == receita.prescriber.user_id,
                'revoke_form': PrescriptionRevokeForm(),
            },
        )


class PrescriptionPdfDownloadView(LoginRequiredMixin, View):
    def get(self, request: HttpRequest, prescription_id: UUID) -> HttpResponse:
        try:
            receita = PrescriptionService.obter_receita_autorizada(request.user.id, prescription_id)
            url_verificacao = request.build_absolute_uri(
                reverse('prescriptions:public_verify', kwargs={'token': receita.verification_token})
            )
            pdf_bytes = PrescriptionService.gerar_pdf_receita(
                request.user.id,
                prescription_id,
                verification_url=url_verificacao,
            )
        except ReceitaNaoEncontrada:
            raise Http404 from None
        except PermissaoReceitaNegada:
            raise PermissionDenied from None
        except ValidationError as erro:
            messages.error(request, '; '.join(erro.messages))
            return redirect(reverse('prescriptions:detail', kwargs={'prescription_id': prescription_id}))

        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receita-{prescription_id}.pdf"'
        return response


class PrescriptionReviewView(LoginRequiredMixin, View):
    template_name = 'prescriptions/review.html'

    def _carregar_contexto(self, request: HttpRequest, triage_id: UUID, form: PrescriptionReviewForm) -> dict:
        try:
            ctx = PrescriptionReviewService.obter_contexto_revisao(request.user.id, triage_id)
        except ReceitaNaoEncontrada:
            raise Http404 from None
        except PermissaoReceitaNegada:
            raise PermissionDenied from None
        ctx['form'] = form
        ctx['triage_id'] = triage_id
        ctx['queue_item_id'] = request.GET.get('queue_item_id') or request.POST.get('queue_item_id') or ''
        return ctx

    def get(self, request: HttpRequest, triage_id: UUID) -> HttpResponse:
        if request.user.role != User.Role.PROFESSIONAL:
            raise PermissionDenied
        ctx = self._carregar_contexto(request, triage_id, PrescriptionReviewForm())
        return render(request, self.template_name, ctx)

    def post(self, request: HttpRequest, triage_id: UUID) -> HttpResponse:
        if request.user.role != User.Role.PROFESSIONAL:
            raise PermissionDenied
        form = PrescriptionReviewForm(request.POST)
        queue_item_raw = request.POST.get('queue_item_id') or request.GET.get('queue_item_id')
        queue_item_uuid = None
        if queue_item_raw:
            try:
                queue_item_uuid = UUID(queue_item_raw)
            except ValueError:
                queue_item_uuid = None

        if form.is_valid():
            try:
                _revisao, receita, dispatch = PrescriptionReviewService.registrar_revisao(
                    request.user.id,
                    triage_id,
                    decision=form.cleaned_data['decision'],
                    clinical_opinion=form.cleaned_data['clinical_opinion'],
                    prescribed_medication=form.cleaned_data.get('prescribed_medication', ''),
                    dosage_and_route=form.cleaned_data.get('dosage_and_route', ''),
                    instructions=form.cleaned_data.get('instructions', ''),
                    queue_item_id=queue_item_uuid,
                )
            except ReceitaNaoEncontrada:
                raise Http404 from None
            except PermissaoReceitaNegada:
                raise PermissionDenied from None
            except (ValidationError, ConflitoAlergiaCritico) as erro:
                mensagens = erro.messages if isinstance(erro, ValidationError) else [str(erro)]
                for msg in mensagens:
                    form.add_error(None, msg)
            else:
                if receita is not None:
                    messages.success(request, 'Receita digital assinada e emitida com sucesso.')
                    return redirect(reverse('prescriptions:detail', kwargs={'prescription_id': receita.pk}))
                if dispatch is not None:
                    messages.warning(request, 'Caso reclassificado para Vermelho. Emergência disparada.')
                else:
                    messages.info(request, 'Caso encaminhado para atendimento síncrono por chat.')
                return redirect(reverse('care:queue_dashboard'))

        ctx = self._carregar_contexto(request, triage_id, form)
        return render(request, self.template_name, ctx)


class PrescriptionRevokeView(LoginRequiredMixin, View):
    def post(self, request: HttpRequest, prescription_id: UUID) -> HttpResponse:
        if request.user.role != User.Role.PROFESSIONAL:
            raise PermissionDenied
        form = PrescriptionRevokeForm(request.POST)
        if form.is_valid():
            try:
                PrescriptionService.revogar_receita(
                    request.user.id,
                    prescription_id,
                    reason=form.cleaned_data['reason'],
                )
            except ReceitaNaoEncontrada:
                raise Http404 from None
            except PermissaoReceitaNegada:
                raise PermissionDenied from None
            except ValidationError as erro:
                messages.error(request, '; '.join(erro.messages))
            else:
                messages.success(request, 'Receita revogada com sucesso.')
        else:
            messages.error(request, 'Informe uma justificativa válida para a revogação.')
        return redirect(reverse('prescriptions:detail', kwargs={'prescription_id': prescription_id}))


class PublicPrescriptionVerifyView(View):
    """Página pública de conferência de autenticidade e dispensação única (Specs 0011/0014).
    Nunca expõe CPF do paciente nem conteúdo clínico da triagem.
    """

    template_name = 'prescriptions/public_verify.html'

    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        try:
            verificacao = PrescriptionService.consultar_autenticidade_publica(token)
        except ReceitaNaoEncontrada:
            return render(
                request,
                self.template_name,
                {'invalida': True, 'verificacao': None, 'form': None},
                status=404,
            )

        return render(
            request,
            self.template_name,
            {
                'invalida': False,
                'verificacao': verificacao,
                'form': PrescriptionDispensationForm() if verificacao.is_valid_for_dispensation else None,
            },
        )

    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        form = PrescriptionDispensationForm(request.POST)
        if form.is_valid():
            try:
                PrescriptionService.dispensar_receita(
                    token,
                    pharmacist_name=form.cleaned_data['pharmacist_name'],
                    crf_number=form.cleaned_data['crf_number'],
                    crf_uf=form.cleaned_data['crf_uf'],
                    pharmacy_cnpj=form.cleaned_data['pharmacy_cnpj'],
                )
            except (ValidationError, DispensacaoRecusada) as erro:
                msg = '; '.join(erro.messages) if isinstance(erro, ValidationError) else str(erro)
                messages.error(request, msg)
            else:
                messages.success(request, 'Dispensação registrada com sucesso.')
                return redirect(reverse('prescriptions:public_verify', kwargs={'token': token}))

        try:
            verificacao = PrescriptionService.consultar_autenticidade_publica(token)
        except ReceitaNaoEncontrada:
            return render(
                request,
                self.template_name,
                {'invalida': True, 'verificacao': None, 'form': None},
                status=404,
            )

        return render(
            request,
            self.template_name,
            {'invalida': False, 'verificacao': verificacao, 'form': form},
        )
