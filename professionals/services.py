from __future__ import annotations

from datetime import date
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from audit.models import AdministrativeAction
from audit.services import AuditService
from users.identifiers import normalizar_celular, validar_cpf
from users.services import PermissaoGestaoUsuariosNegada, UserService
from users.services.authentication_service import AutenticacaoService

from .models import ProfessionalProfile, ShiftHistory

ALLOWED_CRM_DOC_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg'}
MAX_CRM_DOC_BYTES = 10 * 1024 * 1024
UFS_BRASIL = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO',
    'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI',
    'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
}


class ProfissionalNaoEncontrado(Exception):
    pass


class PermissaoProfissionalNegada(Exception):
    pass


class ProfessionalService:
    @staticmethod
    def _exigir_admin(actor_id: int) -> None:
        if UserService.obter_admin_ativo_por_id(actor_id) is None:
            raise PermissaoGestaoUsuariosNegada

    @staticmethod
    def _validar_documento_crm(documento) -> None:
        if documento is None:
            raise ValidationError('O comprovante de CRM (PDF, PNG ou JPEG) é obrigatório.')
        extensao = Path(documento.name).suffix.lower()
        if extensao not in ALLOWED_CRM_DOC_EXTENSIONS:
            raise ValidationError('O comprovante de CRM deve ser PDF, PNG ou JPEG.')
        if getattr(documento, 'size', 0) > MAX_CRM_DOC_BYTES:
            raise ValidationError('O comprovante de CRM deve ter no máximo 10 MB.')

    @staticmethod
    def _validar_nascimento_medico(birth_date: date) -> date:
        hoje = timezone.localdate()
        if birth_date > hoje:
            raise ValidationError('A data de nascimento não pode ser futura.')
        idade = hoje.year - birth_date.year - (
            (hoje.month, hoje.day) < (birth_date.month, birth_date.day)
        )
        if idade < 21:
            raise ValidationError('A idade informada é incompatível com a formação médica.')
        return birth_date

    @classmethod
    def listar_profissionais(cls, actor_id: int) -> QuerySet[ProfessionalProfile]:
        cls._exigir_admin(actor_id)
        return ProfessionalProfile.objects.select_related('user').order_by('user__first_name', 'user__last_name')

    @classmethod
    def cadastrar_profissional(
        cls,
        actor_id: int,
        dados: dict,
        crm_document,
        ip_address: str | None = None,
    ) -> ProfessionalProfile:
        cls._exigir_admin(actor_id)
        cpf = validar_cpf(dados.get('cpf', ''))
        full_name = (dados.get('full_name') or '').strip()
        if len(full_name) < 3 or len(full_name) > 120:
            raise ValidationError('O nome deve ter entre 3 e 120 caracteres.')

        birth_date = cls._validar_nascimento_medico(dados['birth_date'])
        phone = normalizar_celular(dados.get('phone', ''))
        email = (dados.get('email') or '').strip().casefold()
        if not email:
            raise ValidationError('Informe um e-mail corporativo válido.')

        crm_number = ''.join(ch for ch in (dados.get('crm_number') or '').strip() if ch.isalnum())
        crm_uf = (dados.get('crm_uf') or '').strip().upper()
        if not crm_number or crm_uf not in UFS_BRASIL:
            raise ValidationError('Informe número de CRM e UF válidos.')

        cls._validar_documento_crm(crm_document)

        with transaction.atomic():
            if UserService.cpf_existe(cpf):
                raise ValidationError('Já existe um usuário com este CPF.')
            if UserService.email_existe(email):
                raise ValidationError('Já existe um usuário com este e-mail.')
            if ProfessionalProfile.objects.filter(crm_number=crm_number, crm_uf=crm_uf).exists():
                raise ValidationError('Já existe um médico cadastrado com este CRM/UF.')

            senha_inicial = AutenticacaoService._gerar_senha_temporaria()
            usuario = UserService.criar_usuario_profissional(
                cpf=cpf,
                email=email,
                full_name=full_name,
                password=senha_inicial,
                is_active=False,
                must_change_password=True,
            )
            perfil = ProfessionalProfile.objects.create(
                user=usuario,
                birth_date=birth_date,
                phone=phone,
                crm_number=crm_number,
                crm_uf=crm_uf,
                crm_document=crm_document,
                homologation_status=ProfessionalProfile.HomologationStatus.PENDING,
            )
            AuditService.registrar_acao_administrativa(
                actor_id,
                usuario.pk,
                AdministrativeAction.Action.PROFESSIONAL_CREATED,
                ip_address,
            )
            return perfil

    @classmethod
    def homologar_profissional(
        cls,
        actor_id: int,
        professional_id: int,
        *,
        crm_regular: bool,
        icp_brasil_active: bool,
        ip_address: str | None = None,
    ) -> tuple[ProfessionalProfile, bool]:
        cls._exigir_admin(actor_id)
        if not crm_regular:
            raise ValidationError('CRM irregular impede a homologação do médico.')

        with transaction.atomic():
            perfil = (
                ProfessionalProfile.objects.select_for_update()
                .select_related('user')
                .filter(pk=professional_id)
                .first()
            )
            if perfil is None:
                raise ProfissionalNaoEncontrado
            if not perfil.crm_document:
                raise ValidationError('Comprovante de CRM obrigatório antes da homologação.')

            UserService.ativar_usuario(perfil.user_id)
            perfil.crm_regular = True
            perfil.icp_brasil_active = icp_brasil_active
            perfil.homologation_status = ProfessionalProfile.HomologationStatus.APPROVED
            perfil.approved_by_id = actor_id
            perfil.approved_at = timezone.now()
            perfil.suspended_at = None
            perfil.save(
                update_fields=(
                    'crm_regular',
                    'icp_brasil_active',
                    'homologation_status',
                    'approved_by',
                    'approved_at',
                    'suspended_at',
                    'updated_at',
                ),
            )
            AuditService.registrar_acao_administrativa(
                actor_id,
                perfil.user_id,
                AdministrativeAction.Action.PROFESSIONAL_APPROVED,
                ip_address,
            )

        enviada = AutenticacaoService.emitir_senha_provisoria_medico(
            actor_id,
            perfil.user_id,
            ip_address,
        )
        perfil.refresh_from_db()
        return perfil, enviada

    @classmethod
    def suspender_profissional(
        cls,
        actor_id: int,
        professional_id: int,
        ip_address: str | None = None,
    ) -> ProfessionalProfile:
        cls._exigir_admin(actor_id)
        with transaction.atomic():
            perfil = (
                ProfessionalProfile.objects.select_for_update()
                .select_related('user')
                .filter(pk=professional_id)
                .first()
            )
            if perfil is None:
                raise ProfissionalNaoEncontrado

            AuditService.registrar_acao_administrativa(
                actor_id,
                perfil.user_id,
                AdministrativeAction.Action.PROFESSIONAL_SUSPENDED,
                ip_address,
            )
            perfil.homologation_status = ProfessionalProfile.HomologationStatus.SUSPENDED
            perfil.availability = ProfessionalProfile.Availability.OFFLINE
            perfil.suspended_at = timezone.now()
            perfil.save(
                update_fields=(
                    'homologation_status',
                    'availability',
                    'suspended_at',
                    'updated_at',
                ),
            )
            if perfil.user.is_active:
                UserService.inativar_usuario(perfil.user_id, actor_id, ip_address)
            ShiftHistory.objects.create(
                professional=perfil,
                status=ProfessionalProfile.Availability.OFFLINE,
            )
            return perfil

    @classmethod
    def alterar_disponibilidade(
        cls,
        user_id: int,
        novo_status: str,
        *,
        operational_phone: str | None = None,
    ) -> ProfessionalProfile:
        if novo_status not in ProfessionalProfile.Availability.values:
            raise ValidationError('Status de disponibilidade inválido.')

        with transaction.atomic():
            perfil = (
                ProfessionalProfile.objects.select_for_update()
                .select_related('user')
                .filter(user_id=user_id, user__is_active=True)
                .first()
            )
            if perfil is None or perfil.homologation_status != ProfessionalProfile.HomologationStatus.APPROVED:
                raise PermissaoProfissionalNegada

            if novo_status == ProfessionalProfile.Availability.ONLINE:
                if not perfil.crm_regular or not perfil.icp_brasil_active:
                    raise ValidationError(
                        'Somente médico com CRM regular e certificado ICP-Brasil ativo pode ficar Online.',
                    )

            campos = ['availability', 'updated_at']
            perfil.availability = novo_status
            if operational_phone is not None and operational_phone.strip():
                perfil.operational_phone = normalizar_celular(operational_phone)
                campos.append('operational_phone')
            perfil.save(update_fields=tuple(campos))

            ShiftHistory.objects.create(professional=perfil, status=novo_status)
            return perfil

    @staticmethod
    def obter_por_usuario(user_id: int) -> ProfessionalProfile | None:
        return (
            ProfessionalProfile.objects.select_related('user')
            .filter(user_id=user_id, user__is_active=True)
            .first()
        )
