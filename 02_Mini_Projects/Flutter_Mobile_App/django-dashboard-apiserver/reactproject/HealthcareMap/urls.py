from django.urls import path
from .views import (
    HealthcareSearchView,
    DepartmentListView,
    FavoriteHospitalListCreateView,
    FavoriteHospitalDetailView,
    FavoriteClinicListCreateView,
    FavoriteClinicDetailView,
)

urlpatterns = [
    # 병원/의원/약국 통합 검색 (좌표 기반)
    path('search/', HealthcareSearchView.as_view(), name='healthcare-search'),
    
    # 진료과목 목록 (필터용)
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('favorites/hospitals/', FavoriteHospitalListCreateView.as_view(), name='favorite-hospital-list'),
    path('favorites/hospitals/<int:pk>/', FavoriteHospitalDetailView.as_view(), name='favorite-hospital-detail'),
    path('favorites/clinics/', FavoriteClinicListCreateView.as_view(), name='favorite-clinic-list'),
    path('favorites/clinics/<int:pk>/', FavoriteClinicDetailView.as_view(), name='favorite-clinic-detail'),
]
