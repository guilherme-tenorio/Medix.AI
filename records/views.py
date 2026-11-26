from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from patients.services import DependentService, PatientService, PermissaoPacienteNegada
from users.models import User

from .forms import MedicalRecordFilterForm
from .services import (
    MedicalRecordService,
    PermissaoProntuarioNegada,
    ProntuarioNaoEncontrado,
)


class MedicalRecordTimelineView(LoginRequiredMixin, View):
    template_name = 'records/timeline.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        form = MedicalRecordFilterForm(request.GET or None)
        dependent_id_raw = request.GET.get('dependent_id')
        patient_id_raw = request.GET.get('patient_id')

        patient_id = int(patient_id_raw) if patient_id_raw and patient_id_raw.isdigit() else None
        dependent_id = int(dependent_id_raw) if dependent_id_raw and dependent_id_raw.isdigit() else None

        dependentes = []
        if request.user.role == User.Role.PATIENT:
            perfil = PatientService.obter_perfil_por_usuario(request.user.id)
            if perfil is None:
                raise PermissionDenied
            if patient_id is None and dependent_id is None:
                patient_id = perfil.pk
            try:
                dependentes = DependentService.listar_dependentes(request.user.id)
            except PermissaoPacienteNegada:
                dependentes = []

        eventos = []
        if form.is_valid():
            try:
                eventos = MedicalRecordService.consultar_prontuario(
                    request.user.id,
                    patient_id=patient_id,
                    dependent_id=dependent_id,
                    start_date=form.cleaned_data.get('start_date'),
                    end_date=form.cleaned_data.get('end_date'),
                    event_type=form.cleaned_data.get('event_type', ''),
                    risk_color=form.cleaned_data.get('risk_color', ''),
                    keyword=form.cleaned_data.get('keyword', ''),
                    ip_address=request.META.get('REMOTE_ADDR'),
                )
            except ProntuarioNaoEncontrado:
                raise Http404 from None
            except PermissaoProntuarioNegada:
                raise PermissionDenied from None
            except ValidationError as erro:
                for msg in erro.messages:
                    form.add_error(None, msg)

        return render(
            request,
            self.template_name,
            {
                'form': form,
                'eventos': eventos,
                'dependentes': dependentes,
            },
        )
