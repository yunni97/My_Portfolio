"""
DDI API URLs
"""
from django.urls import path
from .views import (
    HomeView,
    DDIAnalysisView,
    DrugSearchView,
    HealthCheckView
)

app_name = 'ddi_api'

urlpatterns = [
    # 웹 UI
    path('', HomeView.as_view(), name='home'),

    # API 엔드포인트
    path('api/analyze/', DDIAnalysisView.as_view(), name='analyze'),
    path('api/drugs/search/', DrugSearchView.as_view(), name='drug_search'),
    path('api/health/', HealthCheckView.as_view(), name='health'),
]
