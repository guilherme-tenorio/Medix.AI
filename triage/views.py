from uuid import UUID

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from patients.services import DependentService, PermissaoPacienteNegada
from users.models import User

from .forms import EmergencyLocationForm, TriageAnswersForm, TriageStartForm
from .services import (
    EmergenciaNaoEncontrada,
    EmergencyService,
    PermissaoTriagemNegada,
    TriageService,
    TriagemImutavel,
    TriagemIndisponivel,
    TriagemNaoEncontrada,
)


def _garantir_paciente(request: HttpRequest) -> None:
    if request.user.role != User.Role.PATIENT:
        raise PermissionDenied


class TriageListView(LoginRequiredMixin, View):
    template_name = 'triage/list.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        triagens = TriageService.listar_triagens_usuario(request.user.id)
        try:
            dependentes = DependentService.listar_dependentes(request.user.id)
        except PermissaoPacienteNegada:
            dependentes = []
        return render(
            request,
            self.template_name,
            {
                'triagens': triagens,
                'dependentes': dependentes,
            },
        )


class TriageStartView(LoginRequiredMixin, View):
    template_name = 'triage/start.html'

    def _obter_dependent_id(self, request: HttpRequest) -> int | None:
        raw = request.GET.get('dependent_id') or request.POST.get('dependent_id')
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            raise Http404 from None

    def get(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        dependent_id = self._obter_dependent_id(request)
        try:
            sujeito = TriageService.obter_alvo_autorizado(
                request.user.id,
                dependent_id=dependent_id,
            )
        except PermissaoTriagemNegada:
            raise PermissionDenied from None
        except ValidationError as erro:
            messages.error(request, '; '.join(erro.messages))
            return redirect(reverse('patients:profile'))

        form = TriageStartForm(initial={'dependent_id': dependent_id})
        return render(
            request,
            self.template_name,
            {'form': form, 'sujeito': sujeito},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        dependent_id = self._obter_dependent_id(request)
        try:
            sujeito = TriageService.obter_alvo_autorizado(
                request.user.id,
                dependent_id=dependent_id,
            )
        except PermissaoTriagemNegada:
            raise PermissionDenied from None

        form = TriageStartForm(request.POST)
        if form.is_valid():
            try:
                sessao, dispatch = TriageService.iniciar_triagem(
                    request.user.id,
                    symptoms_description=form.cleaned_data['symptoms_description'],
                    symptom_onset=form.cleaned_data['symptom_onset'],
                    pain_intensity=form.cleaned_data['pain_intensity'],
                    dependent_id=dependent_id,
                    identity_confirmed=form.cleaned_data['identity_confirmed'],
                )
            except (ValidationError, TriagemIndisponivel) as erro:
                mensagens = erro.messages if isinstance(erro, ValidationError) else [str(erro)]
                for msg in mensagens:
                    form.add_error(None, msg)
            except PermissaoTriagemNegada:
                raise PermissionDenied from None
            else:
                if dispatch is not None:
                    return redirect(reverse('triage:emergency', kwargs={'dispatch_id': dispatch.pk}))
                return redirect(reverse('triage:detail', kwargs={'triage_id': sessao.pk}))

        return render(
            request,
            self.template_name,
            {'form': form, 'sujeito': sujeito},
        )


class TriageDetailView(LoginRequiredMixin, View):
    template_name = 'triage/detail.html'

    def get(self, request: HttpRequest, triage_id: UUID) -> HttpResponse:
        _garantir_paciente(request)
        try:
            sessao = TriageService.obter_triagem(request.user.id, triage_id)
        except TriagemNaoEncontrada:
            raise Http404 from None
        except PermissaoTriagemNegada:
            raise PermissionDenied from None

        perguntas = (sessao.answers or {}).get('questions', [])
        return render(
            request,
            self.template_name,
            {
                'sessao': sessao,
                'perguntas': perguntas,
                'form': TriageAnswersForm(),
            },
        )

    def post(self, request: HttpRequest, triage_id: UUID) -> HttpResponse:
        _garantir_paciente(request)
        try:
            sessao = TriageService.obter_triagem(request.user.id, triage_id)
        except TriagemNaoEncontrada:
            raise Http404 from None
        except PermissaoTriagemNegada:
            raise PermissionDenied from None

        form = TriageAnswersForm(request.POST)
        if form.is_valid():
            respostas = {
                'pergunta_1': form.cleaned_data['answer_1'],
                'pergunta_2': form.cleaned_data.get('answer_2', ''),
            }
            try:
                sessao, dispatch = TriageService.concluir_triagem(
                    request.user.id,
                    triage_id,
                    responses=respostas,
                )
            except TriagemImutavel as erro:
                messages.warning(request, str(erro))
                return redirect(reverse('triage:detail', kwargs={'triage_id': triage_id}))
            except PermissaoTriagemNegada:
                raise PermissionDenied from None
            else:
                if dispatch is not None:
                    return redirect(reverse('triage:emergency', kwargs={'dispatch_id': dispatch.pk}))
                messages.success(request, 'Triagem concluída com sucesso.')
                return redirect(reverse('triage:detail', kwargs={'triage_id': sessao.pk}))

        perguntas = (sessao.answers or {}).get('questions', [])
        return render(
            request,
            self.template_name,
            {
                'sessao': sessao,
                'perguntas': perguntas,
                'form': form,
            },
        )


class EmergencyDispatchView(LoginRequiredMixin, View):
    template_name = 'triage/emergency.html'

    def get(self, request: HttpRequest, dispatch_id: UUID) -> HttpResponse:
        _garantir_paciente(request)
        try:
            dispatch = EmergencyService.obter_emergencia_autorizada(request.user.id, dispatch_id)
        except EmergenciaNaoEncontrada:
            raise Http404 from None
        except PermissaoTriagemNegada:
            raise PermissionDenied from None

        unidades = EmergencyService.buscar_unidades_proximas(dispatch)
        form = EmergencyLocationForm(
            initial={
                'latitude': dispatch.latitude,
                'longitude': dispatch.longitude,
                'manual_location_query': dispatch.manual_location_query,
            }
        )
        return render(
            request,
            self.template_name,
            {
                'dispatch': dispatch,
                'unidades': unidades,
                'form': form,
            },
        )

    def post(self, request: HttpRequest, dispatch_id: UUID) -> HttpResponse:
        _garantir_paciente(request)
        form = EmergencyLocationForm(request.POST)
        if form.is_valid():
            try:
                dispatch, unidades = EmergencyService.atualizar_localizacao(
                    request.user.id,
                    dispatch_id,
                    latitude=form.cleaned_data.get('latitude'),
                    longitude=form.cleaned_data.get('longitude'),
                    manual_location_query=form.cleaned_data.get('manual_location_query', ''),
                )
            except EmergenciaNaoEncontrada:
                raise Http404 from None
            except PermissaoTriagemNegada:
                raise PermissionDenied from None
            except ValidationError as erro:
                for msg in erro.messages:
                    form.add_error(None, msg)
                dispatch = EmergencyService.obter_emergencia_autorizada(request.user.id, dispatch_id)
                unidades = EmergencyService.buscar_unidades_proximas(dispatch)
            else:
                messages.success(request, 'Lista de unidades de emergência atualizada.')
        else:
            try:
                dispatch = EmergencyService.obter_emergencia_autorizada(request.user.id, dispatch_id)
            except EmergenciaNaoEncontrada:
                raise Http404 from None
            except PermissaoTriagemNegada:
                raise PermissionDenied from None
            unidades = EmergencyService.buscar_unidades_proximas(dispatch)

        return render(
            request,
            self.template_name,
            {
                'dispatch': dispatch,
                'unidades': unidades,
                'form': form,
            },
        )
