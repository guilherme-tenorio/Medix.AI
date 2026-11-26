from django.conf import settings
from django.db import models
from django.db.models import Q


class Gender(models.TextChoices):
    FEMALE = 'female', 'Feminino'
    MALE = 'male', 'Masculino'
    OTHER = 'other', 'Outro'
    PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefiro não informar'


class BloodType(models.TextChoices):
    A_POS = 'A+', 'A+'
    A_NEG = 'A-', 'A-'
    B_POS = 'B+', 'B+'
    B_NEG = 'B-', 'B-'
    AB_POS = 'AB+', 'AB+'
    AB_NEG = 'AB-', 'AB-'
    O_POS = 'O+', 'O+'
    O_NEG = 'O-', 'O-'
    UNKNOWN = 'unknown', 'Não sei informar'


class PatientProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='patient_profile',
        verbose_name='usuário',
    )
    birth_date = models.DateField('data de nascimento')
    gender = models.CharField('gênero', max_length=24, choices=Gender.choices)
    phone = models.CharField('celular', max_length=11)
    phone_verified_at = models.DateTimeField('celular verificado em', blank=True, null=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'paciente titular'
        verbose_name_plural = 'pacientes titulares'

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.email


class ConsentRecord(models.Model):
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.PROTECT,
        related_name='consents',
        verbose_name='paciente',
    )
    term_version = models.CharField('versão do termo', max_length=32)
    accepted = models.BooleanField('aceito')
    ip_address = models.GenericIPAddressField('endereço IP', blank=True, null=True)
    accepted_at = models.DateTimeField('aceito em', auto_now_add=True)

    class Meta:
        verbose_name = 'registro de consentimento'
        verbose_name_plural = 'registros de consentimento'
        ordering = ('-accepted_at',)

    def __str__(self) -> str:
        return f'{self.patient} — {self.term_version}'


class Dependent(models.Model):
    class LegalRelationship(models.TextChoices):
        CHILD = 'child', 'Filho(a)'
        WARD = 'ward', 'Tutelado/Curatelado'
        OTHER = 'other', 'Outro Dependente Legal'

    guardian = models.ForeignKey(
        PatientProfile,
        on_delete=models.PROTECT,
        related_name='dependents',
        verbose_name='responsável',
    )
    legal_relationship = models.CharField(
        'vínculo legal',
        max_length=24,
        choices=LegalRelationship.choices,
    )
    cpf = models.CharField('CPF', max_length=11, unique=True)
    full_name = models.CharField('nome completo', max_length=120)
    birth_date = models.DateField('data de nascimento')
    gender = models.CharField('gênero', max_length=24, choices=Gender.choices)
    is_active = models.BooleanField('ativo', default=True)
    deactivated_at = models.DateTimeField('desativado em', blank=True, null=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'dependente'
        verbose_name_plural = 'dependentes'
        ordering = ('full_name',)
        indexes = [
            models.Index(fields=('guardian', 'is_active'), name='patient_dep_guardian_act_idx'),
        ]

    def __str__(self) -> str:
        return self.full_name


class ClinicalProfile(models.Model):
    patient = models.OneToOneField(
        PatientProfile,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='clinical_profile',
        verbose_name='paciente titular',
    )
    dependent = models.OneToOneField(
        Dependent,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='clinical_profile',
        verbose_name='dependente',
    )
    has_disability = models.BooleanField('possui deficiência', default=False)
    disability_description = models.CharField('descrição da deficiência', max_length=120, blank=True)
    blood_type = models.CharField(
        'tipo sanguíneo',
        max_length=16,
        choices=BloodType.choices,
        default=BloodType.UNKNOWN,
    )
    has_allergy = models.BooleanField('possui alergia', default=False)
    allergy_description = models.CharField('descrição da alergia', max_length=200, blank=True)
    continuous_medications = models.CharField('medicamentos contínuos', max_length=300, blank=True)
    height_cm = models.PositiveSmallIntegerField('altura (cm)')
    weight_kg = models.DecimalField('peso (kg)', max_digits=4, decimal_places=1)
    has_hypertension = models.BooleanField('pressão alta', default=False)
    has_diabetes = models.BooleanField('diabetes', default=False)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'perfil clínico'
        verbose_name_plural = 'perfis clínicos'
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(patient__isnull=False) & Q(dependent__isnull=True))
                    | (Q(patient__isnull=True) & Q(dependent__isnull=False))
                ),
                name='clinical_profile_exactly_one_owner',
            ),
        ]

    def __str__(self) -> str:
        alvo = self.patient or self.dependent
        return f'Perfil clínico de {alvo}'


class ClinicalProfileHistory(models.Model):
    clinical_profile = models.ForeignKey(
        ClinicalProfile,
        on_delete=models.PROTECT,
        related_name='history',
        verbose_name='perfil clínico',
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='clinical_profile_changes',
        verbose_name='alterado por',
    )
    snapshot = models.JSONField('retrato clínico')
    change_reason = models.CharField('motivo da alteração', max_length=120, blank=True)
    changed_at = models.DateTimeField('alterado em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'histórico clínico'
        verbose_name_plural = 'históricos clínicos'
        ordering = ('-changed_at',)

    def __str__(self) -> str:
        return f'Histórico #{self.pk} — {self.changed_at:%Y-%m-%d %H:%M}'


class SmsVerificationChallenge(models.Model):
    phone = models.CharField('celular', max_length=11, db_index=True)
    code_hash = models.CharField('hash do código', max_length=128)
    attempts = models.PositiveSmallIntegerField('tentativas', default=0)
    expires_at = models.DateTimeField('expira em')
    verified_at = models.DateTimeField('verificado em', blank=True, null=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'desafio de verificação SMS'
        verbose_name_plural = 'desafios de verificação SMS'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'SMS ****{self.phone[-4:]}'
