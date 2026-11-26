from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from users.models import User

from .forms import (
    DependentCreateForm,
    DependentUpdateForm,
    PatientRegistrationForm,
    PatientUpdateForm,
    SmsCodeRequestForm,
)
from .services import (
    DependentService,
    DependenteNaoEncontrado,
    PatientService,
    PermissaoPacienteNegada,
    SmsVerificationService,
)


def _garantir_paciente(request: HttpRequest) -> None:
    if request.user.role != User.Role.PATIENT:
        raise PermissionDenied


class SolicitarCodigoSmsView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        form = SmsCodeRequestForm(request.POST)
        if form.is_valid():
            try:
                SmsVerificationService.enviar_codigo(form.cleaned_data['phone'])
            except ValidationError as erro:
                messages.error(request, '; '.join(erro.messages))
            else:
                from django.conf import settings
                from core.integrations.sms import SandboxSmsAdapter

                if settings.DEBUG and form.cleaned_data['phone']:
                    from users.identifiers import normalizar_celular

                    tel_norm = normalizar_celular(form.cleaned_data['phone'])
                    codigo_dev = SandboxSmsAdapter.sent_codes.get(tel_norm)
                    if codigo_dev:
                        messages.info(
                            request,
                            f'[MODO DEV] Código SMS gerado para teste: {codigo_dev}',
                        )
                messages.success(request, 'Código de verificação SMS enviado para o celular informado.')
        else:
            messages.error(request, 'Informe um celular válido com DDD.')
        return redirect(reverse('patients:register'))


class CadastroPacienteView(View):
    template_name = 'patients/register.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect(reverse('users:patient_portal'))
        return render(
            request,
            self.template_name,
            {
                'form': PatientRegistrationForm(),
                'sms_form': SmsCodeRequestForm(),
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            raise PermissionDenied
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            try:
                PatientService.cadastrar_titular(
                    form.cleaned_data,
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
            except ValidationError as erro:
                for mensagem in erro.messages:
                    form.add_error(None, mensagem)
            else:
                messages.success(request, 'Cadastro concluído com sucesso. Faça login para continuar.')
                return redirect(reverse('users:patient_login'))

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'sms_form': SmsCodeRequestForm(initial={'phone': request.POST.get('phone', '')}),
            },
        )


class PerfilPacienteView(LoginRequiredMixin, View):
    login_url = 'users:patient_login'
    template_name = 'patients/profile.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        paciente = PatientService.obter_perfil_por_usuario(request.user.pk)
        if paciente is None:
            raise Http404
        clinico = paciente.clinical_profile
        form = PatientUpdateForm(
            initial={
                'full_name': paciente.user.get_full_name(),
                'birth_date': paciente.birth_date,
                'gender': paciente.gender,
                'phone': paciente.phone,
                'has_disability': clinico.has_disability,
                'disability_description': clinico.disability_description,
                'blood_type': clinico.blood_type,
                'has_allergy': clinico.has_allergy,
                'allergy_description': clinico.allergy_description,
                'continuous_medications': clinico.continuous_medications,
                'height_cm': clinico.height_cm,
                'weight_kg': clinico.weight_kg,
                'has_hypertension': clinico.has_hypertension,
                'has_diabetes': clinico.has_diabetes,
            }
        )
        return render(request, self.template_name, {'form': form, 'paciente': paciente})

    def post(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        form = PatientUpdateForm(request.POST)
        paciente = PatientService.obter_perfil_por_usuario(request.user.pk)
        if paciente is None:
            raise Http404
        if form.is_valid():
            try:
                PatientService.atualizar_titular_e_perfil(request.user.pk, form.cleaned_data)
            except PermissaoPacienteNegada as erro:
                raise PermissionDenied from erro
            except ValidationError as erro:
                for mensagem in erro.messages:
                    form.add_error(None, mensagem)
            else:
                messages.success(request, 'Dados cadastrais e perfil clínico atualizados.')
                return redirect(reverse('patients:profile'))
        return render(request, self.template_name, {'form': form, 'paciente': paciente})


class ListaDependentesView(LoginRequiredMixin, View):
    login_url = 'users:patient_login'
    template_name = 'patients/dependents_list.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        try:
            dependentes = DependentService.listar_dependentes(request.user.pk)
        except PermissaoPacienteNegada as erro:
            raise PermissionDenied from erro
        responsavel = PatientService.obter_perfil_por_usuario(request.user.pk)
        return render(
            request,
            self.template_name,
            {'dependentes': dependentes, 'responsavel': responsavel},
        )


class CadastrarDependenteView(LoginRequiredMixin, View):
    login_url = 'users:patient_login'
    template_name = 'patients/dependent_form.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        responsavel = PatientService.obter_perfil_por_usuario(request.user.pk)
        if responsavel is None:
            raise PermissionDenied
        return render(
            request,
            self.template_name,
            {
                'form': DependentCreateForm(),
                'responsavel': responsavel,
                'modo_edicao': False,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        _garantir_paciente(request)
        responsavel = PatientService.obter_perfil_por_usuario(request.user.pk)
        if responsavel is None:
            raise PermissionDenied
        form = DependentCreateForm(request.POST)
        if form.is_valid():
            try:
                DependentService.cadastrar_dependente(request.user.pk, form.cleaned_data)
            except PermissaoPacienteNegada as erro:
                raise PermissionDenied from erro
            except ValidationError as erro:
                for mensagem in erro.messages:
                    form.add_error(None, mensagem)
            else:
                messages.success(request, 'Dependente cadastrado com sucesso.')
                return redirect(reverse('patients:dependents_list'))

        return render(
            request,
            self.template_name,
            {'form': form, 'responsavel': responsavel, 'modo_edicao': False},
        )


class EditarDependenteView(LoginRequiredMixin, View):
    login_url = 'users:patient_login'
    template_name = 'patients/dependent_form.html'

    def get(self, request: HttpRequest, dependent_id: int) -> HttpResponse:
        _garantir_paciente(request)
        try:
            dependente = DependentService.obter_dependente(request.user.pk, dependent_id)
        except PermissaoPacienteNegada as erro:
            raise PermissionDenied from erro
        except DependenteNaoEncontrado as erro:
            raise Http404 from erro

        clinico = dependente.clinical_profile
        form = DependentUpdateForm(
            initial={
                'legal_relationship': dependente.legal_relationship,
                'full_name': dependente.full_name,
                'birth_date': dependente.birth_date,
                'gender': dependente.gender,
                'has_disability': clinico.has_disability,
                'disability_description': clinico.disability_description,
                'blood_type': clinico.blood_type,
                'has_allergy': clinico.has_allergy,
                'allergy_description': clinico.allergy_description,
                'continuous_medications': clinico.continuous_medications,
                'height_cm': clinico.height_cm,
                'weight_kg': clinico.weight_kg,
                'has_hypertension': clinico.has_hypertension,
                'has_diabetes': clinico.has_diabetes,
            }
        )
        return render(
            request,
            self.template_name,
            {
                'form': form,
                'dependente': dependente,
                'responsavel': dependente.guardian,
                'modo_edicao': True,
            },
        )

    def post(self, request: HttpRequest, dependent_id: int) -> HttpResponse:
        _garantir_paciente(request)
        try:
            dependente = DependentService.obter_dependente(request.user.pk, dependent_id)
        except PermissaoPacienteNegada as erro:
            raise PermissionDenied from erro
        except DependenteNaoEncontrado as erro:
            raise Http404 from erro

        form = DependentUpdateForm(request.POST)
        if form.is_valid():
            try:
                DependentService.atualizar_dependente(request.user.pk, dependent_id, form.cleaned_data)
            except PermissaoPacienteNegada as erro:
                raise PermissionDenied from erro
            except DependenteNaoEncontrado as erro:
                raise Http404 from erro
            except ValidationError as erro:
                for mensagem in erro.messages:
                    form.add_error(None, mensagem)
            else:
                messages.success(request, 'Dados do dependente atualizados.')
                return redirect(reverse('patients:dependents_list'))

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'dependente': dependente,
                'responsavel': dependente.guardian,
                'modo_edicao': True,
            },
        )


class DesativarDependenteView(LoginRequiredMixin, View):
    login_url = 'users:patient_login'

    def post(self, request: HttpRequest, dependent_id: int) -> HttpResponse:
        _garantir_paciente(request)
        try:
            DependentService.desativar_dependente(request.user.pk, dependent_id)
        except PermissaoPacienteNegada as erro:
            raise PermissionDenied from erro
        except DependenteNaoEncontrado as erro:
            raise Http404 from erro
        messages.success(request, 'Dependente desativado com preservação do histórico.')
        return redirect(reverse('patients:dependents_list'))
