from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from patients.models import BloodType, Gender, SmsVerificationChallenge
from patients.services import PatientService
from prescriptions.models import PrescriptionReview
from prescriptions.services import PrescriptionReviewService
from professionals.services import ProfessionalService
from triage.services import TriageService

from .models import MedicalRecordAccessLog
from .services import MedicalRecordService, PermissaoProntuarioNegada

User = get_user_model()


def _criar_paciente(cpf: str, email: str, full_name: str, phone: str):
    SmsVerificationChallenge.objects.create(
        phone=phone,
        code_hash=make_password('123456'),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    return PatientService.cadastrar_titular(
        {
            'full_name': full_name,
            'cpf': cpf,
            'email': email,
            'phone': phone,
            'sms_code': '123456',
            'birth_date': date(1990, 1, 15),
            'gender': Gender.FEMALE,
            'password': 'SenhaForte!123',
            'consent_accepted': True,
            'has_disability': False,
            'disability_description': '',
            'blood_type': BloodType.O_POS,
            'has_allergy': False,
            'allergy_description': '',
            'continuous_medications': '',
            'height_cm': 165,
            'weight_kg': Decimal('60.0'),
            'has_hypertension': False,
            'has_diabetes': False,
        },
        ip_address='127.0.0.1',
    )


class MedicalRecordTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            username='admin-rec',
            cpf='55566677700',
            email='admin.rec@example.com',
            password='AdminPassword!123',
            role=User.Role.ADMINISTRATOR,
            first_name='Admin',
            last_name='Rec',
        )
        cls.paciente_a = _criar_paciente('52998224725', 'rec.a@example.com', 'Helena Prontuario', '11944441111')
        cls.paciente_b = _criar_paciente('11144477735', 'rec.b@example.com', 'Igor Terceiro', '11944442222')

        comprovante_1 = SimpleUploadedFile('crm1.pdf', b'%PDF-1.4 crm1', content_type='application/pdf')
        cls.medico_vinculado = ProfessionalService.cadastrar_profissional(
            cls.admin.id,
            {
                'full_name': 'Dra. Sofia Vinculada',
                'cpf': '39053344705',
                'email': 'sofia.rec@example.com',
                'birth_date': date(1984, 3, 20),
                'phone': '11933331111',
                'crm_number': '111222',
                'crm_uf': 'SP',
            },
            crm_document=comprovante_1,
        )
        ProfessionalService.homologar_profissional(
            cls.admin.id,
            cls.medico_vinculado.pk,
            crm_regular=True,
            icp_brasil_active=True,
        )
        cls.medico_vinculado.refresh_from_db()

        comprovante_2 = SimpleUploadedFile('crm2.pdf', b'%PDF-1.4 crm2', content_type='application/pdf')
        cls.medico_sem_vinculo = ProfessionalService.cadastrar_profissional(
            cls.admin.id,
            {
                'full_name': 'Dr. Paulo Sem Vinculo',
                'cpf': '71428793860',
                'email': 'paulo.rec@example.com',
                'birth_date': date(1981, 7, 11),
                'phone': '11933332222',
                'crm_number': '333444',
                'crm_uf': 'SP',
            },
            crm_document=comprovante_2,
        )
        ProfessionalService.homologar_profissional(
            cls.admin.id,
            cls.medico_sem_vinculo.pk,
            crm_regular=True,
            icp_brasil_active=True,
        )
        cls.medico_sem_vinculo.refresh_from_db()

    def test_linha_do_tempo_filtros_retificacao_e_auditoria_acesso(self):
        triagem, _ = TriageService.iniciar_triagem(
            self.paciente_a.user_id,
            symptoms_description='Dor de cabeça leve recorrente',
            symptom_onset='Hoje',
            pain_intensity=3,
            identity_confirmed=True,
        )
        triagem, _ = TriageService.concluir_triagem(
            self.paciente_a.user_id,
            triagem.pk,
            responses={'pergunta_1': 'Sem febre'},
        )
        PrescriptionReviewService.registrar_revisao(
            self.medico_vinculado.user_id,
            triagem.pk,
            decision=PrescriptionReview.Decision.APPROVED,
            clinical_opinion='Cefaleia tensional leve.',
            prescribed_medication='Paracetamol 750mg',
            dosage_and_route='1 comprimido VO 8/8h',
        )

        # Titular consulta próprio prontuário e vê triagem, parecer e receita
        eventos = MedicalRecordService.consultar_prontuario(
            self.paciente_a.user_id,
            patient_id=self.paciente_a.pk,
        )
        tipos = {ev.event_type for ev in eventos}
        self.assertTrue({'triage', 'review', 'prescription'}.issubset(tipos))

        # Filtro por palavra-chave
        filtrados = MedicalRecordService.consultar_prontuario(
            self.paciente_a.user_id,
            patient_id=self.paciente_a.pk,
            keyword='Paracetamol',
        )
        self.assertEqual(len(filtrados), 1)
        self.assertEqual(filtrados[0].event_type, 'prescription')

        # Período inválido rejeitado
        with self.assertRaises(ValidationError):
            MedicalRecordService.consultar_prontuario(
                self.paciente_a.user_id,
                patient_id=self.paciente_a.pk,
                start_date=date(2026, 12, 10),
                end_date=date(2026, 12, 1),
            )

        # Terceiro sem vínculo é bloqueado e tentativa fica auditada
        with self.assertRaises(PermissaoProntuarioNegada):
            MedicalRecordService.consultar_prontuario(
                self.paciente_b.user_id,
                patient_id=self.paciente_a.pk,
            )
        self.assertTrue(
            MedicalRecordAccessLog.objects.filter(
                actor=self.paciente_b.user,
                patient=self.paciente_a,
                allowed=False,
            ).exists()
        )

        # Médico sem vínculo é bloqueado; médico vinculado acessa e registra CRM
        with self.assertRaises(PermissaoProntuarioNegada):
            MedicalRecordService.consultar_prontuario(
                self.medico_sem_vinculo.user_id,
                patient_id=self.paciente_a.pk,
            )

        MedicalRecordService.consultar_prontuario(
            self.medico_vinculado.user_id,
            patient_id=self.paciente_a.pk,
        )
        self.assertTrue(
            MedicalRecordAccessLog.objects.filter(
                actor=self.medico_vinculado.user,
                crm_snapshot='111222/SP',
                allowed=True,
            ).exists()
        )

        # Retificação preserva o evento original e anexa nova retificação
        MedicalRecordService.registrar_retificacao(
            self.medico_vinculado.user_id,
            target_event_type='triage',
            target_event_id=triagem.pk,
            amendment_text='Esclarecimento clínico complementar sem alterar registro original.',
            patient_id=self.paciente_a.pk,
        )
        eventos_pos = MedicalRecordService.consultar_prontuario(
            self.paciente_a.user_id,
            patient_id=self.paciente_a.pk,
            event_type='triage',
        )
        self.assertEqual(len(eventos_pos[0].amendments), 1)
