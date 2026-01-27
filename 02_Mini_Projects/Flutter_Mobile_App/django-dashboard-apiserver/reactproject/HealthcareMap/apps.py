from django.apps import AppConfig


class HealthcaremapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'HealthcareMap'

    def ready(self):
        """앱이 준비될 때 signals를 import하여 등록"""
        # import HealthcareMap.signals  # 비활성화: csvTodb.py에서 직접 처리
