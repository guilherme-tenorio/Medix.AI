from decimal import Decimal

from django import forms

from .models import BloodType, Dependent, Gender


class ClinicalFieldsMixin(forms.Form):
    has_disability = forms.BooleanField(label='Possui deficiência?', required=False)
    disability_description = forms.CharField(
        label='Descrição da deficiência',
        max_length=120,
        required=False,
    )
    blood_type = forms.ChoiceField(
        label='Tipo sanguíneo',
        choices=BloodType.choices,
        initial=BloodType.UNKNOWN,
    )
    has_allergy = forms.BooleanField(label='Possui alergia?', required=False)
    allergy_description = forms.CharField(
        label='Descrição da alergia',
        max_length=200,
        required=False,
    )
    continuous_medications = forms.CharField(
        label='Medicamentos de uso contínuo',
        max_length=300,
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
    height_cm = forms.IntegerField(label='Altura (cm)', min_value=40, max_value=250)
    weight_kg = forms.DecimalField(
        label='Peso (kg)',
        min_value=Decimal('1.0'),
        max_value=Decimal('400.0'),
        decimal_places=1,
        max_digits=4,
    )
    has_hypertension = forms.BooleanField(label='Pressão alta (hipertensão)', required=False)
    has_diabetes = forms.BooleanField(label='Diabetes', required=False)

    def clean(self):
        dados = super().clean()
        if dados.get('has_disability') and not (dados.get('disability_description') or '').strip():
            self.add_error('disability_description', 'Descreva a deficiência informada.')
        if dados.get('has_allergy') and not (dados.get('allergy_description') or '').strip():
            self.add_error('allergy_description', 'Descreva a alergia informada.')
        return dados


class SmsCodeRequestForm(forms.Form):
    phone = forms.CharField(label='Celular com DDD', max_length=16)


class PatientRegistrationForm(ClinicalFieldsMixin):
    cpf = forms.CharField(label='CPF', max_length=14)
    full_name = forms.CharField(label='Nome completo', min_length=3, max_length=120)
    birth_date = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    gender = forms.ChoiceField(label='Gênero', choices=Gender.choices)
    phone = forms.CharField(label='Celular com DDD', max_length=16)
    sms_code = forms.CharField(label='Código SMS', max_length=6)
    email = forms.EmailField(label='E-mail', max_length=254)
    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    password_confirm = forms.CharField(
        label='Confirmar senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    consent_accepted = forms.BooleanField(
        label='Li e aceito o termo de consentimento para tratamento de dados pessoais e de saúde (LGPD).',
        required=True,
    )

    def clean(self):
        dados = super().clean()
        senha = dados.get('password')
        confirmacao = dados.get('password_confirm')
        if senha and confirmacao and senha != confirmacao:
            self.add_error('password_confirm', 'As senhas informadas não coincidem.')
        return dados


class PatientUpdateForm(ClinicalFieldsMixin):
    full_name = forms.CharField(label='Nome completo', min_length=3, max_length=120)
    birth_date = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    gender = forms.ChoiceField(label='Gênero', choices=Gender.choices)
    phone = forms.CharField(label='Celular com DDD', max_length=16)


class DependentCreateForm(ClinicalFieldsMixin):
    legal_relationship = forms.ChoiceField(
        label='Vínculo legal',
        choices=Dependent.LegalRelationship.choices,
    )
    cpf = forms.CharField(label='CPF do dependente', max_length=14)
    full_name = forms.CharField(label='Nome completo', min_length=3, max_length=120)
    birth_date = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    gender = forms.ChoiceField(label='Gênero', choices=Gender.choices)


class DependentUpdateForm(ClinicalFieldsMixin):
    legal_relationship = forms.ChoiceField(
        label='Vínculo legal',
        choices=Dependent.LegalRelationship.choices,
    )
    full_name = forms.CharField(label='Nome completo', min_length=3, max_length=120)
    birth_date = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    gender = forms.ChoiceField(label='Gênero', choices=Gender.choices)
