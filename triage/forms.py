from django import forms


class TriageStartForm(forms.Form):
    dependent_id = forms.IntegerField(
        label='Dependente (opcional)',
        required=False,
        widget=forms.HiddenInput(),
    )
    identity_confirmed = forms.BooleanField(
        label='Confirmo que o nome, a idade e o vínculo exibidos correspondem ao paciente desta triagem',
        required=True,
    )
    symptoms_description = forms.CharField(
        label='Relato de sintomas',
        min_length=5,
        max_length=2000,
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'placeholder': 'Descreva o que está sentindo (você também pode usar o microfone).',
                'data-voice-target': 'true',
            }
        ),
    )
    symptom_onset = forms.CharField(
        label='Início e duração dos sintomas',
        max_length=120,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Ex.: Há 2 dias, começou pela manhã',
                'data-voice-target': 'true',
            }
        ),
    )
    pain_intensity = forms.IntegerField(
        label='Intensidade da dor ou desconforto (0 a 10)',
        min_value=0,
        max_value=10,
        initial=3,
        widget=forms.NumberInput(attrs={'min': 0, 'max': 10}),
    )


class TriageAnswersForm(forms.Form):
    answer_1 = forms.CharField(
        label='Resposta 1',
        required=True,
        max_length=500,
        widget=forms.TextInput(attrs={'data-voice-target': 'true'}),
    )
    answer_2 = forms.CharField(
        label='Resposta 2',
        required=False,
        max_length=500,
        widget=forms.TextInput(attrs={'data-voice-target': 'true'}),
    )


class EmergencyLocationForm(forms.Form):
    latitude = forms.DecimalField(
        label='Latitude',
        required=False,
        max_digits=9,
        decimal_places=6,
    )
    longitude = forms.DecimalField(
        label='Longitude',
        required=False,
        max_digits=9,
        decimal_places=6,
    )
    manual_location_query = forms.CharField(
        label='Buscar por bairro ou cidade',
        required=False,
        max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Ex.: Centro, Vila Mariana ou São Paulo'}),
    )
