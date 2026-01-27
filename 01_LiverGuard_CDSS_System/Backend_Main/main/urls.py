from django.urls import path
from . import views

urlpatterns = [
    # 인증
    path('auth/login/', views.login, name='login'),
    path('auth/nurse-login/', views.nurse_login, name='nurse_login'),

    # 대시보드
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),

    # 환자 관리
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/delete/', views.patient_delete, name='patient_delete'),
    path('patients/create/', views.patient_create, name='patient_create'),
    path('patients/<int:patient_id>/update/', views.patient_update, name='patient_update'),

    # 진료 기록
    path('medical-records/<int:patient_id>/', views.medical_record, name='medical_record'),

    # 임상 기록
    path('patients/<int:patient_id>/clinical/', views.manage_clinical_data, name='manage_clinical_data'),

    # 유전체 기록
    path('patients/<int:patient_id>/genomic/', views.manage_genomic_data, name='manage_genomic_data'),

    # AI 예측
    path('ai-predictions/', views.ai_predictions, name='ai_predictions'),

    # DICOM 관련 (API 접두사 추가)
    path('dicom-studies/', views.dicom_studies, name='dicom_studies'),
    path('dicom-series/', views.dicom_series, name='dicom_series'),
    path('dicom-upload/', views.dicom_upload, name='dicom_upload'),
    path('dicom-upload-folder/', views.dicom_folder_upload, name='dicom_folder_upload'),
    path('patients/<int:patient_id>/ai-results/', views.get_patient_ai_results, name='patient_ai_results'),

    # 의사 프로필
    path('doctors/<int:doctor_id>/profile/', views.doctor_profile, name='doctor_profile'),
    path('doctors/<int:doctor_id>/change-password/', views.change_password, name='change_password'),
    path('doctors/<int:doctor_id>/available-slots/', views.available_slots, name='available_slots'),

    # 간호사 프로필
    path('nurses/<int:nurse_id>/profile/', views.nurse_profile, name='nurse_profile'),
    path('nurses/<int:nurse_id>/change-password/', views.nurse_change_password, name='nurse_change_password'),

    # 예약 관리
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),

    # BentoML 세그멘테이션 API
    path('segment/', views.segment_ct, name='segment_ct'),
    path('segment/existing/', views.segment_existing_file, name='segment_existing'),
    path('bentoml/status/', views.check_bentoml_status, name='bentoml_status'),
    
    
    path('pacs/webhook/', views.OrthancWebhookView.as_view(), name='orthanc_webhook'),
]