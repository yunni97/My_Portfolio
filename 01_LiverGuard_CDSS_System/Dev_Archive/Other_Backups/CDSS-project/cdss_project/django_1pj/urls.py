from django.urls import path
from . import views

urlpatterns = [
    # 의사 로그인 (기본 URL)
    path('', views.doctor_login_view, name='doctor_login'),
    path('logout/', views.doctor_logout_view, name='doctor_logout'),

    # 의사 홈 및 환자 관리
    path('home/', views.home_view, name='home'),
    path('doctor/status/change/', views.doctor_status_change_view, name='doctor_status_change'),
    path('patient/add/', views.patient_add_view, name='patient_add'),
    path('patient/<str:patient_id>/', views.patient_detail_view, name='patient_detail'),
    path('patient/<str:patient_id>/edit/', views.patient_edit_view, name='patient_edit'),
    path('patient/<str:patient_id>/delete/', views.patient_delete_view, name='patient_delete'),
]