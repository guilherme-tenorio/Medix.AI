from __future__ import annotations

import secrets
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from core.integrations.sms import SmsIntegrationDisabled, get_sms_adapter
from users.identifiers import normalizar_celular, validar_cpf
from users.services import UserService

from .models import (
    BloodType,
    ClinicalProfile,
    ClinicalProfileHistory,
    ConsentRecord,
    Dependent,
    Gender,
    PatientProfile,
    SmsVerificationChallenge,
)

CONSENT_TERM_VERSION = 'MVP-1.0'
MIN_HEIGHT_CM = 40
MAX_HEIGHT_CM = 250
MIN_WEIGHT_KG = Decimal('1.0')
MAX_WEIGHT_KG = Decimal('400.0')
SMS_CODE_TTL_MINUTES = 10
SMS_MAX_ATTEMPTS = 5


class PermissaoPacienteNegada(Exception):
    pass


class DependenteNaoEncontrado(Exception):
    pass


def _calcular_idade(birth_date: date, referencia: date) -> int:
    anos = referencia.year - birth_date.year
    if (referencia.month, referencia.day) < (birth_date.month, birth_date.day):
        anos -= 1
    return anos


def _validar_nome(nome: str) -> str:
    limpo = (nome or '').strip()
    if len(limpo) < 3 or len(limpo) > 120:
        raise ValidationError('O nome completo deve ter entre 3 e 120 caracteres.')
    return limpo


def _validar_nascimento(birth_date: date, *, exigir_maioridade: bool) -> date:
    hoje = timezone.localdate()
    if birth_date > hoje:
        raise ValidationError('A data de nascimento não pode ser futura.')
    if exigir_maioridade and _calcular_idade(birth_date, hoje) < 18:
        raise ValidationError('O titular ou responsável deve ter pelo menos 18 anos.')
    return birth_date


def _validar_dados_clinicos(dados: dict) -> dict:
    has_disability = bool(dados.get('has_disability'))
    disability_description = (dados.get('disability_description') or '').strip()
    if has_disability and not disability_description:
        raise ValidationError('Descreva a deficiência informada.')
    if len(disability_description) > 120:
        raise ValidationError('A descrição da deficiência deve ter no máximo 120 caracteres.')
    if not has_disability:
        disability_description = ''

    has_allergy = bool(dados.get('has_allergy'))
    allergy_description = (dados.get('allergy_description') or '').strip()
    if has_allergy and not allergy_description:
        raise ValidationError('Descreva a alergia informada.')
    if len(allergy_description) > 200:
        raise ValidationError('A descrição da alergia deve ter no máximo 200 caracteres.')
    if not has_allergy:
        allergy_description = ''

    continuous_medications = (dados.get('continuous_medications') or '').strip()
    if len(continuous_medications) > 300:
        raise ValidationError('Medicamentos contínuos deve ter no máximo 300 caracteres.')

    blood_type = dados.get('blood_type') or BloodType.UNKNOWN
    if blood_type not in BloodType.values:
        raise ValidationError('Tipo sanguíneo inválido.')

    height_cm = dados.get('height_cm')
    if height_cm is None or height_cm < MIN_HEIGHT_CM or height_cm > MAX_HEIGHT_CM:
        raise ValidationError(
            f'A altura deve estar entre {MIN_HEIGHT_CM} cm e {MAX_HEIGHT_CM} cm.',
        )

    weight_kg = dados.get('weight_kg')
    if weight_kg is None or weight_kg < MIN_WEIGHT_KG or weight_kg > MAX_WEIGHT_KG:
        raise ValidationError(
            f'O peso deve estar entre {MIN_WEIGHT_KG} kg e {MAX_WEIGHT_KG} kg.',
        )

    return {
        'has_disability': has_disability,
        'disability_description': disability_description,
        'blood_type': blood_type,
        'has_allergy': has_allergy,
        'allergy_description': allergy_description,
        'continuous_medications': continuous_medications,
        'height_cm': int(height_cm),
        'weight_kg': Decimal(weight_kg).quantize(Decimal('0.1')),
        'has_hypertension': bool(dados.get('has_hypertension')),
        'has_diabetes': bool(dados.get('has_diabetes')),
    }


def _gerar_snapshot_clinico(perfil: ClinicalProfile) -> dict:
    return {
        'has_disability': perfil.has_disability,
        'disability_description': perfil.disability_description,
        'blood_type': perfil.blood_type,
        'has_allergy': perfil.has_allergy,
        'allergy_description': perfil.allergy_description,
        'continuous_medications': perfil.continuous_medications,
        'height_cm': perfil.height_cm,
        'weight_kg': str(perfil.weight_kg),
        'has_hypertension': perfil.has_hypertension,
        'has_diabetes': perfil.has_diabetes,
    }


class SmsVerificationService:
    @staticmethod
    def enviar_codigo(phone: str) -> SmsVerificationChallenge:
        celular = normalizar_celular(phone)
        codigo = f'{secrets.randbelow(1_000_000):06d}'
        desafio = SmsVerificationChallenge.objects.create(
            phone=celular,
            code_hash=make_password(codigo),
            expires_at=timezone.now() + timedelta(minutes=SMS_CODE_TTL_MINUTES),
        )
        try:
            enviado = get_sms_adapter().send_verification_code(celular, codigo)
        except SmsIntegrationDisabled as erro:
            raise ValidationError(
                'Serviço de verificação por SMS indisponível no momento.',
            ) from erro
        if not enviado:
            raise ValidationError('Não foi possível enviar o código SMS. Tente novamente.')
        return desafio

    @staticmethod
    def confirmar_codigo(phone: str, code: str) -> SmsVerificationChallenge:
        celular = normalizar_celular(phone)
        codigo_limpo = (code or '').strip()
        if not codigo_limpo:
            raise ValidationError('Informe o código de verificação recebido por SMS.')

        with transaction.atomic():
            desafio = (
                SmsVerificationChallenge.objects.select_for_update()
                .filter(phone=celular, verified_at__isnull=True)
                .order_by('-created_at')
                .first()
            )
            agora = timezone.now()
            if desafio is None or desafio.expires_at < agora:
                raise ValidationError('Código SMS inválido ou expirado. Solicite um novo código.')
            if desafio.attempts >= SMS_MAX_ATTEMPTS:
                raise ValidationError('Limite de tentativas do código SMS atingido. Solicite um novo código.')

            if not check_password(codigo_limpo, desafio.code_hash):
                desafio.attempts += 1
                desafio.save(update_fields=('attempts',))
                raise ValidationError('Código SMS inválido.')

            desafio.verified_at = agora
            desafio.save(update_fields=('verified_at',))
            return desafio


class PatientService:
    @staticmethod
    def cpf_disponivel(cpf: str) -> bool:
        return not UserService.cpf_existe(cpf) and not Dependent.objects.filter(cpf=cpf).exists()

    @staticmethod
    def obter_perfil_por_usuario(user_id: int) -> PatientProfile | None:
        return (
            PatientProfile.objects.select_related('user', 'clinical_profile')
            .filter(user_id=user_id, user__is_active=True)
            .first()
        )

    @classmethod
    def cadastrar_titular(
        cls,
        dados: dict,
        *,
        ip_address: str | None = None,
    ) -> PatientProfile:
        cpf = validar_cpf(dados.get('cpf', ''))
        full_name = _validar_nome(dados.get('full_name', ''))
        birth_date = _validar_nascimento(dados['birth_date'], exigir_maioridade=True)
        gender = dados.get('gender')
        if gender not in Gender.values:
            raise ValidationError('Selecione uma opção de gênero válida.')

        phone = normalizar_celular(dados.get('phone', ''))
        email = (dados.get('email') or '').strip().casefold()
        if not email:
            raise ValidationError('Informe um e-mail válido.')

        if not dados.get('consent_accepted'):
            raise ValidationError('O consentimento explícito para tratamento de dados é obrigatório.')

        dados_clinicos = _validar_dados_clinicos(dados)

        with transaction.atomic():
            if not cls.cpf_disponivel(cpf):
                raise ValidationError('Já existe um cadastro com este CPF.')
            if UserService.email_existe(email):
                raise ValidationError('Já existe uma conta com este e-mail.')

            SmsVerificationService.confirmar_codigo(phone, dados.get('sms_code', ''))

            usuario = UserService.criar_usuario_paciente(
                cpf=cpf,
                email=email,
                full_name=full_name,
                password=dados['password'],
            )
            paciente = PatientProfile.objects.create(
                user=usuario,
                birth_date=birth_date,
                gender=gender,
                phone=phone,
                phone_verified_at=timezone.now(),
            )
            ConsentRecord.objects.create(
                patient=paciente,
                term_version=CONSENT_TERM_VERSION,
                accepted=True,
                ip_address=ip_address,
            )
            perfil_clinico = ClinicalProfile.objects.create(
                patient=paciente,
                **dados_clinicos,
            )
            ClinicalProfileHistory.objects.create(
                clinical_profile=perfil_clinico,
                changed_by=usuario,
                snapshot=_gerar_snapshot_clinico(perfil_clinico),
                change_reason='Cadastro inicial do titular',
            )
            return paciente

    @classmethod
    def atualizar_titular_e_perfil(cls, user_id: int, dados: dict) -> PatientProfile:
        with transaction.atomic():
            paciente = (
                PatientProfile.objects.select_for_update(of=('self',))
                .select_related('user', 'clinical_profile')
                .filter(user_id=user_id, user__is_active=True)
                .first()
            )
            if paciente is None:
                raise PermissaoPacienteNegada

            full_name = _validar_nome(dados.get('full_name', ''))
            birth_date = _validar_nascimento(dados['birth_date'], exigir_maioridade=True)
            gender = dados.get('gender')
            if gender not in Gender.values:
                raise ValidationError('Selecione uma opção de gênero válida.')
            phone = normalizar_celular(dados.get('phone', ''))
            dados_clinicos = _validar_dados_clinicos(dados)

            partes = full_name.split(None, 1)
            paciente.user.first_name = partes[0]
            paciente.user.last_name = partes[1] if len(partes) > 1 else ''
            paciente.user.save(update_fields=('first_name', 'last_name'))

            paciente.birth_date = birth_date
            paciente.gender = gender
            paciente.phone = phone
            paciente.save(update_fields=('birth_date', 'gender', 'phone', 'updated_at'))

            perfil_clinico = paciente.clinical_profile
            for campo, valor in dados_clinicos.items():
                setattr(perfil_clinico, campo, valor)
            perfil_clinico.save()

            ClinicalProfileHistory.objects.create(
                clinical_profile=perfil_clinico,
                changed_by=paciente.user,
                snapshot=_gerar_snapshot_clinico(perfil_clinico),
                change_reason='Atualização cadastral e clínica do titular',
            )
            return paciente


class DependentService:
    @staticmethod
    def _obter_responsavel_autorizado(guardian_user_id: int) -> PatientProfile:
        responsavel = PatientService.obter_perfil_por_usuario(guardian_user_id)
        if responsavel is None:
            raise PermissaoPacienteNegada
        if _calcular_idade(responsavel.birth_date, timezone.localdate()) < 18:
            raise PermissaoPacienteNegada
        return responsavel

    @classmethod
    def listar_dependentes(cls, guardian_user_id: int) -> QuerySet[Dependent]:
        responsavel = cls._obter_responsavel_autorizado(guardian_user_id)
        return (
            Dependent.objects.select_related('clinical_profile')
            .filter(guardian=responsavel, is_active=True)
            .order_by('full_name')
        )

    @classmethod
    def obter_dependente(cls, guardian_user_id: int, dependent_id: int) -> Dependent:
        responsavel = cls._obter_responsavel_autorizado(guardian_user_id)
        dependente = (
            Dependent.objects.select_related('clinical_profile', 'guardian__user')
            .filter(pk=dependent_id, guardian=responsavel, is_active=True)
            .first()
        )
        if dependente is None:
            raise DependenteNaoEncontrado
        return dependente

    @classmethod
    def cadastrar_dependente(cls, guardian_user_id: int, dados: dict) -> Dependent:
        responsavel = cls._obter_responsavel_autorizado(guardian_user_id)
        cpf = validar_cpf(dados.get('cpf', ''))
        full_name = _validar_nome(dados.get('full_name', ''))
        birth_date = _validar_nascimento(dados['birth_date'], exigir_maioridade=False)

        gender = dados.get('gender')
        if gender not in Gender.values:
            raise ValidationError('Selecione uma opção de gênero válida.')

        legal_relationship = dados.get('legal_relationship')
        if legal_relationship not in Dependent.LegalRelationship.values:
            raise ValidationError('Selecione um vínculo legal válido.')

        dados_clinicos = _validar_dados_clinicos(dados)

        with transaction.atomic():
            if not PatientService.cpf_disponivel(cpf):
                raise ValidationError('Já existe um cadastro com este CPF.')

            dependente = Dependent.objects.create(
                guardian=responsavel,
                legal_relationship=legal_relationship,
                cpf=cpf,
                full_name=full_name,
                birth_date=birth_date,
                gender=gender,
            )
            perfil_clinico = ClinicalProfile.objects.create(
                dependent=dependente,
                **dados_clinicos,
            )
            ClinicalProfileHistory.objects.create(
                clinical_profile=perfil_clinico,
                changed_by=responsavel.user,
                snapshot=_gerar_snapshot_clinico(perfil_clinico),
                change_reason='Cadastro inicial de dependente',
            )
            return dependente

    @classmethod
    def atualizar_dependente(
        cls,
        guardian_user_id: int,
        dependent_id: int,
        dados: dict,
    ) -> Dependent:
        responsavel = cls._obter_responsavel_autorizado(guardian_user_id)
        full_name = _validar_nome(dados.get('full_name', ''))
        birth_date = _validar_nascimento(dados['birth_date'], exigir_maioridade=False)

        gender = dados.get('gender')
        if gender not in Gender.values:
            raise ValidationError('Selecione uma opção de gênero válida.')

        legal_relationship = dados.get('legal_relationship')
        if legal_relationship not in Dependent.LegalRelationship.values:
            raise ValidationError('Selecione um vínculo legal válido.')

        dados_clinicos = _validar_dados_clinicos(dados)

        with transaction.atomic():
            dependente = (
                Dependent.objects.select_for_update(of=('self',))
                .select_related('clinical_profile')
                .filter(pk=dependent_id, guardian=responsavel, is_active=True)
                .first()
            )
            if dependente is None:
                raise DependenteNaoEncontrado

            # CPF do dependente é imutável após o cadastro.
            dependente.full_name = full_name
            dependente.birth_date = birth_date
            dependente.gender = gender
            dependente.legal_relationship = legal_relationship
            dependente.save(
                update_fields=(
                    'full_name',
                    'birth_date',
                    'gender',
                    'legal_relationship',
                    'updated_at',
                ),
            )

            perfil_clinico = dependente.clinical_profile
            for campo, valor in dados_clinicos.items():
                setattr(perfil_clinico, campo, valor)
            perfil_clinico.save()

            ClinicalProfileHistory.objects.create(
                clinical_profile=perfil_clinico,
                changed_by=responsavel.user,
                snapshot=_gerar_snapshot_clinico(perfil_clinico),
                change_reason='Atualização cadastral e clínica de dependente',
            )
            return dependente

    @classmethod
    def desativar_dependente(cls, guardian_user_id: int, dependent_id: int) -> Dependent:
        responsavel = cls._obter_responsavel_autorizado(guardian_user_id)
        with transaction.atomic():
            dependente = (
                Dependent.objects.select_for_update()
                .filter(pk=dependent_id, guardian=responsavel, is_active=True)
                .first()
            )
            if dependente is None:
                raise DependenteNaoEncontrado

            dependente.is_active = False
            dependente.deactivated_at = timezone.now()
            dependente.save(update_fields=('is_active', 'deactivated_at', 'updated_at'))
            return dependente
