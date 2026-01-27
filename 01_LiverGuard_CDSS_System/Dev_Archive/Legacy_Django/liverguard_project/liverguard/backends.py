"""
의사 전용 커스텀 인증 백엔드
doctor_id와 password로 인증
"""
from django.utils import timezone
from .models import DoctorProfiles


class DoctorAuthenticationBackend:
    """의사ID 기반 인증 백엔드"""

    def authenticate(self, request, doctor_id=None, password=None):
        """
        doctor_id와 password로 의사 인증
        """
        if doctor_id is None or password is None:
            return None

        try:
            doctor = DoctorProfiles.objects.get(doctor_id=doctor_id)
            # 비밀번호 확인
            if doctor.check_password(password):
                return doctor
        except DoctorProfiles.DoesNotExist:
            return None

        return None

    def get_user(self, doctor_id):
        """
        doctor_id로 의사 객체 반환
        """
        try:
            return DoctorProfiles.objects.get(pk=doctor_id)
        except DoctorProfiles.DoesNotExist:
            return None
