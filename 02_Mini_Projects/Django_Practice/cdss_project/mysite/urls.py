from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('django_1pj.urls')),
]

# 개발 환경에서 media 파일 서빙
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 관리자 사이트 커스터마이징
admin.site.site_header = "CDSS 관리자"
admin.site.site_title = "간암 예후관리 시스템"
admin.site.index_title = "환영합니다"