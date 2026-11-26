from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.integrations.sms import SandboxSmsAdapter
from patients.models import ClinicalProfileHistory, Dependent, PatientProfile
from patients.services import (
    DependentService,
    DependenteNaoEncontrado,
    PatientService,
    SmsVerificationService,
)
from users.models import User


class PatientRegistrationAndProfileTests(TestCase):
    def _dados_cadastro_valido(self, *, cpf: str, email: str, phone: str, sms_code: str) -> dict:
        return {
            'cpf': cpf,
            'full_name': 'Maria Silva Santos',
            'birth_date': date(1990, 5, 15),
            'gender': 'female',
            'phone': phone,
            'sms_code': sms_code,
            'email': email,
            'password': 'SenhaForte9!',
            'has_disability': False,
            'disability_description': '',
            'blood_type': 'O+',
            'has_allergy': True,
            'allergy_description': 'Dipirona',
            'continuous_medications': 'Losartana 50mg',
            'height_cm': 165,
            'weight_kg': Decimal('64.5'),
            'has_hypertension': True,
            'has_diabetes': False,
            'consent_accepted': True,
        }

    def test_cadastro_titular_valido_com_sms_cria_perfil_e_historico(self) -> None:
        SmsVerificationService.enviar_codigo('11999998888')
        codigo = SandboxSmsAdapter.sent_codes['11999998888']

        paciente = PatientService.cadastrar_titular(
            self._dados_cadastro_valido(
                cpf='52998224725',
                email='maria@example.test',
                phone='11999998888',
                sms_code=codigo,
            ),
            ip_address='127.0.0.1',
        )

        self.assertEqual(paciente.user.role, User.Role.PATIENT)
        self.assertIsNotNone(paciente.phone_verified_at)
        self.assertEqual(paciente.consents.count(), 1)
        self.assertEqual(paciente.clinical_profile.history.count(), 1)

    def test_rejeita_menor_de_18_anos_cpf_invalido_e_alergia_sem_descricao(self) -> None:
        SmsVerificationService.enviar_codigo('11988887777')
        codigo = SandboxSmsAdapter.sent_codes['11988887777']

        dados = self._dados_cadastro_valido(
            cpf='11111111111',
            email='jovem@example.test',
            phone='11988887777',
            sms_code=codigo,
        )
        with self.assertRaises(ValidationError):
            PatientService.cadastrar_titular(dados)

        dados['cpf'] = '52998224725'
        dados['birth_date'] = date.today() - timedelta(days=365 * 17)
        with self.assertRaises(ValidationError):
            PatientService.cadastrar_titular(dados)

        dados['birth_date'] = date(1990, 5, 15)
        dados['allergy_description'] = ''
        with self.assertRaises(ValidationError):
            PatientService.cadastrar_titular(dados)

    def test_atualizacao_perfil_clinico_preserva_historico(self) -> None:
        SmsVerificationService.enviar_codigo('11977776666')
        codigo = SandboxSmsAdapter.sent_codes['11977776666']
        paciente = PatientService.cadastrar_titular(
            self._dados_cadastro_valido(
                cpf='52998224725',
                email='maria2@example.test',
                phone='11977776666',
                sms_code=codigo,
            ),
        )

        PatientService.atualizar_titular_e_perfil(
            paciente.user_id,
            {
                'full_name': 'Maria Silva Atualizada',
                'birth_date': date(1990, 5, 15),
                'gender': 'female',
                'phone': '11977776666',
                'has_disability': False,
                'disability_description': '',
                'blood_type': 'O+',
                'has_allergy': True,
                'allergy_description': 'Dipirona e Penicilina',
                'continuous_medications': 'Losartana 50mg',
                'height_cm': 165,
                'weight_kg': Decimal('65.0'),
                'has_hypertension': True,
                'has_diabetes': False,
            },
        )
        self.assertEqual(ClinicalProfileHistory.objects.filter(clinical_profile=paciente.clinical_profile).count(), 2)


class DependentManagementTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        SmsVerificationService.enviar_codigo('11966665555')
        codigo_a = SandboxSmsAdapter.sent_codes['11966665555']
        cls.titular_a = PatientService.cadastrar_titular(
            {
                'cpf': '52998224725',
                'full_name': 'Responsável A',
                'birth_date': date(1985, 3, 10),
                'gender': 'male',
                'phone': '11966665555',
                'sms_code': codigo_a,
                'email': 'resp_a@example.test',
                'password': 'SenhaForte9!',
                'has_disability': False,
                'disability_description': '',
                'blood_type': 'A+',
                'has_allergy': False,
                'allergy_description': '',
                'continuous_medications': '',
                'height_cm': 175,
                'weight_kg': Decimal('78.0'),
                'has_hypertension': False,
                'has_diabetes': False,
                'consent_accepted': True,
            }
        )
        SmsVerificationService.enviar_codigo('11955554444')
        codigo_b = SandboxSmsAdapter.sent_codes['11955554444']
        cls.titular_b = PatientService.cadastrar_titular(
            {
                'cpf': '15350946056',
                'full_name': 'Responsável B',
                'birth_date': date(1988, 7, 20),
                'gender': 'female',
                'phone': '11955554444',
                'sms_code': codigo_b,
                'email': 'resp_b@example.test',
                'password': 'SenhaForte9!',
                'has_disability': False,
                'disability_description': '',
                'blood_type': 'B+',
                'has_allergy': False,
                'allergy_description': '',
                'continuous_medications': '',
                'height_cm': 162,
                'weight_kg': Decimal('60.0'),
                'has_hypertension': False,
                'has_diabetes': False,
                'consent_accepted': True,
            }
        )

    def test_responsavel_cadastra_edita_e_desativa_dependente_com_isolamento(self) -> None:
        dependente = DependentService.cadastrar_dependente(
            self.titular_a.user_id,
            {
                'legal_relationship': Dependent.LegalRelationship.CHILD,
                'cpf': '39053344705',
                'full_name': 'Lucas Responsável A',
                'birth_date': date(2016, 4, 1),
                'gender': 'male',
                'has_disability': False,
                'disability_description': '',
                'blood_type': 'A+',
                'has_allergy': False,
                'allergy_description': '',
                'continuous_medications': '',
                'height_cm': 130,
                'weight_kg': Decimal('32.0'),
                'has_hypertension': False,
                'has_diabetes': False,
            },
        )
        self.assertEqual(dependente.guardian, self.titular_a)

        # Outro responsável não acessa dependente sem vínculo
        with self.assertRaises(DependenteNaoEncontrado):
            DependentService.obter_dependente(self.titular_b.user_id, dependente.pk)

        self.client.force_login(self.titular_b.user)
        resposta_alheia = self.client.get(
            reverse('patients:dependent_edit', kwargs={'dependent_id': dependente.pk}),
        )
        self.assertEqual(resposta_alheia.status_code, 404)

        # Desativar mantém registro sem exclusão física
        DependentService.desativar_dependente(self.titular_a.user_id, dependente.pk)
        dependente.refresh_from_db()
        self.assertFalse(dependente.is_active)
        self.assertIsNotNone(dependente.deactivated_at)
        self.assertEqual(DependentService.listar_dependentes(self.titular_a.user_id).count(), 0)
