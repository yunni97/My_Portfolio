from rest_framework import serializers
from .models import (
    Hospital,
    Clinic,
    Pharmacy,
    DepartmentOfTreatment,
    FavoriteHospital,
    FavoriteClinic,
)


class DepartmentOfTreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepartmentOfTreatment
        fields = ['id', 'code', 'name']


# 경량 Serializer (지도 마커용 - departments 제외)
class HospitalLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'address', 'phone', 'business_type',
            'coordinate_x', 'coordinate_y'
        ]


class ClinicLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'address', 'phone', 'business_type',
            'coordinate_x', 'coordinate_y'
        ]


class PharmacyLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'address', 'phone',
            'coordinate_x', 'coordinate_y'
        ]


# 풀 Serializer (상세 정보용)
class HospitalSerializer(serializers.ModelSerializer):
    departments = DepartmentOfTreatmentSerializer(many=True, read_only=True)

    class Meta:
        model = Hospital
        fields = [
            'id', 'name', 'address', 'phone', 'business_type',
            'coordinate_x', 'coordinate_y', 'departments', 'created_at'
        ]
        read_only_fields = ['created_at']


class ClinicSerializer(serializers.ModelSerializer):
    departments = DepartmentOfTreatmentSerializer(many=True, read_only=True)

    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'address', 'phone', 'business_type',
            'coordinate_x', 'coordinate_y', 'departments', 'created_at'
        ]
        read_only_fields = ['created_at']


class PharmacySerializer(serializers.ModelSerializer):
    class Meta:
        model = Pharmacy
        fields = [
            'id', 'name', 'address', 'phone',
            'coordinate_x', 'coordinate_y', 'created_at'
        ]
        read_only_fields = ['created_at']


class FavoriteHospitalSerializer(serializers.ModelSerializer):
    patient_id = serializers.UUIDField(source='patient.patient_id', read_only=True)
    hospital = HospitalLiteSerializer(read_only=True)
    hospital_id = serializers.PrimaryKeyRelatedField(
        queryset=Hospital.objects.all(),
        source='hospital',
        write_only=True,
    )

    class Meta:
        model = FavoriteHospital
        fields = ['favorite_id', 'patient_id', 'hospital', 'hospital_id', 'created_at']
        read_only_fields = ['favorite_id', 'patient_id', 'hospital', 'created_at']


class FavoriteClinicSerializer(serializers.ModelSerializer):
    patient_id = serializers.UUIDField(source='patient.patient_id', read_only=True)
    clinic = ClinicLiteSerializer(read_only=True)
    clinic_id = serializers.PrimaryKeyRelatedField(
        queryset=Clinic.objects.all(),
        source='clinic',
        write_only=True,
    )

    class Meta:
        model = FavoriteClinic
        fields = ['favorite_id', 'patient_id', 'clinic', 'clinic_id', 'created_at']
        read_only_fields = ['favorite_id', 'patient_id', 'clinic', 'created_at']
