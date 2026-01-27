from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('patient/add/', views.patient_add_view, name='patient_add'),
    path('patient/<str:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('patient/<str:patient_id>/delete/', views.patient_delete_view, name='patient_delete'),

    # CDSS 관리자
    path('cdss-admin/', views.cdss_admin_view, name='cdss_admin'),
    path('cdss-admin/doctor/add/', views.cdss_admin_doctor_add_view, name='cdss_admin_doctor_add'),
    path('cdss-admin/doctor/<str:doctor_id>/delete/', views.cdss_admin_doctor_delete_view, name='cdss_admin_doctor_delete'),

    # DDI 분석
    path('ddi-analysis/', views.ddi_analysis_view, name='ddi_analysis'),
    path('api/ddi-analyze/', views.ddi_analyze_api, name='ddi_analyze_api'),
    path('api/ddi-drug-list/', views.ddi_drug_list_api, name='ddi_drug_list_api'),
]