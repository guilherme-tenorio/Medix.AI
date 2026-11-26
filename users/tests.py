from django.core import mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import TestCase, override_settings
from django.utils.http import urlsafe_base64_encode

from audit.models import AdministrativeAction
from users.models import User
from users.services import PermissaoGestaoUsuariosNegada
from users.services.authentication_service import AutenticacaoService


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    MEDIX_PUBLIC_BASE_URL='https://medix.example',
)
class AdministrativeCredentialTests(TestCase):
    def criar_usuario(
        self,
        *,
        username: str,
        email: str,
        cpf: str,
        role: str,
        is_staff: bool = False,
    ) -> User:
        usuario = User(
            username=username,
            email=email,
            cpf=cpf,
            role=role,
            is_staff=is_staff,
        )
        usuario.set_password('SenhaAnterior9!')
        usuario.save()
        return usuario

    def test_admin_ativo_pode_solicitar_redefinicao_de_outro_admin(self) -> None:
        administrador = self.criar_usuario(
            username='admin-a',
            email='admin-a@example.test',
            cpf='11111111111',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
        )
        alvo = self.criar_usuario(
            username='admin-b',
            email='admin-b@example.test',
            cpf='22222222222',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
        )

        enviado = AutenticacaoService.solicitar_redefinicao_administrador(
            administrador.pk,
            alvo.pk,
            None,
        )

        self.assertTrue(enviado)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [alvo.email])
        self.assertIn('/senha/redefinir/', mail.outbox[0].body)
        acao = AdministrativeAction.objects.get(target=alvo)
        self.assertEqual(acao.actor, administrador)
        self.assertEqual(
            acao.action,
            AdministrativeAction.Action.ADMIN_PASSWORD_RESET_REQUESTED,
        )

    def test_admin_nao_pode_iniciar_a_propria_redefinicao(self) -> None:
        administrador = self.criar_usuario(
            username='admin-a',
            email='admin-a@example.test',
            cpf='11111111111',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
        )

        enviado = AutenticacaoService.solicitar_redefinicao_administrador(
            administrador.pk,
            administrador.pk,
            None,
        )

        self.assertFalse(enviado)
        self.assertEqual(mail.outbox, [])

    def test_usuario_que_nao_e_admin_nao_pode_solicitar_redefinicao_admin(self) -> None:
        paciente = self.criar_usuario(
            username='paciente',
            email='paciente@example.test',
            cpf='11111111111',
            role=User.Role.PATIENT,
        )

        with self.assertRaises(PermissaoGestaoUsuariosNegada):
            AutenticacaoService.listar_administradores_para_redefinicao(paciente.pk)

    def test_token_de_admin_redefine_senha_e_fica_invalido_apos_uso(self) -> None:
        administrador = self.criar_usuario(
            username='admin-b',
            email='admin-b@example.test',
            cpf='22222222222',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
        )
        uidb64 = urlsafe_base64_encode(str(administrador.pk).encode())
        token = PasswordResetTokenGenerator().make_token(administrador)

        AutenticacaoService.redefinir_senha(
            uidb64,
            token,
            'NovaSenhaSegura8!',
        )

        administrador.refresh_from_db()
        self.assertTrue(administrador.check_password('NovaSenhaSegura8!'))
        self.assertFalse(administrador.must_change_password)
        self.assertIsNone(AutenticacaoService.usuario_para_redefinicao(uidb64, token))

    def test_senha_provisoria_e_enviada_e_exige_troca(self) -> None:
        administrador = self.criar_usuario(
            username='admin-a',
            email='admin-a@example.test',
            cpf='11111111111',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
        )
        medico = self.criar_usuario(
            username='medico',
            email='medico@example.test',
            cpf='33333333333',
            role=User.Role.PROFESSIONAL,
        )

        enviada = AutenticacaoService.emitir_senha_provisoria_medico(
            administrador.pk,
            medico.pk,
            None,
        )

        medico.refresh_from_db()
        senha_temporaria = mail.outbox[0].body.split('Senha temporária: ', 1)[1].splitlines()[0]
        self.assertTrue(enviada)
        self.assertEqual(mail.outbox[0].to, [medico.email])
        self.assertTrue(medico.check_password(senha_temporaria))
        self.assertTrue(medico.must_change_password)
        self.assertTrue(any(caractere.isupper() for caractere in senha_temporaria))
        self.assertTrue(any(caractere.islower() for caractere in senha_temporaria))
        self.assertTrue(any(caractere.isdigit() for caractere in senha_temporaria))
        self.assertTrue(any(not caractere.isalnum() for caractere in senha_temporaria))
        acao = AdministrativeAction.objects.get(target=medico)
        self.assertEqual(acao.actor, administrador)
        self.assertEqual(
            acao.action,
            AdministrativeAction.Action.PROFESSIONAL_TEMP_PASSWORD_REQUESTED,
        )

    @override_settings(EMAIL_BACKEND='core.integrations.email.DisabledEmailBackend')
    def test_backend_desligado_nao_altera_a_senha_do_medico(self) -> None:
        administrador = self.criar_usuario(
            username='admin-a',
            email='admin-a@example.test',
            cpf='11111111111',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
        )
        medico = self.criar_usuario(
            username='medico',
            email='medico@example.test',
            cpf='33333333333',
            role=User.Role.PROFESSIONAL,
        )

        enviada = AutenticacaoService.emitir_senha_provisoria_medico(
            administrador.pk,
            medico.pk,
            None,
        )

        medico.refresh_from_db()
        self.assertFalse(enviada)
        self.assertTrue(medico.check_password('SenhaAnterior9!'))
        self.assertFalse(medico.must_change_password)
        self.assertEqual(mail.outbox, [])
        self.assertTrue(
            AdministrativeAction.objects.filter(
                actor=administrador,
                target=medico,
                action=AdministrativeAction.Action.PROFESSIONAL_TEMP_PASSWORD_REQUESTED,
            ).exists()
        )


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    MEDIX_PUBLIC_BASE_URL='https://medix.example',
)
class PortalAuthenticationAndSessionTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.paciente = User.objects.create_user(
            username='paciente1',
            email='paciente1@example.test',
            cpf='44444444444',
            role=User.Role.PATIENT,
            password='SenhaPaciente9!',
        )
        cls.medico = User.objects.create_user(
            username='medico1',
            email='medico1@example.test',
            cpf='55555555555',
            role=User.Role.PROFESSIONAL,
            password='SenhaMedico9!',
        )
        cls.admin_a = User.objects.create_user(
            username='admin1',
            email='admin1@example.test',
            cpf='66666666666',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
            password='SenhaAdmin9!',
        )
        cls.admin_b = User.objects.create_user(
            username='admin2',
            email='admin2@example.test',
            cpf='77777777777',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
            password='SenhaAdmin9!',
        )

    def test_login_paciente_com_cpf_formatado_e_email(self) -> None:
        from django.urls import reverse

        resposta_cpf = self.client.post(
            reverse('users:patient_login'),
            {'username': '444.444.444-44', 'password': 'SenhaPaciente9!'},
        )
        self.assertRedirects(resposta_cpf, reverse('users:patient_portal'))

        self.client.post(reverse('users:logout'))

        resposta_email = self.client.post(
            reverse('users:patient_login'),
            {'username': 'PACIENTE1@EXAMPLE.TEST', 'password': 'SenhaPaciente9!'},
        )
        self.assertRedirects(resposta_email, reverse('users:patient_portal'))

    def test_acesso_cruzado_entre_portais_retorna_403_e_registra_auditoria(self) -> None:
        from django.urls import reverse

        from audit.models import LoginAttempt

        resposta = self.client.post(
            reverse('users:professional_login'),
            {'username': self.paciente.cpf, 'password': 'SenhaPaciente9!'},
        )
        self.assertEqual(resposta.status_code, 403)
        self.assertTrue(
            LoginAttempt.objects.filter(
                user=self.paciente,
                result=LoginAttempt.Result.PORTAL_DENIED,
            ).exists()
        )

    def test_cinco_falhas_consecutivas_bloqueiam_conta_e_enfileiram_alerta(self) -> None:
        from django.urls import reverse

        from notifications.models import NotificationOutbox

        for _ in range(5):
            self.client.post(
                reverse('users:patient_login'),
                {'username': self.paciente.email, 'password': 'SenhaErrada1!'},
            )

        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.failed_login_attempts, 5)
        self.assertIsNotNone(self.paciente.locked_until)
        self.assertTrue(
            NotificationOutbox.objects.filter(recipient=self.paciente).exists()
        )

        # Mesmo com senha correta durante o bloqueio, não autentica
        resposta = self.client.post(
            reverse('users:patient_login'),
            {'username': self.paciente.email, 'password': 'SenhaPaciente9!'},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(resposta.wsgi_request.user.is_authenticated)

    def test_login_invalido_marca_erros_acessiveis_sem_erro(self) -> None:
        from django.urls import reverse

        resposta = self.client.post(
            reverse('users:patient_login'),
            {'username': self.paciente.email, 'password': 'errada'},
        )
        self.assertEqual(resposta.status_code, 200)

    def test_middleware_exige_troca_de_senha_no_primeiro_acesso(self) -> None:
        from django.urls import reverse

        self.medico.must_change_password = True
        self.medico.save(update_fields=('must_change_password',))
        self.client.force_login(self.medico)

        resposta = self.client.get(reverse('users:professional_portal'))
        self.assertRedirects(resposta, reverse('users:password_change'))

    def test_inativar_usuario_protege_ultimo_admin_e_registra_acao(self) -> None:
        from users.services import UltimoAdministradorAtivo, UserService

        self.client.force_login(self.admin_b)
        session_key_b = self.client.session.session_key

        UserService.inativar_usuario(self.admin_b.pk, self.admin_a.pk, '127.0.0.1')
        self.admin_b.refresh_from_db()
        self.assertFalse(self.admin_b.is_active)
        self.assertTrue(
            AdministrativeAction.objects.filter(
                actor=self.admin_a,
                target=self.admin_b,
                action=AdministrativeAction.Action.USER_INACTIVATED,
            ).exists()
        )

        # Sessão do usuário inativado foi revogada
        from django.contrib.sessions.models import Session

        self.assertFalse(Session.objects.filter(session_key=session_key_b).exists())

        with self.assertRaises(UltimoAdministradorAtivo):
            UserService.inativar_usuario(self.admin_a.pk, self.admin_a.pk, '127.0.0.1')
