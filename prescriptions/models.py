import uuid

from django.db import models
from django.db.models import Q


class PrescriptionReview(models.Model):
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Aprovada integralmente'
        APPROVED_WITH_CHANGES = 'approved_with_changes', 'Aprovada com alterações'
        REJECTED_TO_CHAT = 'rejected_to_chat', 'Rejeitada / Encaminhada ao chat'
        RECLASSIFIED_TO_RED = 'reclassified_to_red', 'Reclassificada para Vermelho (Emergência)'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    triage_session = models.ForeignKey(
        'triage.TriageSession',
        on_delete=models.PROTECT,
        related_name='prescription_reviews',
        verbose_name='triagem',
    )
    queue_item = models.ForeignKey(
        'care.ClinicalQueueItem',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='prescription_reviews',
        verbose_name='chamado da fila',
    )
    professional = models.ForeignKey(
        'professionals.ProfessionalProfile',
        on_delete=models.PROTECT,
        related_name='prescription_reviews',
        verbose_name='médico revisor',
    )
    decision = models.CharField(
        'decisão clínica',
        max_length=24,
        choices=Decision.choices,
    )
    clinical_opinion = models.TextField('parecer clínico')
    allergy_conflict_detected = models.BooleanField('conflito com alergia detectado', default=False)
    allergy_conflict_details = models.CharField('detalhes do conflito', max_length=300, blank=True)
    prescribed_medication = models.CharField('fármaco prescrito', max_length=200, blank=True)
    dosage_and_route = models.CharField('posologia e via', max_length=300, blank=True)
    instructions = models.TextField('orientações ao paciente', blank=True)
    created_at = models.DateTimeField('registrado em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'revisão de prescrição'
        verbose_name_plural = 'revisões de prescrição'
        ordering = ('-created_at',)

    def __str__(self) -> str:
        return f'Revisão {self.pk} — {self.get_decision_display()}'


class DigitalPrescription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Ativa / Válida'
        DISPENSED = 'dispensed', 'Utilizada / Dispensada'
        EXPIRED = 'expired', 'Expirada'
        REVOKED = 'revoked', 'Revogada'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.OneToOneField(
        PrescriptionReview,
        on_delete=models.PROTECT,
        related_name='digital_prescription',
        verbose_name='revisão clínica',
    )
    triage_session = models.ForeignKey(
        'triage.TriageSession',
        on_delete=models.PROTECT,
        related_name='digital_prescriptions',
        verbose_name='triagem',
    )
    patient = models.ForeignKey(
        'patients.PatientProfile',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='digital_prescriptions',
        verbose_name='paciente titular',
    )
    dependent = models.ForeignKey(
        'patients.Dependent',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name='digital_prescriptions',
        verbose_name='dependente',
    )
    prescriber = models.ForeignKey(
        'professionals.ProfessionalProfile',
        on_delete=models.PROTECT,
        related_name='digital_prescriptions',
        verbose_name='médico prescritor',
    )
    medication_name = models.CharField('medicamento', max_length=200)
    dosage_and_route = models.CharField('posologia e via', max_length=300)
    instructions = models.TextField('orientações', blank=True)
    icp_signature_hash = models.CharField('hash criptográfico ICP-Brasil', max_length=64)
    icp_signature_valid = models.BooleanField('assinatura ICP-Brasil válida', default=True)
    verification_token = models.CharField('token de verificação', max_length=64, unique=True)
    status = models.CharField(
        'status',
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
    )
    issued_at = models.DateTimeField('emitida em', auto_now_add=True, db_index=True)
    valid_until = models.DateTimeField('válida até')
    revoked_at = models.DateTimeField('revogada em', blank=True, null=True)
    revocation_reason = models.CharField('motivo da revogação', max_length=300, blank=True)

    class Meta:
        verbose_name = 'receita digital'
        verbose_name_plural = 'receitas digitais'
        ordering = ('-issued_at',)
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(patient__isnull=False) & Q(dependent__isnull=True))
                    | (Q(patient__isnull=True) & Q(dependent__isnull=False))
                ),
                name='prescription_exactly_one_subject',
            ),
        ]

    def __str__(self) -> str:
        return f'Receita {self.pk} — {self.medication_name} ({self.get_status_display()})'


class PrescriptionDispensation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.OneToOneField(
        DigitalPrescription,
        on_delete=models.PROTECT,
        related_name='dispensation',
        verbose_name='receita digital',
    )
    pharmacist_name = models.CharField('nome do farmacêutico', max_length=120)
    crf_number = models.CharField('CRF', max_length=20)
    crf_uf = models.CharField('UF do CRF', max_length=2)
    pharmacy_cnpj = models.CharField('CNPJ da farmácia', max_length=14)
    dispensed_at = models.DateTimeField('dispensada em', auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = 'dispensação de receita'
        verbose_name_plural = 'dispensações de receita'
        ordering = ('-dispensed_at',)

    def __str__(self) -> str:
        return f'Dispensação {self.prescription_id} — CRF {self.crf_number}/{self.crf_uf}'
