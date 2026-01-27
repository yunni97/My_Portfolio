from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django_1pj.urls')),
]

# 관리자 사이트 커스터마이징
admin.site.site_header = "CDSS 관리자"
admin.site.site_title = "간암 예후관리 시스템"
admin.site.index_title = "환영합니다"