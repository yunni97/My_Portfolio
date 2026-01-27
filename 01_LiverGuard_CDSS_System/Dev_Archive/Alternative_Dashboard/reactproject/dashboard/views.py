# liverguard/views.py

from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
# ✍️ (1/3) 'viewsets' 추가
from rest_framework import generics, viewsets, status, permissions, filters
from .models import (
    DbrPatients, DbrBloodResults, DbrAppointments, DbrBloodTestReferences,
    Medication, MedicationLog,
    # ✍️ (2/3) DUR 모델 2개 추가
    DurDrugInfo, DurDdiDrugbank,DurDrugMapping 
)
from .serializers import (
    PatientSerializer, BloodResultSerializer, AppointmentSerializer,
    BloodTestReferenceSerializer,
    DbrPatientRegisterSerializer, DbrPatientLoginSerializer,
    MedicationSerializer, MedicationLogSerializer,
    # ✍️ (3/3) DDI 검사용 Serializer 추가
    MedicationCreateUpdateSerializer,
    DurDrugInfoSearchSerializer
)
from dashboard.authentication import PatientJWTAuthentication
from django.contrib.auth import authenticate, login
from rest_framework.decorators import api_view
from django.contrib.auth.hashers import check_password
from rest_framework.permissions import AllowAny, IsAuthenticated # 👈 IsAuthenticated 이미 있음
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication

from flask_services.survival_service import predict_survival_from_flask

# =========================== Auth view ===========================
# sign up view
class DbrPatientRegisterView(APIView):
    permission_classes = [AllowAny] 
    authentication_classes = []

    @swagger_auto_schema(
        operation_description="환자 회원가입 API",
        operation_summary="회원가입",
        tags=["Auth"],
        request_body=DbrPatientRegisterSerializer,
        responses={
            201: openapi.Response(
                description="회원가입 성공",
                examples={
                    "application/json": {
                        "message": "회원가입이 완료되었습니다."
                    }
                }
            ),
            400: openapi.Response(
                description="입력 데이터 오류",
                examples={
                    "application/json": {
                        "password": ["비밀번호가 일치하지 않습니다."]
                    }
                }
            )
        }
    )
    def post(self, request):
        serializer = DbrPatientRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "회원가입이 완료되었습니다."}, status=status.HTTP_201_CREATED)
        else:
            print("[ERROR] Serializer errors:", serializer.errors)  # [FIRE] 여기에 실제 원인 표시
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# login view
class DbrPatientLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @swagger_auto_schema(
        operation_description="환자 로그인 API - JWT 토큰 발급",
        operation_summary="로그인",
        tags=["Auth"],
        request_body=DbrPatientLoginSerializer,
        responses={
            200: openapi.Response(
                description="로그인 성공",
                examples={
                    "application/json": {
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                        "user": {
                            "user_id": "patient123",
                            "name": "홍길동",
                            "sex": "M",
                            "phone": "010-1234-5678"
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="로그인 실패",
                examples={
                    "application/json": {
                        "user_id": ["존재하지 않는 사용자입니다."],
                        "password": ["비밀번호가 올바르지 않습니다."]
                    }
                }
            ),
        },
    )
    def post(self, request):
        serializer = DbrPatientLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]

            # [OK] JWT 발급 로직은 View에서 처리
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            
            response_data = {
                "access": str(access),
                "refresh": str(refresh),
                "user": {
                    "patient_id": user.patient_id,
                    "user_id": user.user_id,
                    "name": user.name,
                    "sex": user.sex,
                    "phone": user.phone,
                },
            }
            print(f"[DEBUG] Response user data: {response_data['user']}")

            return Response(response_data, status=status.HTTP_200_OK)

        # [ERROR] 로그인 실패
        print("[ERROR] Login errors:", serializer.errors)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# logout view
class DbrPatientLogoutView(APIView):
    """
    JWT 로그아웃 (Refresh Token 무효화)
    """
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="환자 로그아웃 API - Refresh Token 무효화",
        operation_summary="로그아웃",
        tags=["Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT, # 👈 (수정) type 추가
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh Token")
            }
        ),
        responses={
            205: openapi.Response(
                description="로그아웃 성공",
                examples={
                    "application/json": {
                        "message": "로그아웃되었습니다."
                    }
                }
            ),
            400: openapi.Response(
                description="로그아웃 실패",
                examples={
                    "application/json": {
                        "error": "refresh token이 필요합니다."
                    }
                }
            ),
            401: openapi.Response(description="인증 실패")
        },
        security=[{"Bearer": []}]
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"error": "refresh token이 필요합니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            # token.blacklist()  # [OK] 블랙리스트에 등록 (재사용 불가)

            return Response(
                {"message": "로그아웃되었습니다."},
                status=status.HTTP_205_RESET_CONTENT
            )
        except TokenError:
            return Response(
                {"error": "유효하지 않은 refresh token입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
    
# 🔹 현재 로그인된 사용자 조회 (auth/user)
class DbrPatientUserView(APIView):
    authentication_classes = [PatientJWTAuthentication]  # [OK] 커스텀 인증
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="현재 로그인된 사용자 정보 조회",
        operation_summary="사용자 정보 조회",
        tags=["Auth"],
        responses={
            200: openapi.Response(
                description="사용자 정보 조회 성공",
                examples={
                    "application/json": {
                        "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "patient123",
                        "name": "홍길동",
                        "sex": "M",
                        "phone": "010-1234-5678"
                    }
                }
            ),
            401: openapi.Response(description="인증 실패")
        },
        security=[{"Bearer": []}]
    )
    def get(self, request):
        user = request.user
        return Response({
            "patient_id": str(user.patient_id),
            "user_id": user.user_id,
            "name": user.name,
            "birth_date": user.birth_date,
            "sex": user.sex,
            "height": user.height,
            "weight": user.weight,
        })

# access token 재발급 view
class DbrPatientTokenRefreshView(APIView):
    """
    JWT Refresh API
    - refresh token으로 access token 재발급
    """
    permission_classes = [AllowAny]
    authentication_classes = [] 

    @swagger_auto_schema(
        operation_description="access token 만료 시 refresh token으로 새로운 access token 발급",
        operation_summary="토큰 재발급 (refresh)",
        tags=["Auth"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["refresh"],
            properties={
                "refresh": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Refresh Token"
                ),
            },
        ),
        responses={
            200: openapi.Response(
                description="새로운 access token 발급 성공",
                examples={
                    "application/json": {
                        "access": "new_access_token_string"
                    }
                }
            ),
            400: openapi.Response(
                description="토큰 만료 또는 유효하지 않음",
                examples={"application/json": {"error": "유효하지 않은 refresh token"}},
            ),
        },
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"error": "refresh token이 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # 새 access token 발급
            token = RefreshToken(refresh_token)
            new_access = str(token.access_token)
            return Response({"access": new_access}, status=status.HTTP_200_OK)
        except TokenError:
            return Response(
                {"error": "유효하지 않은 refresh token입니다."},
                status=status.HTTP_400_BAD_REQUEST
            )



# ==================== 환자 관련 Views ====================
class PatientListView(generics.ListCreateAPIView):
    """환자 목록 조회 및 생성"""
    queryset = DbrPatients.objects.all()
    serializer_class = PatientSerializer

    @swagger_auto_schema(tags=["Patients"], operation_summary="환자 목록 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Patients"], operation_summary="환자 등록")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """환자 상세 조회, 수정, 삭제"""
    queryset = DbrPatients.objects.all()
    serializer_class = PatientSerializer
    lookup_field = 'patient_id'
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Patients"], operation_summary="환자 상세 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Patients"], operation_summary="환자 정보 수정")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Patients"], operation_summary="환자 정보 부분 수정")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Patients"], operation_summary="환자 삭제")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ==================== 혈액검사 관련 Views ====================
class BloodResultListView(generics.ListCreateAPIView):
    """혈액검사 결과 목록 조회 및 생성"""
    serializer_class = BloodResultSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """로그인한 환자의 혈액검사 결과만 반환"""
        return DbrBloodResults.objects.filter(
            patient_id=self.request.user.patient_id
        ).select_related('patient_id').order_by('-taken_at')

    @swagger_auto_schema(tags=["Blood Results"], operation_summary="혈액검사 결과 목록 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Results"], operation_summary="혈액검사 결과 등록")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BloodResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    """혈액검사 결과 상세 조회, 수정, 삭제"""
    queryset = DbrBloodResults.objects.all().select_related('patient_id')
    serializer_class = BloodResultSerializer
    lookup_field = 'blood_result_id'
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Blood Results"], operation_summary="혈액검사 결과 상세 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Results"], operation_summary="혈액검사 결과 수정")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Results"], operation_summary="혈액검사 결과 부분 수정")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Results"], operation_summary="혈액검사 결과 삭제")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


class LatestBloodResultView(APIView):
    """최신 혈액검사 결과 조회"""
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["Blood Results"],
        operation_summary="최신 혈액검사 결과 조회",
        responses={
            200: BloodResultSerializer(),
            404: "혈액검사 결과가 없습니다"
        }
    )
    def get(self, request):
        user_id = request.user.user_id
        latest_result = DbrBloodResults.objects.filter(
            patient_id__user_id=user_id
        ).select_related('patient_id').order_by('-taken_at').first()

        if not latest_result:
            return Response(
                {"detail": "혈액검사 결과가 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BloodResultSerializer(latest_result)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ==================== 일정 관련 Views ====================
class AppointmentListView(generics.ListCreateAPIView):
    """일정 목록 조회 및 생성"""
    serializer_class = AppointmentSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """로그인한 환자의 일정만 반환"""
        return DbrAppointments.objects.filter(
            patient_id=self.request.user.patient_id
        ).select_related('patient_id').order_by('appointment_date', 'appointment_time')

    @swagger_auto_schema(tags=["Appointments"], operation_summary="일정 목록 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Appointments"], operation_summary="일정 등록")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """일정 상세 조회, 수정, 삭제"""
    queryset = DbrAppointments.objects.all().select_related('patient_id')
    serializer_class = AppointmentSerializer
    lookup_field = 'appointment_id'
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Appointments"], operation_summary="일정 상세 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Appointments"], operation_summary="일정 수정")
    def put(self, request, *args, **kwargs):
        print(f"[DEBUG] PUT Request Data: {request.data}")
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        if not serializer.is_valid():
            print(f"[ERROR] Serializer Errors: {serializer.errors}")
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Appointments"], operation_summary="일정 부분 수정")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Appointments"], operation_summary="일정 삭제")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ==================== 혈액검사 기준 관련 Views ====================
class BloodTestReferenceListView(generics.ListCreateAPIView):
    """혈액검사 기준 목록 조회 및 생성"""
    queryset = DbrBloodTestReferences.objects.all()
    serializer_class = BloodTestReferenceSerializer
    permission_classes = [AllowAny]  # 인증 없이 접근 가능
    authentication_classes = []  # 인증 클래스 비활성화

    @swagger_auto_schema(tags=["Blood Test References"], operation_summary="혈액검사 기준 목록 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Test References"], operation_summary="혈액검사 기준 등록")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class BloodTestReferenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """혈액검사 기준 상세 조회, 수정, 삭제"""
    queryset = DbrBloodTestReferences.objects.all()
    serializer_class = BloodTestReferenceSerializer
    lookup_field = 'reference_id'

    @swagger_auto_schema(tags=["Blood Test References"], operation_summary="혈액검사 기준 상세 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Test References"], operation_summary="혈액검사 기준 수정")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Test References"], operation_summary="혈액검사 기준 부분 수정")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Blood Test References"], operation_summary="혈액검사 기준 삭제")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)


# ==================== Dashboard Graph Views ====================
from .dashboard_bar import generate_risk_bar
from django.http import JsonResponse
from django.core.cache import cache
import hashlib

class DashboardGraphsView(APIView):
    """
    현재 로그인한 환자의 최신 혈액검사 결과로 4개의 그래프 생성
    """
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="혈액검사 결과 그래프 조회 (핵심 지표)",
        operation_summary="혈액검사 그래프",
        tags=["Dashboard"],
        responses={
            200: openapi.Response(
                description="그래프 생성 성공",
                examples={
                    "application/json": {
                        "patient_name": "홍길동",
                        "test_date": "2025-01-15",
                        "graphs": {
                            "afp": "data:image/png;base64,...",
                            "ast": "data:image/png;base64,...",
                            "alt": "data:image/png;base64,...",
                            "albi_grade": "data:image/png;base64,...",
                            "ggt": "data:image/png;base64,...",
                            "bilirubin": "data:image/png;base64,..."
                        }
                    }
                }
            ),
            404: "혈액검사 결과 없음"
        },
        security=[{"Bearer": []}]
    )
    def get(self, request):
        try:
            patient = request.user

            # 최신 혈액검사 결과
            latest_result = DbrBloodResults.objects.filter(
                patient=patient
            ).order_by('-taken_at').first()

            if not latest_result:
                return Response(
                    {"error": "혈액검사 결과가 없습니다."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 캐시 키
            cache_key = f"graphs_v3_{patient.patient_id}_{latest_result.blood_result_id}"
            
            # 캐시 확인
            cached_graphs = cache.get(cache_key)
            if cached_graphs:
                return Response(cached_graphs, status=status.HTTP_200_OK)

            # [FIRE] 핵심 지표 우선순위 (중요한 순서대로)
            primary_indicators = [
                'afp',       # 1. 종양 표지자
                'ast',       # 2. 간세포 손상
                'alt',       # 3. 간세포 손상
                'albi_grade',  # 4. 간 기능 종합
            ]
            
            secondary_indicators = [
                'ggt',       # 5. 담도/알코올
                'r_gtp',     # 6. 알코올
                'bilirubin', # 7. 황달
                'albumin',   # 8. 간 합성
            ]

            graphs = {
                'primary': {},    # 핵심 지표
                'secondary': {},  # 부가 지표
            }
            
            gender = patient.sex

            # [FIRE] 핵심 지표 그래프 생성
            for indicator in primary_indicators:
                value = getattr(latest_result, indicator, None)
                
                if value is None:
                    graphs['primary'][indicator] = None
                else:
                    try:
                        img_base64 = generate_risk_bar(indicator, float(value), gender)
                        graphs['primary'][indicator] = f"data:image/png;base64,{img_base64}"
                    except Exception as e:
                        print(f"[ERROR] Error generating {indicator} graph: {e}")
                        graphs['primary'][indicator] = None

            # 📊 부가 지표 그래프 생성
            for indicator in secondary_indicators:
                value = getattr(latest_result, indicator, None)
                
                if value is None:
                    graphs['secondary'][indicator] = None
                else:
                    try:
                        img_base64 = generate_risk_bar(indicator, float(value), gender)
                        graphs['secondary'][indicator] = f"data:image/png;base64,{img_base64}"
                    except Exception as e:
                        print(f"[ERROR] Error generating {indicator} graph: {e}")
                        graphs['secondary'][indicator] = None

            # 📊 수치 요약
            summary = {
                'afp': {
                    'value': float(latest_result.afp) if latest_result.afp else None,
                    'status': self._get_afp_status(latest_result.afp),
                    'importance': 'critical'
                },
                'ast': {
                    'value': float(latest_result.ast) if latest_result.ast else None,
                    'status': self._get_ast_status(latest_result.ast, gender),
                    'importance': 'high'
                },
                'alt': {
                    'value': float(latest_result.alt) if latest_result.alt else None,
                    'status': self._get_alt_status(latest_result.alt, gender),
                    'importance': 'high'
                },
                'albi': {
                    'score': float(latest_result.albi) if latest_result.albi else None,
                    'grade': latest_result.albi_grade,
                    'status': latest_result.risk_level,
                    'importance': 'high'
                }
            }

            response_data = {
                "patient_name": patient.name,
                "test_date": latest_result.taken_at,
                "gender": gender,
                "graphs": graphs,
                "summary": summary,
                "message": "핵심 간 검사 지표 위주로 표시됩니다."
            }

            # 캐시 저장 (1시간)
            cache.set(cache_key, response_data, 3600)

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # 헬퍼 메서드
    def _get_afp_status(self, afp):
        if not afp:
            return None
        afp = float(afp)
        if afp <= 10:
            return 'safe'
        elif afp <= 100:
            return 'warning'
        elif afp <= 400:
            return 'danger'
        else:
            return 'critical'
    
    def _get_ast_status(self, ast, gender):
        if not ast:
            return None
        ast = float(ast)
        threshold = 40 if gender == 'male' else 32
        if ast <= threshold:
            return 'safe'
        elif ast <= threshold + 10:
            return 'warning'
        else:
            return 'danger'
    
    def _get_alt_status(self, alt, gender):
        if not alt:
            return None
        alt = float(alt)
        threshold = 40 if gender == 'male' else 35
        if alt <= threshold:
            return 'safe'
        elif alt <= threshold + 10:
            return 'warning'
        else:
            return 'danger'

    # ( ... 주석 처리된 옛날 get 메서드 ...)
            
# ==========================================
# 혈액검사 분석 API 추가
# ==========================================
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def blood_result_analysis(request, blood_result_id):
    """
    혈액검사 결과 분석 API
    GET /api/dashboard/blood-results/{id}/analysis/
    """
    try:
        result = DbrBloodResults.objects.get(blood_result_id=blood_result_id)
        
        analysis = {
            'record_id': result.blood_result_id,
            'taken_at': result.taken_at,
            'patient_name': result.patient_id.name,
            'albi_score': float(result.albi) if result.albi else None,
            'albi_grade': result.albi_grade,
            'risk_level': result.risk_level,
            'recommendations': []
        }
        
        # AFP 분석
        if result.afp:
            afp = float(result.afp)
            if afp > 400:
                analysis['recommendations'].append({
                    'priority': 'critical',
                    'title': 'AFP 매우 높음',
                    'description': f'AFP {afp} ng/mL - 즉시 병원 방문 필요'
                })
            elif afp > 100:
                analysis['recommendations'].append({
                    'priority': 'high',
                    'title': 'AFP 높음',
                    'description': f'AFP {afp} ng/mL - 간암 의심'
                })
        
        # AST/ALT 비교
        if result.ast and result.alt:
            ast, alt = float(result.ast), float(result.alt)
            if ast > alt:
                analysis['recommendations'].append({
                    'priority': 'high',
                    'title': 'AST > ALT',
                    'description': '알코올성 간손상 가능성'
                })
        
        return Response(analysis)
    
    except DbrBloodResults.DoesNotExist:
        return Response(
            {'error': '검사 결과를 찾을 수 없습니다.'}, 
            status=404
        )

from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class DashboardTimeSeriesView(APIView):
    """
    시계열 전체 분석 API
    """
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            patient = request.user
            
            # 모든 혈액검사 결과
            blood_results = DbrBloodResults.objects.filter(
                patient=patient
            ).order_by('taken_at')

            if not blood_results.exists():
                return Response(
                    {"error": "검사 데이터가 없습니다."},
                    status=status.HTTP_404_NOT_FOUND
                )
                
            actual_count = blood_results.count()
            print(f"🔍 Total blood results count: {actual_count}")
            
            # 최신 검사 결과로 경고 상태 판단
            latest_result = blood_results.last()
            warning_status = self._analyze_warning_status(latest_result, patient.sex)

            # 시계열 그래프 생성
            time_series_graphs = self._generate_time_series_graphs(blood_results, patient.sex)

            first_result = blood_results.first()
            last_result = blood_results.last()
            
            start_date = first_result.taken_at
            end_date = last_result.taken_at
            
            # datetime 객체면 문자열로 변환
            if isinstance(start_date, datetime):
                start_date = start_date.strftime('%Y-%m-%d')
            if isinstance(end_date, datetime):
                end_date = end_date.strftime('%Y-%m-%d')

            response_data = {
                "patient_name": patient.name,
                "start_date": start_date,
                "end_date": end_date,
                "total_tests": actual_count, 
                "time_series_graphs": time_series_graphs,
                "warning_status": warning_status,
            }
            
            print(f"Response data total_tests: {response_data['total_tests']}")
            print(f"Warning status: {warning_status}")

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"DashboardTimeSeriesView error: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _generate_time_series_graphs(self, blood_results, gender='male'):
        """모든 필드의 시계열 그래프 생성"""
        graphs = {}
        
        # 필드 목록 (dashboard_bar.py의 INDICATORS와 동일)
        fields = [
            'afp', 'ast', 'alt', 'ggt', 'r_gtp', 'alp',
            'bilirubin', 'albumin', 'total_protein', 
            'platelet', 'pt', 'albi'
        ]
        
        for field in fields:
            try:
                # 데이터 추출
                dates = []
                values = []
                
                for result in blood_results:
                    value = getattr(result, field, None)
                    if value is not None and float(value) != 0:
                        dates.append(result.taken_at)
                        values.append(float(value))
                
                if not dates:
                    graphs[field] = None
                    print(f"No valid data for {field}") 
                    continue
                
                print(f"{field}: {len(dates)} data points")
                
                # 그래프 생성
                img_base64 = self._create_time_series_graph(
                    dates, 
                    values, 
                    field,
                    gender
                )
                graphs[field] = f"data:image/png;base64,{img_base64}"
                
            except Exception as e:
                print(f"Error generating {field} time series: {e}")
                graphs[field] = None
        
        return graphs
    
    def _create_time_series_graph(self, dates, values, field, gender='male'):
        """시계열 그래프 생성"""
        from .dashboard_bar import INDICATORS
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        import io
        import base64
        
        # 필드 설정
        config = INDICATORS.get(field, {
            'title': field.upper(),
            'unit': '',
            'vmin': min(values) * 0.9 if values else 0,
            'vmax': max(values) * 1.1 if values else 100,
        })
        
        title = config.get('title', field.upper())
        unit = config.get('unit', '')
        
        print(f"Generating graph for {field}:")
        print(f"   - Dates: {len(dates)}")
        print(f"   - Values: {len(values)}")
        
        # Figure 생성
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # 선 그래프
        ax.plot(dates, values, marker='o', linewidth=2, markersize=6, color='#3498db')
        
        # 정상 범위 표시 (있는 경우)
        if 'ranges' in config and len(config['ranges']) > 0:
            normal_range = config['ranges'][0]
            ax.axhspan(normal_range[0], normal_range[1], alpha=0.2, color='green', label='Normal Range')
    
        # 축 설정
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel(f'{title} ({unit})', fontsize=12)
        ax.set_title(f'{title} Trend', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 날짜 포맷
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        fig.autofmt_xdate()
        
        # 범례
        if 'ranges' in config:
            ax.legend(loc='upper right')
        
        # Base64 변환
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        
        print(f"Graph generated: {len(img_base64)} bytes")
        
        return img_base64
    
    
    def _analyze_warning_status(self, result, gender='male'):
        """
        최신 검사 결과로 각 지표의 경고 상태 판단
        """
        warnings = {}
        
        # AFP 분석
        if result.afp is not None:
            afp = float(result.afp)
            if afp >= 400:
                warnings['afp'] = {
                    'level': 'critical',
                    'value': afp,
                    'message': 'AFP가 매우 높습니다 (400 ng/mL 이상). 즉시 전문의 상담이 필요합니다.'
                }
            elif afp >= 100:
                warnings['afp'] = {
                    'level': 'danger',
                    'value': afp,
                    'message': 'AFP가 높습니다 (100 ng/mL 이상). 간암 의심 - 정밀 검사가 필요합니다.'
                }
            elif afp >= 10:
                warnings['afp'] = {
                    'level': 'warning',
                    'value': afp,
                    'message': 'AFP가 약간 높습니다 (10 ng/mL 이상). 추적 관찰이 필요합니다.'
                }
        
        # AST 분석
        if result.ast is not None:
            ast = float(result.ast)
            threshold = 40 if gender == 'male' else 32
            if ast >= 50:
                warnings['ast'] = {
                    'level': 'danger',
                    'value': ast,
                    'message': 'AST가 높습니다 (50 U/L 이상). 간세포 손상이 의심됩니다.'
                }
            elif ast >= threshold:
                warnings['ast'] = {
                    'level': 'warning',
                    'value': ast,
                    'message': f'AST가 경계선입니다 ({threshold} U/L 이상). 주의가 필요합니다.'
                }
        
        # ALT 분석
        if result.alt is not None:
            alt = float(result.alt)
            threshold = 40 if gender == 'male' else 35
            if alt >= 50:
                warnings['alt'] = {
                    'level': 'danger',
                    'value': alt,
                    'message': 'ALT가 높습니다 (50 U/L 이상). 간세포 손상이 의심됩니다.'
                }
            elif alt >= threshold:
                warnings['alt'] = {
                    'level': 'warning',
                    'value': alt,
                    'message': f'ALT가 경계선입니다 ({threshold} U/L 이상). 주의가 필요합니다.'
                }
        
        # GGT 분석
        if result.ggt is not None:
            ggt = float(result.ggt)
            threshold = 71 if gender == 'male' else 42
            if ggt >= 100:
                warnings['ggt'] = {
                    'level': 'danger',
                    'value': ggt,
                    'message': 'GGT가 높습니다 (100 U/L 이상). 담도 질환 또는 알코올성 간질환 의심.'
                }
            elif ggt >= threshold:
                warnings['ggt'] = {
                    'level': 'warning',
                    'value': ggt,
                    'message': f'GGT가 약간 높습니다 ({threshold} U/L 이상). 음주량 조절이 필요합니다.'
                }
        
        # r-GTP 분석
        if result.r_gtp is not None:
            r_gtp = float(result.r_gtp)
            threshold = 63 if gender == 'male' else 35
            if r_gtp >= 77:
                warnings['r_gtp'] = {
                    'level': 'danger',
                    'value': r_gtp,
                    'message': 'r-GTP가 높습니다 (77 U/L 이상). 알코올성 간손상 의심.'
                }
            elif r_gtp >= threshold:
                warnings['r_gtp'] = {
                    'level': 'warning',
                    'value': r_gtp,
                    'message': f'r-GTP가 약간 높습니다 ({threshold} U/L 이상). 음주량 조절이 필요합니다.'
                }
        
        # Bilirubin 분석
        if result.bilirubin is not None:
            bilirubin = float(result.bilirubin)
            if bilirubin >= 2.5:
                warnings['bilirubin'] = {
                    'level': 'danger',
                    'value': bilirubin,
                    'message': 'Bilirubin이 높습니다 (2.5 mg/dL 이상). 황달 증상 확인 필요.'
                }
            elif bilirubin >= 1.2:
                warnings['bilirubin'] = {
                    'level': 'warning',
                    'value': bilirubin,
                    'message': 'Bilirubin이 약간 높습니다 (1.2 mg/dL 이상). 추적 관찰이 필요합니다.'
                }
        
        # Albumin 분석 (낮을수록 위험)
        if result.albumin is not None:
            albumin = float(result.albumin)
            if albumin < 2.0:
                warnings['albumin'] = {
                    'level': 'critical',
                    'value': albumin,
                    'message': 'Albumin이 매우 낮습니다 (2.0 g/dL 미만). 즉시 전문의 상담이 필요합니다.'
                }
            elif albumin < 2.5:
                warnings['albumin'] = {
                    'level': 'danger',
                    'value': albumin,
                    'message': 'Albumin이 낮습니다 (2.5 g/dL 미만). 간 기능 저하가 의심됩니다.'
                }
            elif albumin < 3.5:
                warnings['albumin'] = {
                    'level': 'warning',
                    'value': albumin,
                    'message': 'Albumin이 약간 낮습니다 (3.5 g/dL 미만). 영양 상태 개선이 필요합니다.'
                }
        
        # ALP 분석
        if result.alp is not None:
            alp = float(result.alp)
            threshold = 120 if gender == 'male' else 104
            if alp >= 160:
                warnings['alp'] = {
                    'level': 'danger',
                    'value': alp,
                    'message': 'ALP가 높습니다 (160 U/L 이상). 담도 질환 의심.'
                }
            elif alp >= threshold:
                warnings['alp'] = {
                    'level': 'warning',
                    'value': alp,
                    'message': f'ALP가 약간 높습니다 ({threshold} U/L 이상). 추적 관찰이 필요합니다.'
                }
        
        # PT 분석
        if result.pt is not None:
            pt = float(result.pt)
            if pt >= 13:
                warnings['pt'] = {
                    'level': 'warning',
                    'value': pt,
                    'message': 'PT가 연장되었습니다 (13초 이상). 응고 기능 저하 의심.'
                }
        
        # Platelet 분석
        if result.platelet is not None:
            platelet = float(result.platelet)
            if platelet < 150:
                warnings['platelet'] = {
                    'level': 'warning',
                    'value': platelet,
                    'message': 'Platelet이 낮습니다 (150×10³/μL 미만). 간경화 또는 비장 비대 의심.'
                }
        
        return warnings

# ==================== 약물 관련 Views ====================
# ✍️ (제거) 기존 MedicationListView, MedicationDetailView 삭제

# ==========================================================
# 👈 [추가] 2. 약물 검색 API (Autocomplete용)
# ==========================================================
class DrugSearchAPIView(generics.ListAPIView):
    # ==========================================================
    # 👈 [수정] 검색할 테이블(queryset)을 DurDrugMapping으로 변경
    # ==========================================================
    # queryset = DurDrugMapping.objects.all() 
    serializer_class = DurDrugInfoSearchSerializer 
    
    filter_backends = [filters.SearchFilter]
    search_fields = ['KoreanName', 'EnglishName'] # 👈 여기는 OK
    
    permission_classes = [IsAuthenticated]
    authentication_classes = [PatientJWTAuthentication]
    
    # ==========================================================
    # 👈 [추가] get_queryset 메서드 (중복 제거)
    # ==========================================================
    def get_queryset(self):
        """
        검색 시 중복된 결과(row)를 제거합니다.
        """
        return DurDrugMapping.objects.all().distinct()

    @swagger_auto_schema(tags=["Medications"], operation_summary="[DDI검사] 약물 마스터 검색 (Autocomplete)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


# ✍️ (추가) MedicationViewSet (DDI 검사 기능 포함)
class MedicationViewSet(viewsets.ModelViewSet):
    """
    약물(Medication) CRUD API ViewSet
    - 로그인한 사용자의 약물만 조회, 생성, 수정, 삭제합니다.
    - 생성/수정 시 MedicationCreateUpdateSerializer를 사용하여 DDI 검사를 수행합니다.
    """
    queryset = Medication.objects.all().select_related('patient_id')
    permission_classes = [IsAuthenticated]
    authentication_classes = [PatientJWTAuthentication] # 👈 인증 클래스 명시

    @swagger_auto_schema(tags=["Medications"], operation_summary="[DDI검사] 약물 목록 조회")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medications"], operation_summary="[DDI검사] 약물 등록 (DDI 검사 수행)")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medications"], operation_summary="[DDI검사] 약물 상세 조회")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medications"], operation_summary="[DDI검사] 약물 정보 수정 (DDI 검사 수행)")
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medications"], operation_summary="[DDI검사] 약물 정보 부분 수정 (DDI 검사 수행)")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medications"], operation_summary="[DDI검사] 약물 삭제")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


    def get_serializer_class(self):
        """
        요청 종류(action)에 따라 다른 Serializer를 반환합니다.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return MedicationCreateUpdateSerializer # 👈 DDI 검사 Serializer
        return MedicationSerializer # 👈 단순 조회 Serializer

    def get_queryset(self):
        """
        로그인한 사용자(request.user) 본인의 약물 기록만 조회합니다.
        """
        # ✍️ (수정) patient_id가 request.user와 일치하는 것만 필터링
        return self.queryset.filter(patient_id=self.request.user)

    def perform_create(self, serializer):
        """
        새 약물 생성 시, patient_id를 로그인한 사용자로 강제 설정합니다.
        """
        serializer.save(patient_id=self.request.user)
    
    def perform_update(self, serializer):
        """
        약물 수정 시, patient_id를 로그인한 사용자로 강제 설정합니다.
        """
        serializer.save(patient_id=self.request.user)


# ( ... 기존 PatientMedicationsView 유지 ... )
class PatientMedicationsView(generics.ListAPIView):
    """특정 환자의 약물 목록 조회"""
    serializer_class = MedicationSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Medications"], operation_summary="특정 환자의 약물 목록 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        patient_id = self.kwargs['patient_id']
        return Medication.objects.filter(patient_id=patient_id, is_active=True).order_by('-start_date')


# ==================== 복용 기록 관련 Views ====================
class MedicationLogListView(generics.ListCreateAPIView):
    """복용 기록 목록 조회 및 생성"""
    queryset = MedicationLog.objects.all().select_related('medication__patient_id') # ✍️ patient -> patient_id
    serializer_class = MedicationLogSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Medication Logs"], operation_summary="복용 기록 목록 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medication Logs"], operation_summary="복용 기록 등록")
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class MedicationLogDetailView(generics.RetrieveUpdateDestroyAPIView):
    """복용 기록 상세 조회, 수정, 삭제"""
    queryset = MedicationLog.objects.all().select_related('medication__patient_id') # ✍️ patient -> patient_id
    serializer_class = MedicationLogSerializer
    lookup_field = 'log_id'
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=["Medication Logs"], operation_summary="복용 기록 상세 조회")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medication Logs"], operation_summary="복용 기록 수정")
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medication Logs"], operation_summary="복용 기록 부분 수정")
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(tags=["Medication Logs"], operation_summary="복용 기록 삭제")
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    



# # ==================== 의료기관 관련 Views ====================
# class MedicalFacilityListView(generics.ListCreateAPIView):
#     """의료기관 목록 조회 및 생성"""
#     queryset = MedicalFacility.objects.all()
#     serializer_class = MedicalFacilitySerializer
#     authentication_classes = [PatientJWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(tags=["Medical Facilities"], operation_summary="의료기관 목록 조회")
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)

#     @swagger_auto_schema(tags=["Medical Facilities"], operation_summary="의료기관 등록")
#     def post(self, request, *args, **kwargs):
#         return super().post(request, *args, **kwargs)


# class MedicalFacilityDetailView(generics.RetrieveUpdateDestroyAPIView):
#     """의료기관 상세 조회, 수정, 삭제"""
#     queryset = MedicalFacility.objects.all()
#     serializer_class = MedicalFacilitySerializer
#     lookup_field = 'facility_id'
#     authentication_classes = [PatientJWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(tags=["Medical Facilities"], operation_summary="의료기관 상세 조회")
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)

#     @swagger_auto_schema(tags=["Medical Facilities"], operation_summary="의료기관 정보 수정")
#     def put(self, request, *args, **kwargs):
#         return super().put(request, *args, **kwargs)

#     @swagger_auto_schema(tags=["Medical Facilities"], operation_summary="의료기관 정보 부분 수정")
#     def patch(self, request, *args, **kwargs):
#         return super().patch(request, *args, **kwargs)

#     @swagger_auto_schema(tags=["Medical Facilities"], operation_summary="의료기관 삭제")
#     def delete(self, request, *args, **kwargs):
#         return super().delete(request, *args, **kwargs)


# # ==================== 즐겨찾기 관련 Views ====================
# class FavoriteFacilityListView(generics.ListCreateAPIView):
#     """즐겨찾기 목록 조회 및 생성"""
#     queryset = FavoriteFacility.objects.all().select_related('patient', 'facility')
#     serializer_class = FavoriteFacilitySerializer
#     authentication_classes = [PatientJWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(tags=["Favorite Facilities"], operation_summary="즐겨찾기 목록 조회")
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)

#     @swagger_auto_schema(tags=["Favorite Facilities"], operation_summary="즐겨찾기 추가")
#     def post(self, request, *args, **kwargs):
#         return super().post(request, *args, **kwargs)


# class FavoriteFacilityDetailView(generics.RetrieveDestroyAPIView):
#     """즐겨찾기 상세 조회, 삭제"""
#     queryset = FavoriteFacility.objects.all().select_related('patient', 'facility')
#     serializer_class = FavoriteFacilitySerializer
#     lookup_field = 'favorite_id'
#     authentication_classes = [PatientJWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(tags=["Favorite Facilities"], operation_summary="즐겨찾기 상세 조회")
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)

#     @swagger_auto_schema(tags=["Favorite Facilities"], operation_summary="즐겨찾기 삭제")
#     def delete(self, request, *args, **kwargs):
#         return super().delete(request, *args, **kwargs)


# class PatientFavoriteFacilitiesView(generics.ListAPIView):
#     """특정 환자의 즐겨찾기 목록 조회"""
#     serializer_class = FavoriteFacilitySerializer
#     authentication_classes = [PatientJWTAuthentication]
#     permission_classes = [IsAuthenticated]

#     @swagger_auto_schema(tags=["Favorite Facilities"], operation_summary="특정 환자의 즐겨찾기 목록 조회")
#     def get(self, request, *args, **kwargs):
#         return super().get(request, *args, **kwargs)

#     def get_queryset(self):
#         patient_id = self.kwargs['patient_id']
#         return FavoriteFacility.objects.filter(patient_id=patient_id).select_related('facility')


# ----------------------- flask ai view -----------------------
class SurvivalPredictionAPIView(APIView):
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        """
        Client -> Django -> Flask -> Django -> Client
        """
        data = request.data

        payload = {
            "sex": data.get("sex"),
            "age_at_index": data.get("age_at_index"),
            "bmi": data.get("bmi"),
            "afp": data.get("afp"),
            "albumin": data.get("albumin"),
            "pt": data.get("pt"),
            "target_days": data.get("target_days", 1825),
        }

        flask_result = predict_survival_from_flask(payload)

        if "error" in flask_result:
            return Response(flask_result, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            "survival_probability": flask_result.get("survival_probability"),
            "target_day": flask_result.get("target_day"),
            "plot_base64": flask_result.get("plot_base64"),
        }, status=200)