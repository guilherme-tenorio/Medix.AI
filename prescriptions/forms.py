from django import forms

from .models import PrescriptionReview


class PrescriptionReviewForm(forms.Form):
    decision = forms.ChoiceField(
        label='Decisão clínica',
        choices=PrescriptionReview.Decision.choices,
    )
    clinical_opinion = forms.CharField(
        label='Parecer / justificativa clínica',
        widget=forms.Textarea(attrs={'rows': 4}),
    )
    prescribed_medication = forms.CharField(
        label='Fármaco prescrito (obrigatório para aprovação)',
        required=False,
        max_length=200,
    )
    dosage_and_route = forms.CharField(
        label='Posologia e via de administração',
        required=False,
        max_length=300,
    )
    instructions = forms.CharField(
        label='Orientações ao paciente',
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
    )


class PrescriptionRevokeForm(forms.Form):
    reason = forms.CharField(
        label='Justificativa da revogação',
        max_length=300,
        widget=forms.Textarea(attrs={'rows': 2}),
    )


class PrescriptionDispensationForm(forms.Form):
    pharmacist_name = forms.CharField(label='Nome do farmacêutico', max_length=120)
    crf_number = forms.CharField(label='Número do CRF', max_length=20)
    crf_uf = forms.CharField(label='UF do CRF', max_length=2)
    pharmacy_cnpj = forms.CharField(label='CNPJ da farmácia', max_length=18)
