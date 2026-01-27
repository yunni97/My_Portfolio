"""
의사 전용 커스텀 인증 백엔드
doctor_id와 password로 인증
"""
from django.utils import timezone
from .models import DoctorProfile


class DoctorAuthenticationBackend:
    """의사ID 기반 인증 백엔드"""

    def authenticate(self, request, doctor_id=None, password=None):
        """
        doctor_id와 password로 의사 인증
        """
        if doctor_id is None or password is None:
            return None

        try:
            doctor = DoctorProfile.objects.get(doctor_id=doctor_id)
            if doctor.check_password(password):
                # 마지막 로그인 시간 업데이트
                doctor.last_login = timezone.now()
                doctor.save(update_fields=['last_login'])
                return doctor
        except DoctorProfile.DoesNotExist:
            return None

        return None

    def get_user(self, doctor_id):
        """
        doctor_id로 의사 객체 반환
        """
        try:
            return DoctorProfile.objects.get(pk=doctor_id)
        except DoctorProfile.DoesNotExist:
            return None
