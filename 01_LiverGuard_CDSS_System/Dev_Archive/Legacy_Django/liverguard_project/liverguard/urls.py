from django.urls import path
from . import views

app_name = 'liverguard'

urlpatterns = [
    # 의사 로그인/로그아웃
    path('login/', views.doctor_login_view, name='doctor_login'),
    path('logout/', views.doctor_logout_view, name='doctor_logout'),

    # 홈 페이지
    path('', views.home, name='home'),

    # 환자 관련
    path('patients/', views.patient_list, name='patient_list'),
    path('patients/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patients/add/', views.patient_add, name='patient_add'),

    # 진료기록 관련
    path('records/', views.record_list, name='record_list'),
    path('records/<int:record_id>/', views.record_detail, name='record_detail'),
    path('records/add/', views.record_add, name='record_add'),

    # 처방 관련
    path('prescriptions/', views.prescription_list, name='prescription_list'),
    path('prescriptions/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),

    # 약물 검색
    path('drugs/', views.drug_list, name='drug_list'),
    path('drugs/<int:drug_id>/', views.drug_detail, name='drug_detail'),
]
