from django import forms

from .models import ClinicalOutcome


class ChatMessageForm(forms.Form):
    content = forms.CharField(
        label='Mensagem',
        required=False,
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                'rows': 2,
                'placeholder': 'Digite sua mensagem (até 1000 caracteres)...',
                'data-voice-target': 'true',
            }
        ),
    )
    attachment = forms.FileField(
        label='Anexo opcional (PDF, PNG ou JPEG até 10 MB)',
        required=False,
    )


class ClinicalOutcomeForm(forms.Form):
    outcome_type = forms.ChoiceField(
        label='Tipo de desfecho',
        choices=ClinicalOutcome.OutcomeType.choices,
    )
    summary_and_conduct = forms.CharField(
        label='Resumo e conduta clínica',
        max_length=1000,
        widget=forms.Textarea(attrs={'rows': 4}),
    )
    warning_signs = forms.CharField(
        label='Sinais de alerta para retorno',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2}),
    )
    reclassified_to_red = forms.BooleanField(
        label='Reclassificar para Vermelho (dispara encaminhamento de emergência imediato)',
        required=False,
    )
