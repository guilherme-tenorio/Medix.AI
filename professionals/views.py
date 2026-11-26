from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from users.models import User
from users.services import PermissaoGestaoUsuariosNegada

from .forms import (
    ProfessionalAvailabilityForm,
    ProfessionalCreateForm,
    ProfessionalHomologateForm,
)
from .services import (
    PermissaoProfissionalNegada,
    ProfessionalService,
    ProfissionalNaoEncontrado,
)


class AdminGestaoMedicosView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'
    template_name = 'professionals/admin_list.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            profissionais = ProfessionalService.listar_profissionais(request.user.pk)
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro
        return render(
            request,
            self.template_name,
            {
                'profissionais': profissionais,
                'form': ProfessionalCreateForm(),
                'homologate_form': ProfessionalHomologateForm(),
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = ProfessionalCreateForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                ProfessionalService.cadastrar_profissional(
                    request.user.pk,
                    form.cleaned_data,
                    form.cleaned_data['crm_document'],
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
            except PermissaoGestaoUsuariosNegada as erro:
                raise PermissionDenied from erro
            except ValidationError as erro:
                for mensagem in erro.messages:
                    form.add_error(None, mensagem)
            else:
                messages.success(request, 'Médico cadastrado como pendente de homologação.')
                return redirect(reverse('professionals:admin_list'))

        try:
            profissionais = ProfessionalService.listar_profissionais(request.user.pk)
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro
        return render(
            request,
            self.template_name,
            {
                'profissionais': profissionais,
                'form': form,
                'homologate_form': ProfessionalHomologateForm(),
            },
        )


class AdminHomologarMedicoView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'

    def post(self, request: HttpRequest, professional_id: int) -> HttpResponse:
        form = ProfessionalHomologateForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Confirme a regularidade do CRM antes de homologar.')
            return redirect(reverse('professionals:admin_list'))
        try:
            _, enviada = ProfessionalService.homologar_profissional(
                request.user.pk,
                professional_id,
                crm_regular=form.cleaned_data['crm_regular'],
                icp_brasil_active=form.cleaned_data['icp_brasil_active'],
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro
        except ProfissionalNaoEncontrado as erro:
            raise Http404 from erro
        except ValidationError as erro:
            messages.error(request, '; '.join(erro.messages))
        else:
            if enviada:
                messages.success(request, 'Médico homologado e convite com senha provisória enviado.')
            else:
                messages.warning(
                    request,
                    'Médico homologado, mas o envio de e-mail da senha provisória falhou.',
                )
        return redirect(reverse('professionals:admin_list'))


class AdminSuspenderMedicoView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'

    def post(self, request: HttpRequest, professional_id: int) -> HttpResponse:
        try:
            ProfessionalService.suspender_profissional(
                request.user.pk,
                professional_id,
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro
        except ProfissionalNaoEncontrado as erro:
            raise Http404 from erro
        messages.success(request, 'Médico suspenso e sessões revogadas imediatamente.')
        return redirect(reverse('professionals:admin_list'))


class DisponibilidadeMedicoView(LoginRequiredMixin, View):
    login_url = 'users:professional_login'
    template_name = 'professionals/availability.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.role != User.Role.PROFESSIONAL:
            raise PermissionDenied
        perfil = ProfessionalService.obter_por_usuario(request.user.pk)
        if perfil is None:
            raise PermissionDenied
        form = ProfessionalAvailabilityForm(
            initial={
                'availability': perfil.availability,
                'operational_phone': perfil.operational_phone,
            }
        )
        return render(request, self.template_name, {'form': form, 'perfil': perfil})

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.role != User.Role.PROFESSIONAL:
            raise PermissionDenied
        perfil = ProfessionalService.obter_por_usuario(request.user.pk)
        if perfil is None:
            raise PermissionDenied
        form = ProfessionalAvailabilityForm(request.POST)
        if form.is_valid():
            try:
                ProfessionalService.alterar_disponibilidade(
                    request.user.pk,
                    form.cleaned_data['availability'],
                    operational_phone=form.cleaned_data['operational_phone'],
                )
            except PermissaoProfissionalNegada as erro:
                raise PermissionDenied from erro
            except ValidationError as erro:
                for mensagem in erro.messages:
                    form.add_error(None, mensagem)
            else:
                messages.success(request, 'Disponibilidade atualizada.')
                return redirect(reverse('professionals:availability'))
        return render(request, self.template_name, {'form': form, 'perfil': perfil})
