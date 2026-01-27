from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Patient, Announcement, Drug, DrugInteraction, DoctorProfile
from .forms import DoctorProfileAdminForm

# Django admin에서 Group 모델 숨김 (사용하지 않음)
admin.site.unregister(Group)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    """공지사항 관리자"""
    list_display = ['title', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'content']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content', 'is_active')
        }),
    )
    
    ordering = ['-created_at']


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    """약물 정보 관리자"""
    list_display = ['drug_code', 'drug_name_kr', 'drug_category', 'updated_at']
    list_filter = ['drug_category']
    search_fields = ['drug_code', 'drug_name_kr', 'drug_name_en']

    fieldsets = (
        ('기본 정보', {
            'fields': ('drug_code', 'drug_name_kr', 'drug_name_en', 'drug_category')
        }),
        ('용법/용량', {
            'fields': ('dosage',)
        }),
        ('효능/효과', {
            'fields': ('efficacy',)
        }),
        ('부작용', {
            'fields': ('common_side_effects', 'serious_side_effects')
        }),
        ('주의사항', {
            'fields': ('precautions', 'contraindications', 'interactions')
        }),
    )

    ordering = ['drug_name_kr']


@admin.register(DrugInteraction)
class DrugInteractionAdmin(admin.ModelAdmin):
    """약물 상호작용 관리자"""
    list_display = ['patient', 'drug_name', 'side_effect', 'risk_level', 'probability', 'created_at']
    list_filter = ['risk_level', 'created_at']
    search_fields = ['patient__name', 'patient__patient_id', 'drug_name', 'side_effect']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('환자 정보', {
            'fields': ('patient',)
        }),
        ('약물 정보', {
            'fields': ('drug_name', 'risk_level', 'side_effect', 'probability', 'color_code')
        }),
        ('조치 계획', {
            'fields': ('action_plan', 'monitoring')
        }),
    )

    ordering = ['-created_at']


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """환자 관리자 - 담당의 변경 및 CT 이미지 업로드 전용"""
    change_form_template = 'admin/django_1pj/patient/change_form.html'
    list_display = ['patient_id', 'name', 'birth_date', 'gender', 'bclc_stage', 'recurrence_risk', 'doctor', 'updated_at']
    list_filter = ['gender', 'bclc_stage', 'recurrence_risk', 'child_pugh', 'treatment_type', 'doctor']
    search_fields = ['patient_id', 'name', 'phone']
    date_hierarchy = 'diagnosis_date'
    readonly_fields = ['created_at', 'updated_at']

    def get_fieldsets(self, request, obj=None):
        """기존 환자는 담당의와 CT만, 새 환자는 전체 정보 입력"""
        if obj:  # 수정 (기존 환자)
            return (
                ('담당의 변경', {
                    'fields': ('doctor',),
                    'description': '담당의를 변경할 수 있습니다.'
                }),
                ('CT 이미지', {
                    'fields': ('ct_image',),
                    'description': 'CT 이미지를 업로드하거나 변경할 수 있습니다.'
                }),
                ('기본 정보 (읽기 전용)', {
                    'fields': ('patient_id', 'name', 'birth_date', 'gender', 'phone'),
                    'classes': ('collapse',),
                }),
                ('진단 정보 (읽기 전용)', {
                    'fields': ('diagnosis_date', 'bclc_stage', 'tumor_size', 'tumor_count', 'vascular_invasion', 'child_pugh'),
                    'classes': ('collapse',),
                }),
                ('시스템 정보', {
                    'fields': ('created_at', 'updated_at'),
                    'classes': ('collapse',),
                }),
            )
        else:  # 새로 추가
            return (
                ('기본 정보', {
                    'fields': ('patient_id', 'name', 'birth_date', 'gender', 'phone', 'doctor')
                }),
                ('진단 정보', {
                    'fields': ('diagnosis_date', 'bclc_stage', 'tumor_size', 'tumor_count', 'vascular_invasion')
                }),
                ('간기능', {
                    'fields': ('child_pugh',)
                }),
                ('바이오마커', {
                    'fields': ('afp_initial', 'afp_current')
                }),
                ('치료 정보', {
                    'fields': ('treatment_type', 'treatment_start_date')
                }),
                ('예후 정보', {
                    'fields': ('survival_1year', 'survival_3year', 'survival_5year', 'recurrence_risk')
                }),
                ('추적관찰', {
                    'fields': ('next_ct_date', 'next_blood_test_date')
                }),
                ('CT 이미지', {
                    'fields': ('ct_image',)
                }),
            )

    def get_readonly_fields(self, request, obj=None):
        """기존 환자 수정 시 환자 정보는 읽기 전용"""
        if obj:  # 수정 모드
            return self.readonly_fields + [
                'patient_id', 'name', 'birth_date', 'gender', 'phone',
                'diagnosis_date', 'bclc_stage', 'tumor_size', 'tumor_count',
                'vascular_invasion', 'child_pugh', 'afp_initial', 'afp_current',
                'treatment_type', 'treatment_start_date', 'survival_1year',
                'survival_3year', 'survival_5year', 'recurrence_risk',
                'next_ct_date', 'next_blood_test_date'
            ]
        return self.readonly_fields

    ordering = ['-updated_at']


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    """의사 프로필 관리자 - Superuser만 접근 가능"""
    form = DoctorProfileAdminForm
    list_display = ['doctor_id', 'doctor_name', 'doctor_sex', 'doctor_status', 'doctor_phone', 'doctor_email', 'last_login', 'created_at']
    list_filter = ['doctor_status', 'doctor_sex', 'created_at']
    search_fields = ['doctor_id', 'doctor_name', 'doctor_phone', 'doctor_email']
    date_hierarchy = 'created_at'
    readonly_fields = ['last_login', 'created_at']
    ordering = ['-created_at']

    def get_fieldsets(self, request, obj=None):
        """새로 추가할 때와 수정할 때 다른 필드셋 표시"""
        if obj:  # 수정
            return (
                ('로그인 정보', {
                    'fields': ('doctor_id', 'last_login', 'created_at'),
                    'description': '비밀번호를 변경하려면 아래 비밀번호 필드를 입력하세요.'
                }),
                ('비밀번호 변경 (선택사항)', {
                    'fields': ('password', 'password_confirm'),
                    'classes': ('collapse',),
                }),
                ('기본 정보', {
                    'fields': ('doctor_name', 'doctor_sex', 'doctor_phone', 'doctor_email')
                }),
                ('근무 정보', {
                    'fields': ('doctor_status', 'profile_image')
                }),
            )
        else:  # 새로 추가
            return (
                ('로그인 정보 (필수)', {
                    'fields': ('doctor_id', 'password', 'password_confirm')
                }),
                ('기본 정보', {
                    'fields': ('doctor_name', 'doctor_sex', 'doctor_phone', 'doctor_email')
                }),
                ('근무 정보', {
                    'fields': ('doctor_status', 'profile_image')
                }),
            )