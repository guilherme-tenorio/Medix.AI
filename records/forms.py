from django import forms

from triage.models import TriageSession

from .models import MedicalRecordAmendment


class MedicalRecordFilterForm(forms.Form):
    start_date = forms.DateField(
        label='Data inicial',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    end_date = forms.DateField(
        label='Data final',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    event_type = forms.ChoiceField(
        label='Tipo de evento',
        required=False,
        choices=[('', 'Todos'), *MedicalRecordAmendment.EventType.choices],
    )
    risk_color = forms.ChoiceField(
        label='Classificação de risco',
        required=False,
        choices=[('', 'Todas'), *TriageSession.RiskColor.choices],
    )
    keyword = forms.CharField(
        label='Palavra-chave',
        required=False,
        max_length=100,
    )
