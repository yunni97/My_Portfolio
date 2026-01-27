from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User
from .models import (
    Department, DoctorProfile, NurseProfile,
    Patient, Drug,
    MedicalRecord, TestOrder, MedicalDiagnosis, MedicalVitals, ClinicalRecord,
    Prescription, NursingNote, GenomicRecord,
    DicomStudy, DicomSeries, AiPrediction,
    Announcement, Appointment
)


# ============================================
# 커스텀 Admin Site - 모델 순서 제어
# ============================================

class CDSSAdminSite(AdminSite):
    site_header = 'CDSS 관리 시스템'
    site_title = 'CDSS Admin'
    index_title = '임상 의사결정지원 시스템'

    def get_app_list(self, request, app_label=None):
        """
        모델을 카테고리별로 그룹화하여 표시
        """
        app_dict = self._build_app_dict(request, app_label)

        # 카테고리별 모델 정의
        categories = {
            '👥 인력 관리': ['department', 'doctorprofile', 'nurseprofile'],
            '👤 환자 관리': ['patient'],
            '📋 진료 기록': ['medicalrecord', 'testorder', 'medicaldiagnosis', 'medicalvitals', 'clinicalrecord'],
            '🔬 영상 검사': ['dicomstudy', 'dicomseries'],
            '💊 약물 & 처방': ['drug', 'prescription'],
            '🤖 AI & 유전체': ['aiprediction', 'genomicrecord'],
            '📅 예약 & 간호 & 공지': ['appointment', 'nursingnote', 'announcement'],
        }

        # main 앱을 카테고리별로 분할
        result = []

        for app in app_dict.values():
            if app['app_label'] == 'main':
                # 카테고리별로 앱 생성
                for category_name, model_list in categories.items():
                    category_models = []

                    for model in app['models']:
                        if model['object_name'].lower() in model_list:
                            category_models.append(model)

                    # 카테고리에 모델이 있으면 추가
                    if category_models:
                        # 모델을 정의된 순서대로 정렬
                        category_models.sort(
                            key=lambda x: model_list.index(x['object_name'].lower())
                            if x['object_name'].lower() in model_list else 999
                        )

                        result.append({
                            'name': category_name,
                            'app_label': 'main',
                            'app_url': app['app_url'],
                            'has_module_perms': app['has_module_perms'],
                            'models': category_models,
                        })
            else:
                # main 앱이 아닌 경우 그대로 추가
                result.append(app)

        return result


# 커스텀 Admin Site 인스턴스 생성
admin_site = CDSSAdminSite(name='cdss_admin')


# 기본 ModelAdmin
class CDSSModelAdmin(admin.ModelAdmin):
    """CDSS 기본 Admin"""
    pass


# ============================================
# 👥 1. 인력 관리
# ============================================

class DoctorProfileAdminForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = '__all__'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if self.instance.pk:
                if DoctorProfile.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('이미 사용 중인 전화번호입니다.')
            else:
                if DoctorProfile.objects.filter(phone=phone).exists():
                    raise forms.ValidationError('이미 사용 중인 전화번호입니다.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            if self.instance.pk:
                if DoctorProfile.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('이미 사용 중인 이메일입니다.')
            else:
                if DoctorProfile.objects.filter(email=email).exists():
                    raise forms.ValidationError('이미 사용 중인 이메일입니다.')
        return email


@admin.register(Department, site=admin_site)
class DepartmentAdmin(CDSSModelAdmin):
    list_display = ['department_id', 'department_code', 'department']
    search_fields = ['department_code', 'department']
    list_per_page = 20


@admin.register(DoctorProfile, site=admin_site)
class DoctorProfileAdmin(CDSSModelAdmin):
    form = DoctorProfileAdminForm
    list_display = ['doctor_id', 'name', 'sex', 'phone', 'email', 'departments', 'position', 'status', 'created_at']
    list_filter = ['sex', 'status', 'departments']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['doctor_id', 'created_at', 'updated_at']
    list_per_page = 20
    ordering = ['-created_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('doctor_id', 'name', 'sex')
        }),
        ('연락처 정보', {
            'fields': ('phone', 'email')
        }),
        ('소속 정보', {
            'fields': ('departments', 'position', 'status')
        }),
        ('관리자 정보', {
            'fields': ('user',)
        }),
        ('시스템 정보', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NurseProfile, site=admin_site)
class NurseProfileAdmin(CDSSModelAdmin):
    list_display = ['nurse_id', 'name', 'sex', 'phone', 'email', 'department', 'position', 'status', 'created_at']
    list_filter = ['sex', 'status', 'department']
    search_fields = ['name', 'phone', 'email']
    readonly_fields = ['nurse_id', 'created_at']
    list_per_page = 20
    ordering = ['-created_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('nurse_id', 'name', 'sex')
        }),
        ('연락처 정보', {
            'fields': ('phone', 'email')
        }),
        ('소속 정보', {
            'fields': ('department', 'position', 'status')
        }),
        ('관리자 정보', {
            'fields': ('user',)
        }),
        ('시스템 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================
# 👤 2. 환자 관리
# ============================================

@admin.register(Patient, site=admin_site)
class PatientAdmin(CDSSModelAdmin):
    list_display = ['patient_id', 'name', 'birth_date', 'sex', 'phone', 'diagnosis_date', 'created_at']
    list_filter = ['sex', 'created_at']
    search_fields = ['name', 'phone', 'resident_number']
    readonly_fields = ['patient_id', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 30
    ordering = ['-created_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('patient_id', 'name', 'sex', 'birth_date', 'resident_number')
        }),
        ('연락처 정보', {
            'fields': ('phone', 'address')
        }),
        ('진단 정보', {
            'fields': ('diagnosis_date',)
        }),
        ('시스템 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================
# 📋 3. 진료 기록
# ============================================

@admin.register(MedicalRecord, site=admin_site)
class MedicalRecordAdmin(CDSSModelAdmin):
    list_display = ['record_id', 'patient', 'doctor', 'visit_date', 'chief_complaint']
    list_filter = ['visit_date', 'doctor']
    search_fields = ['patient__name', 'doctor__name', 'chief_complaint']
    readonly_fields = ['record_id', 'visit_date']
    date_hierarchy = 'visit_date'
    list_per_page = 30
    ordering = ['-visit_date']

    fieldsets = (
        ('기본 정보', {
            'fields': ('record_id', 'patient', 'doctor', 'visit_date')
        }),
        ('진료 내용 (SOAP)', {
            'fields': ('chief_complaint', 'subjective', 'objective', 'assessment', 'plan')
        }),
    )


@admin.register(TestOrder, site=admin_site)
class TestOrderAdmin(CDSSModelAdmin):
    list_display = ['order_id', 'record', 'test_type', 'body_part', 'status', 'ordered_at', 'completed_at']
    list_filter = ['test_type', 'status', 'ordered_at']
    search_fields = ['record__patient__name', 'body_part']
    readonly_fields = ['order_id', 'ordered_at']
    date_hierarchy = 'ordered_at'
    list_per_page = 30
    ordering = ['-ordered_at']


@admin.register(MedicalDiagnosis, site=admin_site)
class MedicalDiagnosisAdmin(CDSSModelAdmin):
    list_display = ['diagnosis_id', 'record', 'icd_code', 'diagnosis_name']
    list_filter = ['icd_code']
    search_fields = ['icd_code', 'diagnosis_name', 'record__patient__name']
    readonly_fields = ['diagnosis_id']
    list_per_page = 30


@admin.register(MedicalVitals, site=admin_site)
class MedicalVitalsAdmin(CDSSModelAdmin):
    list_display = ['vital_id', 'patient', 'bp_systolic', 'bp_diastolic', 'heart_rate', 'temperature', 'measured_at']
    list_filter = ['measured_at']
    search_fields = ['patient__name']
    readonly_fields = ['vital_id', 'measured_at']
    date_hierarchy = 'measured_at'
    list_per_page = 30
    ordering = ['-measured_at']


@admin.register(ClinicalRecord, site=admin_site)
class ClinicalRecordAdmin(CDSSModelAdmin):
    list_display = ['clinical_id', 'record', 'tumor_stage', 'child_pugh', 'afp', 'test_date']
    list_filter = ['test_date', 'child_pugh']
    search_fields = ['record__patient__name', 'tumor_stage']
    readonly_fields = ['clinical_id', 'test_date']
    date_hierarchy = 'test_date'
    list_per_page = 30
    ordering = ['-test_date']

    fieldsets = (
        ('기본 정보', {
            'fields': ('clinical_id', 'record', 'test_date')
        }),
        ('병기 정보', {
            'fields': ('tumor_stage', 'child_pugh')
        }),
        ('혈액 검사 수치', {
            'fields': ('afp', 'albumin', 'bilirubin', 'platelet', 'creatinine')
        }),
    )


# ============================================
# 🔬 4. 영상 검사 (DICOM)
# ============================================

@admin.register(DicomStudy, site=admin_site)
class DicomStudyAdmin(CDSSModelAdmin):
    list_display = ['study_uid', 'patient', 'study_date', 'modality', 'study_desc', 'created_at']
    list_filter = ['modality', 'study_date']
    search_fields = ['study_uid', 'patient__name', 'study_desc']
    readonly_fields = ['created_at']
    date_hierarchy = 'study_date'
    list_per_page = 30
    ordering = ['-study_date']


@admin.register(DicomSeries, site=admin_site)
class DicomSeriesAdmin(CDSSModelAdmin):
    list_display = ['series_uid', 'study', 'series_number', 'phase_label', 'slice_count', 'is_selected']
    list_filter = ['phase_label', 'is_selected']
    search_fields = ['series_uid', 'study__patient__name', 'series_desc']
    list_per_page = 30

    fieldsets = (
        ('기본 정보', {
            'fields': ('series_uid', 'study', 'series_number', 'series_desc')
        }),
        ('페이즈 정보', {
            'fields': ('phase_label', 'slice_count')
        }),
        ('파일 경로', {
            'fields': ('npy_path', 'thumbnail_path')
        }),
        ('학습 설정', {
            'fields': ('is_selected',)
        }),
    )


# ============================================
# 💊 5. 약물 & 처방 관리
# ============================================

@admin.register(Drug, site=admin_site)
class DrugAdmin(CDSSModelAdmin):
    list_display = ['drug_id', 'get_name_kr', 'drug_category']
    list_filter = ['drug_category']
    search_fields = ['name_kr', 'name_eng', 'drug_category']
    readonly_fields = ['drug_id']
    list_per_page = 50

    def get_name_kr(self, obj):
        return obj.name_kr[:50] if obj.name_kr and len(obj.name_kr) > 50 else obj.name_kr
    get_name_kr.short_description = '약물명(한글)'

    fieldsets = (
        ('기본 정보', {
            'fields': ('drug_id', 'name_kr', 'name_eng', 'drug_category')
        }),
        ('효능/주의사항', {
            'fields': ('efficacy', 'precautions')
        }),
    )


@admin.register(Prescription, site=admin_site)
class PrescriptionAdmin(CDSSModelAdmin):
    list_display = ['prescription_id', 'record', 'drug_name', 'dosage', 'frequency', 'duration', 'created_at']
    list_filter = ['created_at']
    search_fields = ['drug_name', 'record__patient__name']
    readonly_fields = ['prescription_id', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 30
    ordering = ['-created_at']


# ============================================
# 🤖 6. AI 분석 & 유전체
# ============================================

@admin.register(AiPrediction, site=admin_site)
class AiPredictionAdmin(CDSSModelAdmin):
    list_display = ['prediction_id', 'patient', 'series', 'risk_score', 'survival_prob_1yr', 'survival_prob_3yr', 'analyzed_at']
    list_filter = ['analyzed_at']
    search_fields = ['patient__name', 'series__series_uid']
    readonly_fields = ['prediction_id', 'analyzed_at']
    date_hierarchy = 'analyzed_at'
    list_per_page = 30
    ordering = ['-analyzed_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('prediction_id', 'patient', 'series', 'analyzed_at')
        }),
        ('예측 결과', {
            'fields': ('risk_score', 'survival_prob_1yr', 'survival_prob_3yr')
        }),
        ('입력 데이터 스냅샷', {
            'fields': ('input_clinical_features', 'input_gene_data'),
            'classes': ('collapse',)
        }),
        ('시각화', {
            'fields': ('gradcam_path',)
        }),
    )


@admin.register(GenomicRecord, site=admin_site)
class GenomicRecordAdmin(CDSSModelAdmin):
    list_display = ['sample_id', 'patient', 'sample_date', 'order', 'created_at']
    list_filter = ['sample_date', 'created_at']
    search_fields = ['patient__name', 'sample_id']
    readonly_fields = ['sample_id', 'created_at']
    date_hierarchy = 'sample_date'
    list_per_page = 30
    ordering = ['-sample_date']

    fieldsets = (
        ('기본 정보', {
            'fields': ('sample_id', 'patient', 'order', 'sample_date')
        }),
        ('유전자 데이터', {
            'fields': ('gene_data',),
            'classes': ('collapse',)
        }),
        ('시스템 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


# ============================================
# 📅 7. 예약 & 간호 & 공지
# ============================================

@admin.register(Appointment, site=admin_site)
class AppointmentAdmin(CDSSModelAdmin):
    list_display = ['appointment_id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status', 'created_at']
    list_filter = ['status', 'appointment_date', 'created_at']
    search_fields = ['patient__name', 'doctor__name']
    readonly_fields = ['appointment_id', 'created_at']
    date_hierarchy = 'appointment_date'
    list_per_page = 30
    ordering = ['-appointment_date', '-appointment_time']

    fieldsets = (
        ('기본 정보', {
            'fields': ('appointment_id', 'patient', 'doctor')
        }),
        ('예약 정보', {
            'fields': ('appointment_date', 'appointment_time', 'status')
        }),
        ('메모', {
            'fields': ('notes',)
        }),
        ('시스템 정보', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(NursingNote, site=admin_site)
class NursingNoteAdmin(CDSSModelAdmin):
    list_display = ['note_id', 'patient', 'nurse', 'created_at']
    list_filter = ['created_at']
    search_fields = ['patient__name', 'nurse__name', 'note_content']
    readonly_fields = ['note_id', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 30
    ordering = ['-created_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('note_id', 'patient', 'nurse', 'created_at')
        }),
        ('간호 기록 내용', {
            'fields': ('note_content',)
        }),
    )


@admin.register(Announcement, site=admin_site)
class AnnouncementAdmin(CDSSModelAdmin):
    list_display = ['announcement_id', 'title', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['announcement_id', 'created_at']
    date_hierarchy = 'created_at'
    list_per_page = 20
    ordering = ['-created_at']

    fieldsets = (
        ('기본 정보', {
            'fields': ('announcement_id', 'user', 'created_at')
        }),
        ('공지 내용', {
            'fields': ('title', 'content')
        }),
    )
