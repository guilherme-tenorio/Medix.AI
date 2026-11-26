from __future__ import annotations

import ipaddress
import secrets
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.paginator import Page, Paginator
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import salted_hmac

from core.integrations.email import EmailIntegrationDisabled
from users.identifiers import normalizar_identificador as normalizar_id, validar_cpf
from users.services import UserService

from .models import AdministrativeAction, AuditQuery, LoginAttempt

if TYPE_CHECKING:
    from users.models import User


class PermissaoAuditoriaNegada(Exception):
    pass


class UltimoAdministradorAtivo(Exception):
    pass


@dataclass(frozen=True, slots=True)
class OperationalMetrics:
    chat_queue_waiting: int
    prescription_queue_waiting: int
    in_progress_count: int
    avg_wait_minutes: float
    emergencies_last_24h: int
    total_reviews: int
    active_doctors_online: int
    bottleneck_alerts: list[str]


class AuditService:
    @staticmethod
    def fingerprint_identificador(identificador: str) -> str:
        return salted_hmac(
            'medix.login.identifier',
            normalizar_id(identificador),
            secret=settings.SECRET_KEY,
        ).hexdigest()

    @classmethod
    def registrar_tentativa_login(
        cls,
        identificador_normalizado: str,
        resultado: str,
        usuario: User | None = None,
        papel: str = '',
    ) -> LoginAttempt:
        return LoginAttempt.objects.create(
            user=usuario,
            identifier_fingerprint=cls.fingerprint_identificador(identificador_normalizado),
            role=papel,
            result=resultado,
        )

    @staticmethod
    def administrador_pode_consultar(actor_id: int) -> bool:
        return UserService.obter_admin_ativo_por_id(actor_id) is not None

    @staticmethod
    def registrar_acao_administrativa(
        actor_id: int,
        target_id: int,
        action: str,
        ip_address: str | None,
    ) -> AdministrativeAction:
        administrador = UserService.obter_admin_ativo_por_id(actor_id)
        alvo = UserService.obter_por_id(target_id)
        if administrador is None or alvo is None:
            raise PermissaoAuditoriaNegada
        if action not in AdministrativeAction.Action.values:
            raise ValueError('Ação administrativa inválida.')
        return AdministrativeAction.objects.create(
            actor=administrador,
            target=alvo,
            action=action,
            ip_address=AuditService._validar_endereco_ip(ip_address),
        )

    @classmethod
    def listar_tentativas_acesso(
        cls,
        actor_id: int,
        ip_address: str | None,
        occurred_from: datetime | None,
        occurred_until: datetime | None,
        identificador: str,
        papel: str,
        resultado: str,
        pagina: int | str,
    ) -> Page:
        if papel and papel not in LoginAttempt.Role.values:
            raise ValueError('Perfil de auditoria inválido.')
        if resultado and resultado not in LoginAttempt.Result.values:
            raise ValueError('Resultado de auditoria inválido.')

        administrador = UserService.obter_admin_ativo_por_id(actor_id)
        if administrador is None:
            raise PermissaoAuditoriaNegada

        fingerprint = cls.fingerprint_identificador(identificador) if identificador else ''
        with transaction.atomic():
            AuditQuery.objects.create(
                actor=administrador,
                ip_address=cls._validar_endereco_ip(ip_address),
                identifier_fingerprint=fingerprint,
                role_filter=papel,
                result_filter=resultado,
                occurred_from=occurred_from,
                occurred_until=occurred_until,
            )

        tentativas = LoginAttempt.objects.order_by('-occurred_at')
        if occurred_from:
            tentativas = tentativas.filter(occurred_at__gte=occurred_from)
        if occurred_until:
            tentativas = tentativas.filter(occurred_at__lte=occurred_until)
        if fingerprint:
            tentativas = tentativas.filter(identifier_fingerprint=fingerprint)
        if papel:
            tentativas = tentativas.filter(role=papel)
        if resultado:
            tentativas = tentativas.filter(result=resultado)
        return Paginator(tentativas, 50).get_page(pagina)

    @staticmethod
    def _validar_endereco_ip(endereco: str | None) -> str | None:
        if not endereco:
            return None
        try:
            return str(ipaddress.ip_address(endereco))
        except ValueError:
            return None


class AdminAccountService:
    @staticmethod
    def _calcular_idade(birth_date: date) -> int:
        hoje = timezone.localdate()
        anos = hoje.year - birth_date.year
        if (hoje.month, hoje.day) < (birth_date.month, birth_date.day):
            anos -= 1
        return anos

    @classmethod
    def listar_administradores(cls, actor_id: int):
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoAuditoriaNegada
        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        return UserModel.objects.filter(role=UserModel.Role.ADMINISTRATOR).order_by('-is_active', 'first_name', 'email')

    @classmethod
    def criar_administrador(
        cls,
        actor_id: int,
        *,
        full_name: str,
        cpf: str,
        email: str,
        birth_date: date,
        ip_address: str | None = None,
    ):
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoAuditoriaNegada

        nome = (full_name or '').strip()
        if len(nome) < 3 or len(nome) > 120:
            raise ValidationError('O nome completo deve ter entre 3 e 120 caracteres.')
        if birth_date > timezone.localdate() or cls._calcular_idade(birth_date) < 18:
            raise ValidationError('O administrador deve ter pelo menos 18 anos.')
        cpf_limpo = validar_cpf(cpf)
        email_limpo = (email or '').strip().lower()
        if not email_limpo or '@' not in email_limpo:
            raise ValidationError('Informe um e-mail corporativo válido.')

        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        with transaction.atomic():
            if UserService.cpf_existe(cpf_limpo):
                raise ValidationError('Já existe uma conta cadastrada com este CPF.')
            if UserService.email_existe(email_limpo):
                raise ValidationError('Já existe uma conta cadastrada com este e-mail.')

            senha_provisoria = f'Adm!{secrets.token_urlsafe(10)}9A'
            partes = nome.split(None, 1)
            novo_admin = UserModel.objects.create_user(
                username=f'adm-{cpf_limpo}',
                cpf=cpf_limpo,
                email=email_limpo,
                first_name=partes[0],
                last_name=partes[1] if len(partes) > 1 else '',
                role=UserModel.Role.ADMINISTRATOR,
                is_staff=True,
                is_active=True,
                must_change_password=True,
                password=senha_provisoria,
            )
            AuditService.registrar_acao_administrativa(
                actor_id=actor_id,
                target_id=novo_admin.pk,
                action=AdministrativeAction.Action.ADMIN_CREATED,
                ip_address=ip_address,
            )

        try:
            send_mail(
                'Convite administrativo MEDIX.AI — senha provisória',
                (
                    'Sua conta administrativa MEDIX.AI foi criada. '
                    f'Use a senha provisória {senha_provisoria} no primeiro login '
                    'e altere-a imediatamente.'
                ),
                settings.DEFAULT_FROM_EMAIL,
                [email_limpo],
                fail_silently=False,
            )
        except (EmailIntegrationDisabled, OSError):
            pass

        return novo_admin

    @classmethod
    def desativar_administrador(
        cls,
        actor_id: int,
        target_admin_id: int,
        *,
        ip_address: str | None = None,
    ):
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoAuditoriaNegada

        from django.contrib.auth import get_user_model

        UserModel = get_user_model()
        with transaction.atomic():
            admins_ativos = list(
                UserModel.objects.select_for_update()
                .filter(role=UserModel.Role.ADMINISTRATOR, is_active=True)
            )
            alvo = next((u for u in admins_ativos if u.pk == target_admin_id), None)
            if alvo is None:
                raise ValidationError('Administrador ativo não encontrado.')
            if len(admins_ativos) <= 1:
                raise UltimoAdministradorAtivo(
                    'Não é possível desativar o último administrador ativo do sistema.',
                )

            UserService.inativar_usuario(
                alvo.pk,
                actor_id=actor_id,
                ip_address=ip_address,
            )
            AuditService.registrar_acao_administrativa(
                actor_id=actor_id,
                target_id=alvo.pk,
                action=AdministrativeAction.Action.ADMIN_DEACTIVATED,
                ip_address=ip_address,
            )
            alvo.refresh_from_db()
            return alvo


class OperationalMonitoringService:
    @classmethod
    def obter_metricas_operacionais(cls, actor_id: int) -> OperationalMetrics:
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoAuditoriaNegada

        from care.models import ClinicalQueueItem
        from prescriptions.models import PrescriptionReview
        from professionals.models import ProfessionalProfile
        from triage.models import EmergencyDispatch

        agora = timezone.now()
        aguardando = list(
            ClinicalQueueItem.objects.filter(status=ClinicalQueueItem.Status.WAITING)
            .values('queue_type', 'enqueued_at')
        )
        chat_waiting = sum(1 for i in aguardando if i['queue_type'] == ClinicalQueueItem.QueueType.SYNCHRONOUS_CHAT)
        rx_waiting = sum(1 for i in aguardando if i['queue_type'] == ClinicalQueueItem.QueueType.PRESCRIPTION_REVIEW)
        in_progress = ClinicalQueueItem.objects.filter(status=ClinicalQueueItem.Status.IN_PROGRESS).count()

        if aguardando:
            esperas = [(agora - i['enqueued_at']).total_seconds() / 60.0 for i in aguardando]
            avg_wait = round(sum(esperas) / len(esperas), 1)
        else:
            avg_wait = 0.0

        emergencies_24h = EmergencyDispatch.objects.filter(
            created_at__gte=agora - timedelta(hours=24)
        ).count()
        total_reviews = PrescriptionReview.objects.count()
        doctors_online = ProfessionalProfile.objects.filter(
            homologation_status=ProfessionalProfile.HomologationStatus.APPROVED,
            availability=ProfessionalProfile.Availability.ONLINE,
            user__is_active=True,
        ).count()

        alertas: list[str] = []
        if (chat_waiting + rx_waiting) > 0 and doctors_online == 0:
            alertas.append('Fila com chamados aguardando e nenhum médico Online no momento.')
        if avg_wait >= 30.0:
            alertas.append(f'Tempo médio de espera elevado ({avg_wait} min).')

        return OperationalMetrics(
            chat_queue_waiting=chat_waiting,
            prescription_queue_waiting=rx_waiting,
            in_progress_count=in_progress,
            avg_wait_minutes=avg_wait,
            emergencies_last_24h=emergencies_24h,
            total_reviews=total_reviews,
            active_doctors_online=doctors_online,
            bottleneck_alerts=alertas,
        )
