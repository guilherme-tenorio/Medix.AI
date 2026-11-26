from django import forms

from .models import ProfessionalProfile
from .services import UFS_BRASIL


class ProfessionalCreateForm(forms.Form):
    cpf = forms.CharField(label='CPF', max_length=14)
    full_name = forms.CharField(label='Nome completo', min_length=3, max_length=120)
    birth_date = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    phone = forms.CharField(label='Celular com DDD', max_length=16)
    email = forms.EmailField(label='E-mail corporativo', max_length=254)
    crm_number = forms.CharField(label='CRM', max_length=20)
    crm_uf = forms.ChoiceField(
        label='UF do CRM',
        choices=[(uf, uf) for uf in sorted(UFS_BRASIL)],
    )
    crm_document = forms.FileField(label='Comprovante de CRM (PDF, PNG ou JPEG)')


class ProfessionalHomologateForm(forms.Form):
    crm_regular = forms.BooleanField(label='CRM regular confirmado junto ao conselho', required=True)
    icp_brasil_active = forms.BooleanField(label='Certificado ICP-Brasil válido e ativo', required=False)


class ProfessionalAvailabilityForm(forms.Form):
    availability = forms.ChoiceField(
        label='Disponibilidade',
        choices=ProfessionalProfile.Availability.choices,
    )
    operational_phone = forms.CharField(
        label='Telefone operacional',
        max_length=16,
        required=False,
    )
