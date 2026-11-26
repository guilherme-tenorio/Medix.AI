from django.contrib.auth import login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from .forms import (
    EmitirSenhaProvisoriaForm,
    PortalLoginForm,
    RedefinirSenhaForm,
    SolicitarRedefinicaoAdministradorForm,
    SolicitarRedefinicaoSenhaForm,
    TrocarSenhaForm,
)
from .models import User
from .services import PermissaoGestaoUsuariosNegada
from .services.authentication_service import AutenticacaoService


class PortalLoginView(View):
    papel = ''
    nome_portal = ''
    template_name = 'users/login.html'
    success_url_name = ''
    habilitar_recuperacao = False
    orientacao_senha = ''

    def get_success_url(self) -> str:
        return reverse(self.success_url_name)

    def get(self, request: HttpRequest) -> HttpResponse:
        if request.user.is_authenticated:
            if not AutenticacaoService.pode_acessar_portal(request.user, self.papel):
                AutenticacaoService.registrar_negacao_portal(request.user, self.papel)
                raise PermissionDenied
            return redirect(self.get_success_url())

        return render(
            request,
            self.template_name,
            {
                'form': PortalLoginForm(request=request),
                'nome_portal': self.nome_portal,
                'habilitar_recuperacao': self.habilitar_recuperacao,
                'orientacao_senha': self.orientacao_senha,
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        form = PortalLoginForm(request=request, data=request.POST)
        if form.is_valid():
            usuario = form.get_user()
            if not AutenticacaoService.pode_acessar_portal(usuario, self.papel):
                AutenticacaoService.registrar_negacao_portal(usuario, self.papel)
                raise PermissionDenied
            login(request, usuario, backend='users.backends.CpfEmailBackend')
            return redirect(self.get_success_url())

        form.marcar_erros_acessiveis()
        return render(
            request,
            self.template_name,
            {
                'form': form,
                'nome_portal': self.nome_portal,
                'habilitar_recuperacao': self.habilitar_recuperacao,
                'orientacao_senha': self.orientacao_senha,
            },
        )


class PatientLoginView(PortalLoginView):
    papel = User.Role.PATIENT
    nome_portal = 'Paciente e responsável'
    success_url_name = 'users:patient_portal'
    habilitar_recuperacao = True


class ProfessionalLoginView(PortalLoginView):
    papel = User.Role.PROFESSIONAL
    nome_portal = 'Área médica'
    success_url_name = 'users:professional_portal'
    orientacao_senha = 'Para solicitar uma nova senha provisória, fale com o administrador da plataforma.'


class AdministratorLoginView(PortalLoginView):
    papel = User.Role.ADMINISTRATOR
    nome_portal = 'Administração'
    success_url_name = 'admin:index'
    orientacao_senha = 'Solicite a redefinição a outro administrador ativo da plataforma.'

    def get_success_url(self) -> str:
        return reverse('admin:index')


class PortalHomeView(View):
    papel = ''
    nome_portal = ''
    login_url_name = ''

    def get(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect(reverse(self.login_url_name))
        if not AutenticacaoService.pode_acessar_portal(request.user, self.papel):
            AutenticacaoService.registrar_negacao_portal(request.user, self.papel)
            raise PermissionDenied

        contexto = {'nome_portal': self.nome_portal}
        if request.user.role == User.Role.PATIENT:
            from care.services import ChatService
            from notifications.services import NotificacaoService

            contexto['chats_paciente'] = ChatService.listar_sessoes_paciente(request.user.id)[:5]
            contexto['notificacoes_nao_lidas'] = NotificacaoService.listar_central_usuario(
                request.user.id
            ).filter(read_at__isnull=True).count()
        elif request.user.role == User.Role.PROFESSIONAL:
            from professionals.services import ProfessionalService

            contexto['perfil_medico'] = ProfessionalService.obter_por_usuario(request.user.id)
        return render(request, 'users/portal_home.html', contexto)


class PatientPortalView(PortalHomeView):
    papel = User.Role.PATIENT
    nome_portal = 'Portal do paciente'
    login_url_name = 'users:patient_login'


class ProfessionalPortalView(PortalHomeView):
    papel = User.Role.PROFESSIONAL
    nome_portal = 'Portal médico'
    login_url_name = 'users:professional_login'


class LogoutView(View):
    def post(self, request: HttpRequest) -> HttpResponse:
        logout(request)
        return redirect(reverse('users:patient_login'))


class TrocarSenhaView(LoginRequiredMixin, View):
    login_url = 'users:patient_login'
    template_name = 'users/change_password.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {'form': TrocarSenhaForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = TrocarSenhaForm(request.POST)
        if form.is_valid():
            try:
                usuario = AutenticacaoService.trocar_senha(
                    request.user.pk,
                    form.cleaned_data['senha_atual'],
                    form.cleaned_data['nova_senha'],
                    request.session.session_key,
                )
            except ValidationError as erro:
                form.add_error(None, erro)
            else:
                update_session_auth_hash(request, usuario)
                return redirect(self._obter_rota_portal(usuario))

        return render(request, self.template_name, {'form': form})

    @staticmethod
    def _obter_rota_portal(usuario: User) -> str:
        if usuario.role == User.Role.PROFESSIONAL:
            return reverse('users:professional_portal')
        if usuario.role == User.Role.ADMINISTRATOR:
            return reverse('admin:index')
        return reverse('users:patient_portal')


class SolicitarRedefinicaoSenhaView(View):
    template_name = 'users/password_reset_request.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, self.template_name, {'form': SolicitarRedefinicaoSenhaForm()})

    def post(self, request: HttpRequest) -> HttpResponse:
        form = SolicitarRedefinicaoSenhaForm(request.POST)
        if form.is_valid():
            AutenticacaoService.solicitar_redefinicao_senha(form.cleaned_data['email'])
            return redirect(reverse('users:password_reset_sent'))
        return render(request, self.template_name, {'form': form})


@method_decorator(never_cache, name='dispatch')
class RedefinirSenhaView(View):
    template_name = 'users/password_reset_confirm.html'

    def get(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        valido = AutenticacaoService.usuario_para_redefinicao(uidb64, token) is not None
        return render(
            request,
            self.template_name,
            {'form': RedefinirSenhaForm() if valido else None, 'link_valido': valido},
        )

    def post(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        form = RedefinirSenhaForm(request.POST)
        if form.is_valid():
            try:
                AutenticacaoService.redefinir_senha(
                    uidb64,
                    token,
                    form.cleaned_data['nova_senha'],
                )
            except ValidationError as erro:
                form.add_error(None, erro)
            else:
                return redirect(reverse('users:password_reset_complete'))

        valido = AutenticacaoService.usuario_para_redefinicao(uidb64, token) is not None
        return render(
            request,
            self.template_name,
            {'form': form if valido else None, 'link_valido': valido},
        )


class RedefinirSenhaEnviadoView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, 'users/password_reset_sent.html')


class RedefinirSenhaConcluidoView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return render(request, 'users/password_reset_complete.html')


class RedirecionarTrocaSenhaAdminView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        return redirect(reverse('users:password_change'))


class SolicitarRedefinicaoAdministradorView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'
    template_name = 'users/admin_password_reset_request.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        choices = self._obter_administradores(request.user.pk)
        return render(
            request,
            self.template_name,
            {
                'form': SolicitarRedefinicaoAdministradorForm(choices=choices),
                'ha_administradores': bool(choices),
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        choices = self._obter_administradores(request.user.pk)
        form = SolicitarRedefinicaoAdministradorForm(request.POST, choices=choices)
        if not choices:
            return render(
                request,
                self.template_name,
                {'form': form, 'ha_administradores': False},
            )
        if form.is_valid():
            try:
                enviado = AutenticacaoService.solicitar_redefinicao_administrador(
                    request.user.pk,
                    int(form.cleaned_data['administrador_id']),
                    request.META.get('REMOTE_ADDR'),
                )
            except PermissaoGestaoUsuariosNegada as erro:
                raise PermissionDenied from erro
            if enviado:
                return redirect(reverse('users:admin_password_reset_sent'))
            form.add_error(
                None,
                'O envio não foi concluído. Verifique a configuração do e-mail e tente novamente.',
            )

        return render(
            request,
            self.template_name,
            {'form': form, 'ha_administradores': True},
        )

    @staticmethod
    def _obter_administradores(actor_id: int) -> list[tuple[str, str]]:
        try:
            return AutenticacaoService.listar_administradores_para_redefinicao(actor_id)
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro


class RedefinicaoAdministradorEnviadaView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            AutenticacaoService.listar_administradores_para_redefinicao(request.user.pk)
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro
        return render(request, 'users/admin_password_reset_sent.html')


class EmitirSenhaProvisoriaMedicoView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'
    template_name = 'users/professional_temporary_password.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        choices = self._obter_profissionais(request.user.pk)
        return render(
            request,
            self.template_name,
            {
                'form': EmitirSenhaProvisoriaForm(choices=choices),
                'ha_profissionais': bool(choices),
            },
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        choices = self._obter_profissionais(request.user.pk)
        form = EmitirSenhaProvisoriaForm(request.POST, choices=choices)
        if not choices:
            return render(
                request,
                self.template_name,
                {'form': form, 'ha_profissionais': False},
            )
        if form.is_valid():
            try:
                enviada = AutenticacaoService.emitir_senha_provisoria_medico(
                    request.user.pk,
                    int(form.cleaned_data['profissional_id']),
                    request.META.get('REMOTE_ADDR'),
                )
            except PermissaoGestaoUsuariosNegada as erro:
                raise PermissionDenied from erro
            if enviada:
                return redirect(reverse('users:professional_temporary_password_sent'))
            form.add_error(
                None,
                'A senha não foi alterada porque o envio de e-mail não foi concluído.',
            )

        return render(
            request,
            self.template_name,
            {'form': form, 'ha_profissionais': True},
        )

    @staticmethod
    def _obter_profissionais(actor_id: int) -> list[tuple[str, str]]:
        try:
            return AutenticacaoService.listar_profissionais_para_senha_provisoria(actor_id)
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro


class SenhaProvisoriaMedicoEnviadaView(LoginRequiredMixin, View):
    login_url = 'users:administrator_login'

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            AutenticacaoService.listar_profissionais_para_senha_provisoria(request.user.pk)
        except PermissaoGestaoUsuariosNegada as erro:
            raise PermissionDenied from erro
        return render(request, 'users/professional_temporary_password_sent.html')
