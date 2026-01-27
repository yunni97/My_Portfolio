# dashboard/authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from dashboard.models import DbrPatients

class PatientJWTAuthentication(JWTAuthentication):
    """
    DbrPatients 모델 기반으로 동작하는 커스텀 JWT 인증 클래스
    (기본 User 모델이 아닌 환자 전용 JWT 검증용)
    """
    def get_user(self, validated_token):
        try:
            patient_id = validated_token.get("patient_id")
            user = DbrPatients.objects.get(patient_id=patient_id)
            return user

        except DbrPatients.DoesNotExist:
            print("[DEBUG] DbrPatients.DoesNotExist")
            return None
        except Exception as e:
            print("[DEBUG] Unexpected error in get_user:", e)
            return None