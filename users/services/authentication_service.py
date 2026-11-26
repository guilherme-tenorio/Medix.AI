import binascii
import secrets
import smtplib
import string
from datetime import timedelta
from urllib.parse import urljoin, urlsplit

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.core.exceptions import ValidationError
from django.db import transaction
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils import timezone

from audit.models import AdministrativeAction, LoginAttempt
from audit.services import AuditService, PermissaoAuditoriaNegada
from notifications.services import NotificacaoService
from core.integrations.email import EmailIntegrationDisabled
from users.models import User
from users.identifiers import normalizar_identificador as normalizar_id
from users.services import PermissaoGestaoUsuariosNegada, UserService
from users.services.session_service import SessaoService


class EnvioSenhaTemporariaFalhou(Exception):
    pass


class AutenticacaoService:
    @staticmethod
    def normalizar_identificador(identificador: str) -> str:
        return normalizar_id(identificador)

    @classmethod
    def autenticar(cls, identificador: str, senha: str) -> User | None:
        if not identificador or not senha:
            return None

        identificador_normalizado = cls.normalizar_identificador(identificador)
        agora = timezone.now()

        with transaction.atomic():
            usuario = UserService.buscar_bloqueado_para_atualizacao(
                identificador_normalizado,
            )
            if usuario is None:
                AuditService.registrar_tentativa_login(
                    identificador_normalizado,
                    LoginAttempt.Result.INVALID_CREDENTIALS,
                )
                return None

            if usuario.locked_until and usuario.locked_until > agora:
                AuditService.registrar_tentativa_login(
                    identificador_normalizado,
                    LoginAttempt.Result.LOCKED,
                    usuario,
                    usuario.role,
                )
                return None

            if not usuario.is_active:
                AuditService.registrar_tentativa_login(
                    identificador_normalizado,
                    LoginAttempt.Result.INVALID_CREDENTIALS,
                    usuario,
                    usuario.role,
                )
                return None

            if usuario.locked_until:
                usuario.locked_until = None
                usuario.failed_login_attempts = 0

            if usuario.check_password(senha):
                usuario.failed_login_attempts = 0
                usuario.locked_until = None
                usuario.save(update_fields=('failed_login_attempts', 'locked_until'))
                AuditService.registrar_tentativa_login(
                    identificador_normalizado,
                    LoginAttempt.Result.SUCCESS,
                    usuario,
                    usuario.role,
                )
                return usuario

            usuario.failed_login_attempts += 1
            bloqueada = usuario.failed_login_attempts >= settings.MEDIX_MAX_LOGIN_FAILURES
            if bloqueada:
                usuario.locked_until = agora + timedelta(
                    minutes=settings.MEDIX_LOGIN_LOCKOUT_MINUTES,
                )
            usuario.save(update_fields=('failed_login_attempts', 'locked_until'))

            resultado = (
                LoginAttempt.Result.LOCKED
                if bloqueada
                else LoginAttempt.Result.INVALID_CREDENTIALS
            )
            tentativa = AuditService.registrar_tentativa_login(
                identificador_normalizado,
                resultado,
                usuario,
                usuario.role,
            )
            if bloqueada:
                NotificacaoService.enfileirar_alerta_bloqueio_login(usuario.pk, tentativa.pk)

            return None

    @staticmethod
    def pode_acessar_portal(usuario: User, papel_esperado: str) -> bool:
        return (
            usuario.is_active
            and usuario.role == papel_esperado
            and (papel_esperado != User.Role.ADMINISTRATOR or usuario.is_staff)
        )

    @staticmethod
    def registrar_negacao_portal(usuario: User, papel_esperado: str) -> None:
        permitido = AutenticacaoService.pode_acessar_portal(usuario, papel_esperado)
        if not permitido:
            AuditService.registrar_tentativa_login(
                usuario.cpf,
                LoginAttempt.Result.PORTAL_DENIED,
                usuario,
                papel_esperado,
            )

    @staticmethod
    def obter_usuario_por_id(usuario_id: int) -> User | None:
        return UserService.obter_ativo_por_id(usuario_id)

    @staticmethod
    def trocar_senha(
        usuario_id: int,
        senha_atual: str,
        nova_senha: str,
        session_key: str | None = None,
    ) -> User:
        with transaction.atomic():
            usuario = UserService.obter_para_atualizacao(usuario_id)
            if usuario is None or not usuario.check_password(senha_atual):
                raise ValidationError('A senha atual não confere.', code='invalid_current_password')

            validate_password(nova_senha, usuario)
            usuario.set_password(nova_senha)
            usuario.must_change_password = False
            usuario.failed_login_attempts = 0
            usuario.locked_until = None
            usuario.save(
                update_fields=(
                    'password',
                    'must_change_password',
                    'failed_login_attempts',
                    'locked_until',
                ),
            )
            SessaoService.revogar_sessoes_usuario(
                usuario.pk,
                preservar_chave=session_key,
            )
            return usuario

    @staticmethod
    def solicitar_redefinicao_senha(email: str) -> bool:
        usuario = UserService.obter_paciente_ativo_por_email(email.strip())
        return AutenticacaoService._enviar_link_redefinicao(usuario)

    @staticmethod
    def listar_administradores_para_redefinicao(actor_id: int) -> list[tuple[str, str]]:
        return UserService.listar_administradores_para_redefinicao(actor_id)

    @staticmethod
    def solicitar_redefinicao_administrador(
        actor_id: int,
        target_id: int,
        ip_address: str | None,
    ) -> bool:
        administrador = UserService.obter_admin_ativo_por_id(actor_id)
        if administrador is None:
            raise PermissaoGestaoUsuariosNegada
        if actor_id == target_id:
            return False
        alvo = UserService.obter_admin_ativo_por_id(target_id)
        if alvo is None:
            return False
        try:
            AuditService.registrar_acao_administrativa(
                actor_id,
                target_id,
                AdministrativeAction.Action.ADMIN_PASSWORD_RESET_REQUESTED,
                ip_address,
            )
        except PermissaoAuditoriaNegada as erro:
            raise PermissaoGestaoUsuariosNegada from erro
        return AutenticacaoService._enviar_link_redefinicao(alvo)

    @staticmethod
    def listar_profissionais_para_senha_provisoria(actor_id: int) -> list[tuple[str, str]]:
        return UserService.listar_profissionais_para_senha_provisoria(actor_id)

    @staticmethod
    def emitir_senha_provisoria_medico(
        actor_id: int,
        professional_id: int,
        ip_address: str | None,
    ) -> bool:
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoGestaoUsuariosNegada

        profissional_inicial = UserService.obter_profissional_ativo_por_id(professional_id)
        if profissional_inicial is None:
            return False
        try:
            AuditService.registrar_acao_administrativa(
                actor_id,
                professional_id,
                AdministrativeAction.Action.PROFESSIONAL_TEMP_PASSWORD_REQUESTED,
                ip_address,
            )
        except PermissaoAuditoriaNegada as erro:
            raise PermissaoGestaoUsuariosNegada from erro

        try:
            with transaction.atomic():
                profissional = UserService.obter_profissional_ativo_por_id(
                    professional_id,
                    bloquear=True,
                )
                if profissional is None:
                    return False

                senha_temporaria = AutenticacaoService._gerar_senha_temporaria()
                profissional.set_password(senha_temporaria)
                profissional.must_change_password = True
                profissional.failed_login_attempts = 0
                profissional.locked_until = None
                profissional.save(
                    update_fields=(
                        'password',
                        'must_change_password',
                        'failed_login_attempts',
                        'locked_until',
                    ),
                )
                SessaoService.revogar_sessoes_usuario(profissional.pk)

                try:
                    enviada = send_mail(
                        'Senha provisória MEDIX.AI',
                        (
                            'Um administrador solicitou uma nova senha provisória para sua conta. '
                            f'Senha temporária: {senha_temporaria}\n'
                            'Entre pelo portal médico e altere a senha antes de continuar.'
                        ),
                        settings.DEFAULT_FROM_EMAIL,
                        [profissional.email],
                        fail_silently=False,
                    )
                except (EmailIntegrationDisabled, OSError, smtplib.SMTPException) as erro:
                    raise EnvioSenhaTemporariaFalhou from erro
                if not enviada:
                    raise EnvioSenhaTemporariaFalhou
                return True
        except EnvioSenhaTemporariaFalhou:
            return False

    @staticmethod
    def _gerar_senha_temporaria() -> str:
        simbolos = '!@#$%&*+-_'
        alfabeto = string.ascii_letters + string.digits + simbolos
        caracteres = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(simbolos),
        ]
        caracteres.extend(secrets.choice(alfabeto) for _ in range(28))
        secrets.SystemRandom().shuffle(caracteres)
        return ''.join(caracteres)

    @staticmethod
    def _enviar_link_redefinicao(usuario: User | None) -> bool:
        base_url = settings.MEDIX_PUBLIC_BASE_URL.strip()
        partes_url = urlsplit(base_url)
        if (
            usuario is None
            or partes_url.scheme not in {'http', 'https'}
            or not partes_url.netloc
            or partes_url.username is not None
            or partes_url.password is not None
            or partes_url.query
            or partes_url.fragment
        ):
            return False

        uid = urlsafe_base64_encode(str(usuario.pk).encode())
        token = PasswordResetTokenGenerator().make_token(usuario)
        caminho = reverse(
            'users:password_reset_confirm',
            kwargs={'uidb64': uid, 'token': token},
        )
        base = f"{base_url.rstrip('/')}/"
        link = urljoin(base, caminho.lstrip('/'))
        corpo = (
            'Foi solicitada a redefinição de senha da sua conta MEDIX.AI. '
            f'Use este link em até 30 minutos: {link}\n'
            'Se você não fez esta solicitação, ignore esta mensagem.'
        )
        try:
            return bool(
                send_mail(
                    'Redefinição de senha MEDIX.AI',
                    corpo,
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario.email],
                    fail_silently=False,
                )
            )
        except (EmailIntegrationDisabled, OSError, smtplib.SMTPException):
            return False

    @classmethod
    def usuario_para_redefinicao(cls, uidb64: str, token: str) -> User | None:
        usuario_id = cls._decodificar_uid(uidb64)
        if usuario_id is None:
            return None
        usuario = UserService.obter_conta_para_redefinicao(usuario_id)
        if usuario is None or not PasswordResetTokenGenerator().check_token(usuario, token):
            return None
        return usuario

    @classmethod
    def redefinir_senha(
        cls,
        uidb64: str,
        token: str,
        nova_senha: str,
    ) -> User:
        usuario_id = cls._decodificar_uid(uidb64)
        if usuario_id is None:
            raise ValidationError('O link de redefinição é inválido ou expirou.')

        with transaction.atomic():
            usuario = UserService.obter_conta_para_redefinicao(usuario_id, bloquear=True)
            if usuario is None or not PasswordResetTokenGenerator().check_token(usuario, token):
                raise ValidationError('O link de redefinição é inválido ou expirou.')

            validate_password(nova_senha, usuario)
            usuario.set_password(nova_senha)
            usuario.must_change_password = False
            usuario.failed_login_attempts = 0
            usuario.locked_until = None
            usuario.save(
                update_fields=(
                    'password',
                    'must_change_password',
                    'failed_login_attempts',
                    'locked_until',
                ),
            )
            SessaoService.revogar_sessoes_usuario(usuario.pk)
            return usuario

    @staticmethod
    def _decodificar_uid(uidb64: str) -> int | None:
        try:
            usuario_id = force_str(urlsafe_base64_decode(uidb64))
        except (binascii.Error, UnicodeDecodeError, ValueError, TypeError):
            return None
        if not usuario_id.isdecimal():
            return None
        return int(usuario_id)
