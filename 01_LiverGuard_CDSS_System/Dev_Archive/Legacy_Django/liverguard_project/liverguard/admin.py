from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import (
    Patients, DoctorProfiles, NurseProfiles, Departments,
    MedicalRecords, MedicalDiagnosis, MedicalVitals, BloodResults,
    MedicalStudy, MedicalSeries, NursingNotes,
    Drugs, DrugForm, DrugRoute, DrugFrequency, Prescriptions, PrescriptionDrug,
    DeseaseManage, Announcements
)
from .forms import DoctorProfileAdminForm


# 커스텀 Admin Site
class LiverGuardAdminSite(AdminSite):
    site_header = 'LiverGuard 관리자'
    site_title = 'LiverGuard Admin'
    index_title = '간암 의사결정지원시스템 관리'

    def has_permission(self, request):
        """
        모든 superuser에게 admin 접근 권한 부여
        """
        return request.user.is_active and request.user.is_staff


# 기본 admin site를 커스텀 site로 교체
admin.site = LiverGuardAdminSite()
admin.site.__class__ = LiverGuardAdminSite


# managed=False 모델을 위한 권한 우회 Mixin
class UnmanagedModelAdmin(admin.ModelAdmin):
    """
    managed=False인 모델들의 권한 체크를 우회하는 Mixin
    superuser는 모든 권한을 가짐
    """
    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_staff

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_staff


# ============================================
# 🔑 핵심 관리 (의사 & 약물)
# ============================================

@admin.register(DoctorProfiles)
class DoctorProfilesAdmin(UnmanagedModelAdmin):
    form = DoctorProfileAdminForm
    list_display = ['doctor_id', 'name', 'sex', 'phone', 'email', 'status', 'position', 'departments', 'last_login']
    list_filter = ['status', 'sex', 'departments']
    search_fields = ['name', 'doctor_id', 'email', 'phone']
    exclude = ['password']
    list_per_page = 30

    fieldsets = (
        ('기본 정보', {
            'fields': ('doctor_id', 'name', 'sex', 'phone', 'email')
        }),
        ('근무 정보', {
            'fields': ('departments', 'position', 'status', 'license_number')
        }),
        ('프로필', {
            'fields': ('profile_image',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Drugs)
class DrugsAdmin(UnmanagedModelAdmin):
    list_display = ['drug_id', 'get_name_kr', 'drug_category', 'created_at']
    list_filter = ['drug_category', 'created_at']
    search_fields = ['name_kr', 'name_eng', 'drug_category']
    list_per_page = 50
    date_hierarchy = 'created_at'

    def get_name_kr(self, obj):
        return obj.name_kr[:50] if obj.name_kr and len(obj.name_kr) > 50 else obj.name_kr
    get_name_kr.short_description = '약물명(한글)'

    fieldsets = (
        ('기본 정보', {
            'fields': ('name_kr', 'name_eng', 'drug_category')
        }),
        ('용법/효능', {
            'fields': ('dosage', 'instructions', 'efficacy')
        }),
        ('주의사항', {
            'fields': ('precautions', 'contraindications', 'common_side_effects', 'serious_side_effects'),
            'classes': ('collapse',)
        }),
        ('기타', {
            'fields': ('smiles',),
            'classes': ('collapse',)
        }),
    )


# ============================================
# 👤 환자 관리
# ============================================

@admin.register(Patients)
class PatientsAdmin(UnmanagedModelAdmin):
    list_display = ['patient_id', 'name', 'birth_date', 'sex', 'phone', 'created_at']
    list_filter = ['sex', 'created_at']
    search_fields = ['name', 'phone', 'resident_number']
    date_hierarchy = 'created_at'
    list_per_page = 30


@admin.register(DeseaseManage)
class DeseaseManageAdmin(UnmanagedModelAdmin):
    list_display = ['desease_manage_id', 'patient', 'diagnosis_date', 'bclc_stage', 'treatment_type']
    list_filter = ['bclc_stage', 'treatment_type', 'diagnosis_date']
    search_fields = ['patient__name']
    date_hierarchy = 'diagnosis_date'
    list_per_page = 30


# ============================================
# 📋 진료 기록
# ============================================

@admin.register(MedicalRecords)
class MedicalRecordsAdmin(UnmanagedModelAdmin):
    list_display = ['record_id', 'patient', 'doctor_id', 'visit_date', 'chief_complatint']
    list_filter = ['visit_date']
    search_fields = ['patient__name', 'doctor_id', 'chief_complatint']
    date_hierarchy = 'visit_date'
    list_per_page = 30


@admin.register(MedicalDiagnosis)
class MedicalDiagnosisAdmin(UnmanagedModelAdmin):
    list_display = ['diagnosis_id', 'record', 'icd_code', 'diagnosis_name', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['icd_code', 'diagnosis_name']
    list_per_page = 30


@admin.register(MedicalVitals)
class MedicalVitalsAdmin(UnmanagedModelAdmin):
    list_display = ['vital_id', 'record', 'bp_systolic', 'bp_diastolic', 'heart_rate', 'temperature']
    search_fields = ['record__patient__name']
    list_per_page = 30


@admin.register(BloodResults)
class BloodResultsAdmin(UnmanagedModelAdmin):
    list_display = ['blood_id', 'record', 'ast', 'alt', 'afp', 'taken_at']
    list_filter = ['taken_at']
    search_fields = ['record__patient__name']
    date_hierarchy = 'taken_at'
    list_per_page = 30


# ============================================
# 🔬 영상 검사
# ============================================

@admin.register(MedicalStudy)
class MedicalStudyAdmin(UnmanagedModelAdmin):
    list_display = ['study_id', 'record', 'modality', 'body_part', 'study_date']
    list_filter = ['modality', 'study_date']
    search_fields = ['record__patient__name', 'body_part']
    date_hierarchy = 'study_date'
    list_per_page = 30


@admin.register(MedicalSeries)
class MedicalSeriesAdmin(UnmanagedModelAdmin):
    list_display = ['series_id', 'study', 'slice_count']
    search_fields = ['study__record__patient__name']
    list_per_page = 30


# ============================================
# 💊 처방 관리
# ============================================

@admin.register(Prescriptions)
class PrescriptionsAdmin(UnmanagedModelAdmin):
    list_display = ['prescription_id', 'record', 'medication_name', 'status', 'dosage', 'due_date']
    list_filter = ['status', 'created_at']
    search_fields = ['medication_name', 'record__patient__name']
    date_hierarchy = 'created_at'
    list_per_page = 30


@admin.register(PrescriptionDrug)
class PrescriptionDrugAdmin(UnmanagedModelAdmin):
    list_display = ['prescription', 'drug']
    search_fields = ['prescription__medication_name', 'drug__name_kr']
    list_per_page = 30


# ============================================
# 🏥 병원 조직
# ============================================

@admin.register(Departments)
class DepartmentsAdmin(UnmanagedModelAdmin):
    list_display = ['department_id', 'department_code', 'department']
    search_fields = ['department', 'department_code']
    list_per_page = 20


@admin.register(NurseProfiles)
class NurseProfilesAdmin(UnmanagedModelAdmin):
    list_display = ['nurse_id', 'name', 'sex', 'phone', 'status', 'shift_type', 'departments']
    list_filter = ['status', 'sex', 'shift_type', 'departments']
    search_fields = ['name', 'phone', 'email']
    list_per_page = 20


# ============================================
# 💬 간호 기록 & 공지사항
# ============================================

@admin.register(NursingNotes)
class NursingNotesAdmin(UnmanagedModelAdmin):
    list_display = ['note_id', 'record', 'note_type', 'abnormal_flag', 'nurse_id', 'created_at']
    list_filter = ['note_type', 'abnormal_flag', 'created_at']
    search_fields = ['record__patient__name']
    date_hierarchy = 'created_at'
    list_per_page = 30


@admin.register(Announcements)
class AnnouncementsAdmin(UnmanagedModelAdmin):
    list_display = ['announcements_id', 'title', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
    list_per_page = 20


# ============================================
# 💊 약물 상세 정보
# ============================================

@admin.register(DrugForm)
class DrugFormAdmin(UnmanagedModelAdmin):
    list_display = ['form_id', 'form']
    search_fields = ['form']
    list_per_page = 20


@admin.register(DrugRoute)
class DrugRouteAdmin(UnmanagedModelAdmin):
    list_display = ['route_id', 'route']
    search_fields = ['route']
    list_per_page = 20


@admin.register(DrugFrequency)
class DrugFrequencyAdmin(UnmanagedModelAdmin):
    list_display = ['frequency_id', 'frequency']
    search_fields = ['frequency']
    list_per_page = 20
