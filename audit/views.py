from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from .forms import AdminAccountCreateForm, AuditSearchForm
from .services import (
    AdminAccountService,
    AuditService,
    OperationalMonitoringService,
    PermissaoAuditoriaNegada,
    UltimoAdministradorAtivo,
)


class HistoricoAcessosView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'
    template_name = 'audit/access_history.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        if not AuditService.administrador_pode_consultar(request.user.pk):
            raise PermissionDenied

        form = AuditSearchForm(request.GET)
        pagina = None
        query_paginacao = request.GET.copy()
        query_paginacao.pop('page', None)
        if form.is_valid():
            filtros = form.cleaned_data
            try:
                pagina = AuditService.listar_tentativas_acesso(
                    actor_id=request.user.pk,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    occurred_from=filtros['periodo_inicial'],
                    occurred_until=filtros['periodo_final'],
                    identificador=filtros['identificador'],
                    papel=filtros['perfil'],
                    resultado=filtros['resultado'],
                    pagina=request.GET.get('page', 1),
                )
            except PermissaoAuditoriaNegada as erro:
                raise PermissionDenied from erro

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'pagina': pagina,
                'query_paginacao': query_paginacao.urlencode(),
            },
        )


class PainelOperacionalView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'
    template_name = 'audit/monitoring.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            metricas = OperationalMonitoringService.obter_metricas_operacionais(request.user.pk)
        except PermissaoAuditoriaNegada:
            raise PermissionDenied from None

        from records.services import MedicalRecordService

        ultimos_acessos_prontuario = MedicalRecordService.listar_logs_acesso()[:20]
        return render(
            request,
            self.template_name,
            {
                'metricas': metricas,
                'ultimos_acessos_prontuario': ultimos_acessos_prontuario,
            },
        )


class GestaoAdministradoresView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'
    template_name = 'audit/admin_accounts.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            admins = AdminAccountService.listar_administradores(request.user.pk)
        except PermissaoAuditoriaNegada:
            raise PermissionDenied from None
        return render(
            request,
            self.template_name,
            {'admins': admins, 'form': AdminAccountCreateForm()},
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = AdminAccountCreateForm(request.POST)
        try:
            admins = AdminAccountService.listar_administradores(request.user.pk)
        except PermissaoAuditoriaNegada:
            raise PermissionDenied from None

        if form.is_valid():
            try:
                AdminAccountService.criar_administrador(
                    request.user.pk,
                    full_name=form.cleaned_data['full_name'],
                    cpf=form.cleaned_data['cpf'],
                    email=form.cleaned_data['email'],
                    birth_date=form.cleaned_data['birth_date'],
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
            except PermissaoAuditoriaNegada:
                raise PermissionDenied from None
            except ValidationError as erro:
                for msg in erro.messages:
                    form.add_error(None, msg)
            else:
                messages.success(
                    request,
                    'Conta administrativa criada com sucesso. Senha provisória enviada ao e-mail corporativo.',
                )
                return redirect(reverse('audit:admin_accounts'))

        return render(
            request,
            self.template_name,
            {'admins': admins, 'form': form},
        )


class DesativarAdministradorView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'

    def post(self, request: HttpRequest, admin_id: int) -> HttpResponse:
        try:
            AdminAccountService.desativar_administrador(
                request.user.pk,
                admin_id,
                ip_address=request.META.get('REMOTE_ADDR'),
            )
        except PermissaoAuditoriaNegada:
            raise PermissionDenied from None
        except (ValidationError, UltimoAdministradorAtivo) as erro:
            msg = '; '.join(erro.messages) if isinstance(erro, ValidationError) else str(erro)
            messages.error(request, msg)
        else:
            messages.success(request, 'Conta administrativa desativada com sucesso.')
        return redirect(reverse('audit:admin_accounts'))
