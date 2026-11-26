from django.conf import settings
from django.db import models


class ProfessionalProfile(models.Model):
    class HomologationStatus(models.TextChoices):
        PENDING = 'pending', 'Pendente de homologação'
        APPROVED = 'approved', 'Ativo/Homologado'
        SUSPENDED = 'suspended', 'Inativo/Suspenso'

    class Availability(models.TextChoices):
        ONLINE = 'online', 'Online/Disponível'
        PAUSED = 'paused', 'Pausa'
        OFFLINE = 'offline', 'Offline'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='professional_profile',
        verbose_name='usuário',
    )
    birth_date = models.DateField('data de nascimento')
    phone = models.CharField('celular', max_length=11)
    operational_phone = models.CharField('telefone operacional', max_length=11, blank=True)
    crm_number = models.CharField('CRM', max_length=20)
    crm_uf = models.CharField('UF do CRM', max_length=2)
    crm_document = models.FileField(
        'comprovante CRM',
        upload_to='professionals/crm_documents/',
    )
    crm_regular = models.BooleanField('CRM regular', default=False)
    icp_brasil_active = models.BooleanField('certificado ICP-Brasil ativo', default=False)
    homologation_status = models.CharField(
        'status de homologação',
        max_length=16,
        choices=HomologationStatus.choices,
        default=HomologationStatus.PENDING,
    )
    availability = models.CharField(
        'disponibilidade',
        max_length=16,
        choices=Availability.choices,
        default=Availability.OFFLINE,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='approved_professionals',
        verbose_name='homologado por',
    )
    approved_at = models.DateTimeField('homologado em', blank=True, null=True)
    suspended_at = models.DateTimeField('suspenso em', blank=True, null=True)
    created_at = models.DateTimeField('criado em', auto_now_add=True)
    updated_at = models.DateTimeField('atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'médico'
        verbose_name_plural = 'médicos'
        constraints = [
            models.UniqueConstraint(
                fields=('crm_number', 'crm_uf'),
                name='unique_professional_crm_uf',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.user.get_full_name() or self.user.email} (CRM {self.crm_number}/{self.crm_uf})'


class ShiftHistory(models.Model):
    professional = models.ForeignKey(
        ProfessionalProfile,
        on_delete=models.PROTECT,
        related_name='shift_history',
        verbose_name='médico',
    )
    status = models.CharField(
        'status',
        max_length=16,
        choices=ProfessionalProfile.Availability.choices,
    )
    changed_at = models.DateTimeField('registrado em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'histórico de plantão'
        verbose_name_plural = 'históricos de plantão'
        ordering = ('-changed_at',)

    def __str__(self) -> str:
        return f'{self.professional} — {self.get_status_display()}'
