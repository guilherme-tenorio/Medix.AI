from django.contrib.auth.forms import AuthenticationForm
from django import forms


class PortalLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='CPF ou e-mail',
        max_length=254,
        widget=forms.TextInput(
            attrs={
                'autocomplete': 'username',
                'autofocus': True,
                'placeholder': 'Digite seu CPF ou e-mail',
            }
        ),
    )
    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'autocomplete': 'current-password',
                'placeholder': 'Digite sua senha',
            }
        ),
    )

    error_messages = {
        'invalid_login': 'Não foi possível entrar com esses dados.',
        'inactive': 'Não foi possível entrar com esses dados.',
    }

    def clean(self):
        dados = super().clean()
        if not dados.get('username') or not dados.get('password'):
            raise forms.ValidationError(
                self.error_messages['invalid_login'],
                code='invalid_login',
            )
        return dados

    def marcar_erros_acessiveis(self) -> None:
        for nome, campo in self.fields.items():
            if self[nome].errors:
                campo.widget.attrs['aria-invalid'] = 'true'
                campo.widget.attrs['aria-describedby'] = f'id_{nome}_errors'


class TrocarSenhaForm(forms.Form):
    senha_atual = forms.CharField(
        label='Senha atual',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}),
    )
    nova_senha = forms.CharField(
        label='Nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    confirmar_senha = forms.CharField(
        label='Confirme a nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def clean(self):
        dados = super().clean()
        nova_senha = dados.get('nova_senha')
        confirmar_senha = dados.get('confirmar_senha')
        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            self.add_error('confirmar_senha', 'As senhas informadas não coincidem.')
        return dados




class SolicitarRedefinicaoSenhaForm(forms.Form):
    email = forms.EmailField(
        label='E-mail cadastrado',
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'}),
    )


class RedefinirSenhaForm(forms.Form):
    nova_senha = forms.CharField(
        label='Nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )
    confirmar_senha = forms.CharField(
        label='Confirme a nova senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def clean(self):
        dados = super().clean()
        nova_senha = dados.get('nova_senha')
        confirmar_senha = dados.get('confirmar_senha')
        if nova_senha and confirmar_senha and nova_senha != confirmar_senha:
            self.add_error('confirmar_senha', 'As senhas informadas não coincidem.')
        return dados


class SolicitarRedefinicaoAdministradorForm(forms.Form):
    administrador_id = forms.ChoiceField(
        label='Administrador',
        choices=(),
        widget=forms.Select(),
    )

    def __init__(self, *args, choices: list[tuple[str, str]], **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['administrador_id'].choices = choices


class EmitirSenhaProvisoriaForm(forms.Form):
    profissional_id = forms.ChoiceField(
        label='Médico',
        choices=(),
        widget=forms.Select(),
    )

    def __init__(self, *args, choices: list[tuple[str, str]], **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profissional_id'].choices = choices
