from datetime import date

from django.contrib.sessions.models import Session
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import AdministrativeAction
from professionals.models import ProfessionalProfile, ShiftHistory
from professionals.services import ProfessionalService
from users.models import User
from users.services import PermissaoGestaoUsuariosNegada


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProfessionalManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin = User.objects.create_user(
            username='admin-prof',
            email='admin-prof@example.test',
            cpf='52998224725',
            role=User.Role.ADMINISTRATOR,
            is_staff=True,
            password='SenhaAdmin9!',
        )
        cls.paciente = User.objects.create_user(
            username='pac-prof',
            email='pac-prof@example.test',
            cpf='15350946056',
            role=User.Role.PATIENT,
            password='SenhaPaciente9!',
        )

    def _documento_valido(self) -> SimpleUploadedFile:
        return SimpleUploadedFile('crm.pdf', b'%PDF-1.4 fake pdf', content_type='application/pdf')

    def test_apenas_admin_cadastra_e_homologa_medico(self) -> None:
        dados = {
            'cpf': '39053344705',
            'full_name': 'Dra. Ana Paula Souza',
            'birth_date': date(1985, 6, 20),
            'phone': '11988887777',
            'email': 'ana.souza@clinica.test',
            'crm_number': '123456',
            'crm_uf': 'SP',
        }

        with self.assertRaises(PermissaoGestaoUsuariosNegada):
            ProfessionalService.cadastrar_profissional(
                self.paciente.pk,
                dados,
                self._documento_valido(),
            )

        perfil = ProfessionalService.cadastrar_profissional(
            self.admin.pk,
            dados,
            self._documento_valido(),
            ip_address='127.0.0.1',
        )
        self.assertEqual(perfil.homologation_status, ProfessionalProfile.HomologationStatus.PENDING)
        self.assertFalse(perfil.user.is_active)

        perfil, enviada = ProfessionalService.homologar_profissional(
            self.admin.pk,
            perfil.pk,
            crm_regular=True,
            icp_brasil_active=True,
            ip_address='127.0.0.1',
        )
        self.assertTrue(enviada)
        self.assertEqual(perfil.homologation_status, ProfessionalProfile.HomologationStatus.APPROVED)
        self.assertTrue(perfil.user.is_active)
        self.assertTrue(perfil.user.must_change_password)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(
            AdministrativeAction.objects.filter(
                actor=self.admin,
                target=perfil.user,
                action=AdministrativeAction.Action.PROFESSIONAL_APPROVED,
            ).exists()
        )

    def test_disponibilidade_online_exige_icp_brasil_e_suspensao_revoga_sessao(self) -> None:
        perfil = ProfessionalService.cadastrar_profissional(
            self.admin.pk,
            {
                'cpf': '39053344705',
                'full_name': 'Dr. Carlos Mendes',
                'birth_date': date(1980, 1, 15),
                'phone': '11977776666',
                'email': 'carlos@clinica.test',
                'crm_number': '654321',
                'crm_uf': 'RJ',
            },
            self._documento_valido(),
        )
        perfil, _ = ProfessionalService.homologar_profissional(
            self.admin.pk,
            perfil.pk,
            crm_regular=True,
            icp_brasil_active=False,
        )

        # Sem ICP-Brasil ativo não pode ficar Online
        with self.assertRaises(ValidationError):
            ProfessionalService.alterar_disponibilidade(
                perfil.user_id,
                ProfessionalProfile.Availability.ONLINE,
            )

        perfil.icp_brasil_active = True
        perfil.save(update_fields=('icp_brasil_active',))
        ProfessionalService.alterar_disponibilidade(
            perfil.user_id,
            ProfessionalProfile.Availability.ONLINE,
            operational_phone='11912345678',
        )
        self.assertEqual(ShiftHistory.objects.filter(professional=perfil).count(), 1)

        # Suspensão revoga sessões e impede acesso
        perfil.user.must_change_password = False
        perfil.user.save(update_fields=('must_change_password',))
        self.client.force_login(perfil.user)
        session_key = self.client.session.session_key

        ProfessionalService.suspender_profissional(self.admin.pk, perfil.pk, '127.0.0.1')
        perfil.refresh_from_db()
        self.assertEqual(perfil.homologation_status, ProfessionalProfile.HomologationStatus.SUSPENDED)
        self.assertEqual(perfil.availability, ProfessionalProfile.Availability.OFFLINE)
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())

        resposta = self.client.get(reverse('professionals:availability'))
        self.assertEqual(resposta.status_code, 302)
