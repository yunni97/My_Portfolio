from rest_framework import generics, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, F, FloatField, Value
from django.db.models.functions import Cast, Power
from decimal import Decimal, InvalidOperation
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from .models import (
    Hospital,
    Clinic,
    Pharmacy,
    DepartmentOfTreatment,
    FavoriteHospital,
    FavoriteClinic,
)
from dashboard.models import DbrPatients
from dashboard.authentication import PatientJWTAuthentication
from .serializers import (
    HospitalLiteSerializer, ClinicLiteSerializer, PharmacyLiteSerializer,
    DepartmentOfTreatmentSerializer,
    FavoriteHospitalSerializer,
    FavoriteClinicSerializer,
)


class DepartmentListView(generics.ListAPIView):
    """진료과목 목록 조회"""
    queryset = DepartmentOfTreatment.objects.all()
    serializer_class = DepartmentOfTreatmentSerializer
    permission_classes = [AllowAny]
    authentication_classes = []

class HealthcareSearchView(APIView):
    """병원/의원/약국 통합 검색 - 지도 마커용 (최적화)"""
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def get(self, request):
        search_query = request.query_params.get('q', '')
        facility_type = request.query_params.get('type', 'all')  # all, hospital, clinic, pharmacy
        department_code = request.query_params.get('department', None)

        # 좌표 범위 검색 (지도 경계 내만 검색) - Decimal로 변환
        try:
            min_x = Decimal(request.query_params.get('min_x')) if request.query_params.get('min_x') else None
            max_x = Decimal(request.query_params.get('max_x')) if request.query_params.get('max_x') else None
            min_y = Decimal(request.query_params.get('min_y')) if request.query_params.get('min_y') else None
            max_y = Decimal(request.query_params.get('max_y')) if request.query_params.get('max_y') else None
            center_x = Decimal(request.query_params.get('center_x')) if request.query_params.get('center_x') else None
            center_y = Decimal(request.query_params.get('center_y')) if request.query_params.get('center_y') else None
        except (InvalidOperation, ValueError):
            return Response({'error': '잘못된 좌표 형식입니다.'}, status=400)

        results = {}

        def order_by_distance(qs):
            if center_x is not None and center_y is not None:
                center_x_value = float(center_x)
                center_y_value = float(center_y)
                distance_expr = (
                    Power(
                        Cast(F('coordinate_x'), output_field=FloatField()) -
                        Value(center_x_value, output_field=FloatField()),
                        2,
                    ) +
                    Power(
                        Cast(F('coordinate_y'), output_field=FloatField()) -
                        Value(center_y_value, output_field=FloatField()),
                        2,
                    )
                )
                return qs.annotate(distance=distance_expr).order_by('distance')
            return qs.order_by('id')

        # 병원 검색
        if facility_type in ['all', 'hospital']:
            hospital_qs = Hospital.objects.filter(
                coordinate_x__isnull=False,
                coordinate_y__isnull=False
            )

            if search_query:
                hospital_qs = hospital_qs.filter(
                    Q(name__icontains=search_query) |
                    Q(address__icontains=search_query)
                )

            if department_code:
                hospital_qs = hospital_qs.filter(departments__code=department_code)

            if all([min_x, max_x, min_y, max_y]):
                hospital_qs = hospital_qs.filter(
                    coordinate_x__gte=min_x,
                    coordinate_x__lte=max_x,
                    coordinate_y__gte=min_y,
                    coordinate_y__lte=max_y
                )

            hospital_qs = order_by_distance(hospital_qs)
            results['hospitals'] = HospitalLiteSerializer(
                hospital_qs.distinct()[:100], many=True
            ).data

        # 의원 검색
        if facility_type in ['all', 'clinic']:
            clinic_qs = Clinic.objects.filter(
                coordinate_x__isnull=False,
                coordinate_y__isnull=False
            )

            if search_query:
                clinic_qs = clinic_qs.filter(
                    Q(name__icontains=search_query) |
                    Q(address__icontains=search_query)
                )

            if department_code:
                clinic_qs = clinic_qs.filter(departments__code=department_code)

            if all([min_x, max_x, min_y, max_y]):
                clinic_qs = clinic_qs.filter(
                    coordinate_x__gte=min_x,
                    coordinate_x__lte=max_x,
                    coordinate_y__gte=min_y,
                    coordinate_y__lte=max_y
                )

            clinic_qs = order_by_distance(clinic_qs)
            results['clinics'] = ClinicLiteSerializer(
                clinic_qs.distinct()[:100], many=True
            ).data

        # 약국 검색
        if facility_type in ['all', 'pharmacy']:
            pharmacy_qs = Pharmacy.objects.filter(
                coordinate_x__isnull=False,
                coordinate_y__isnull=False
            )

            if search_query:
                pharmacy_qs = pharmacy_qs.filter(
                    Q(name__icontains=search_query) |
                    Q(address__icontains=search_query)
                )

            if all([min_x, max_x, min_y, max_y]):
                pharmacy_qs = pharmacy_qs.filter(
                    coordinate_x__gte=min_x,
                    coordinate_x__lte=max_x,
                    coordinate_y__gte=min_y,
                    coordinate_y__lte=max_y
                )

            pharmacy_qs = order_by_distance(pharmacy_qs)
            results['pharmacies'] = PharmacyLiteSerializer(
                pharmacy_qs[:100], many=True
            ).data

        return Response(results)


class FavoriteHospitalListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteHospitalSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = self._get_patient()
        return FavoriteHospital.objects.filter(patient=patient)

    def perform_create(self, serializer):
        patient = self._get_patient()

        try:
            serializer.save(patient=patient)
        except IntegrityError:
            raise ValidationError({'detail': '이미 즐겨찾기에 등록되어 있습니다.'})

    def _get_patient(self):
        user = self.request.user
        if isinstance(user, DbrPatients):
            return user

        username = getattr(user, 'username', None)
        if not username:
            raise ValidationError({'detail': '환자 정보를 찾을 수 없습니다.'})

        try:
            return DbrPatients.objects.get(user_id=username)
        except DbrPatients.DoesNotExist:
            raise ValidationError({'detail': '환자 정보를 찾을 수 없습니다.'})


class FavoriteHospitalDetailView(generics.DestroyAPIView):
    serializer_class = FavoriteHospitalSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = self._get_patient()
        return FavoriteHospital.objects.filter(patient=patient)

    def _get_patient(self):
        user = self.request.user
        if isinstance(user, DbrPatients):
            return user

        username = getattr(user, 'username', None)
        if not username:
            raise ValidationError({'detail': '환자 정보를 찾을 수 없습니다.'})

        try:
            return DbrPatients.objects.get(user_id=username)
        except DbrPatients.DoesNotExist:
            raise ValidationError({'detail': '환자 정보를 찾을 수 없습니다.'})


class FavoriteClinicListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteClinicSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = self._get_patient()
        return FavoriteClinic.objects.filter(patient=patient)

    def perform_create(self, serializer):
        patient = self._get_patient()

        try:
            serializer.save(patient=patient)
        except IntegrityError:
            raise ValidationError({'detail': '이미 즐겨찾기에 등록되어 있습니다.'})


class FavoriteClinicDetailView(generics.DestroyAPIView):
    serializer_class = FavoriteClinicSerializer
    authentication_classes = [PatientJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        patient = self._get_patient()
        return FavoriteClinic.objects.filter(patient=patient)

    def _get_patient(self):
        try:
            return DbrPatients.objects.get(user_id=self.request.user.username)
        except DbrPatients.DoesNotExist:
            raise ValidationError({'detail': '환자 정보를 찾을 수 없습니다.'})

    def _get_patient(self):
        try:
            return DbrPatients.objects.get(user_id=self.request.user.username)
        except DbrPatients.DoesNotExist:
            raise ValidationError({'detail': '환자 정보를 찾을 수 없습니다.'})
