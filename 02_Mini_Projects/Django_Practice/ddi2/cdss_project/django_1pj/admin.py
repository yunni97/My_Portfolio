from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import DoctorProfile, Patient, Announcement, Drug, DrugInteraction


class DoctorProfileInline(admin.StackedInline):
    """User 모델에 DoctorProfile을 인라인으로 추가"""
    model = DoctorProfile
    can_delete = False
    verbose_name = '의사 프로필'
    verbose_name_plural = '의사 프로필'
    fields = ('doctor_id', 'doctor_name', 'doctor_sex', 'doctor_phone', 'doctor_email', 'doctor_status', 'profile_image')


class UserAdmin(BaseUserAdmin):
    """확장된 User 관리자"""
    inlines = (DoctorProfileInline,)
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'get_doctor_name']
    
    def get_doctor_name(self, obj):
        try:
            return obj.doctorprofile.doctor_name
        except:
            return '-'
    get_doctor_name.short_description = '의사 이름'


# 기존 User 관리자를 해제하고 새로운 것으로 등록
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


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
    """환자 관리자"""
    list_display = ['patient_id', 'name', 'birth_date', 'gender', 'bclc_stage', 'recurrence_risk', 'doctor', 'updated_at']
    list_filter = ['gender', 'bclc_stage', 'recurrence_risk', 'child_pugh', 'treatment_type']
    search_fields = ['patient_id', 'name', 'phone']
    date_hierarchy = 'diagnosis_date'

    fieldsets = (
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
        ('의료 이미지', {
            'fields': ('ct_image',)
        }),
    )

    ordering = ['-updated_at']