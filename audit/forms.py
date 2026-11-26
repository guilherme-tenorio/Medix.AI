from django import forms

from .models import LoginAttempt


class AuditSearchForm(forms.Form):
    periodo_inicial = forms.DateTimeField(
        label='De',
        required=False,
        input_formats=('%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S'),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    periodo_final = forms.DateTimeField(
        label='Até',
        required=False,
        input_formats=('%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S'),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
    )
    identificador = forms.CharField(
        label='CPF ou e-mail',
        required=False,
        max_length=254,
        widget=forms.TextInput(attrs={'autocomplete': 'off'}),
    )
    perfil = forms.ChoiceField(
        label='Perfil',
        required=False,
        choices=(('', 'Todos'), *LoginAttempt.Role.choices),
    )
    resultado = forms.ChoiceField(
        label='Resultado',
        required=False,
        choices=(('', 'Todos'), *LoginAttempt.Result.choices),
    )

    def clean(self):
        dados = super().clean()
        inicio = dados.get('periodo_inicial')
        fim = dados.get('periodo_final')
        if inicio and fim and inicio > fim:
            self.add_error('periodo_final', 'A data final deve ser igual ou posterior à data inicial.')
        return dados


class AdminAccountCreateForm(forms.Form):
    full_name = forms.CharField(label='Nome completo', min_length=3, max_length=120)
    cpf = forms.CharField(label='CPF', max_length=14)
    email = forms.EmailField(label='E-mail corporativo', max_length=254)
    birth_date = forms.DateField(
        label='Data de nascimento',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
