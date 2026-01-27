# liverguard/serializers.py
from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import Q
from .models import (
    DbrPatients, DbrBloodResults, DbrAppointments, DbrBloodTestReferences,
    Medication, MedicationLog, DurDrugInfo, DurDdiDrugbank
)
from rest_framework_simplejwt.tokens import RefreshToken
from .models import DurDrugInfo,DurDrugMapping,DurDdiDrugbank

# Auth serializers
# sign up serializers
class DbrPatientRegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)
    birth_date = serializers.DateField(
        input_formats=["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"],
        format="%Y-%m-%d"
    )
    class Meta:
        model = DbrPatients
        fields = [
            "user_id", "password", "password2",
            "name", "birth_date", "sex", "phone"
        ]
        extra_kwargs = {
            "password": {"write_only": True},
        }
    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        return data
    def create(self, validated_data):
        validated_data.pop("password2")
        validated_data["password"] = make_password(validated_data["password"])
        return DbrPatients.objects.create(**validated_data)

# login serializers
class DbrPatientLoginSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user_id = data.get("user_id")
        password = data.get("password")

        try:
            user = DbrPatients.objects.get(user_id=user_id)
        except DbrPatients.DoesNotExist:
            raise serializers.ValidationError({"user_id": "존재하지 않는 사용자입니다."})

        if not check_password(password, user.password):
            raise serializers.ValidationError({"password": "비밀번호가 올바르지 않습니다."})

        # ✅ 검증 통과 시 user 객체만 전달
        data["user"] = user
        return data

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = DbrPatients
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True}  # 비밀번호는 응답에 포함하지 않음
        }
        

class BloodResultSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient_id.name', read_only=True)

    class Meta:
        model = DbrBloodResults
        fields = '__all__'
        read_only_fields = ['created_at']
        extra_kwargs = {
            'patient_id': {'required': False}  # 수정 시 필수 아님, 생성 시에만 필수
        }

    def update(self, instance, validated_data):
        # 수정 시 patient_id가 들어와도 무시 (변경 불가)
        validated_data.pop('patient_id', None)
        return super().update(instance, validated_data)


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient_id.name', read_only=True)
    appointment_type_display = serializers.CharField(source='get_appointment_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DbrAppointments
        fields = '__all__'
        read_only_fields = ['appointment_id', 'created_at', 'updated_at']
        extra_kwargs = {
            'patient_id': {'required': False}  # 수정 시 필수 아님, 생성 시에만 필수
        }

    def update(self, instance, validated_data):
        # 수정 시 patient_id가 들어와도 무시 (변경 불가)
        validated_data.pop('patient_id', None)
        return super().update(instance, validated_data)


class BloodTestReferenceSerializer(serializers.ModelSerializer):
    normal_range_min = serializers.FloatField()
    normal_range_max = serializers.FloatField()

    class Meta:
        model = DbrBloodTestReferences
        fields = '__all__'


# ==================== 약물 관련 Serializers ====================
class MedicationSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient_id.name', read_only=True)

    class Meta:
        model = Medication
        fields = '__all__'
        read_only_fields = ['created_at']


class MedicationLogSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.medication_name', read_only=True)
    patient_name = serializers.CharField(source='medication.patient_id.name', read_only=True)

    class Meta:
        model = MedicationLog
        fields = '__all__'
        read_only_fields = ['created_at']

# ==========================================================
# ✍️ (추가) 5-2. 약물 생성/수정용 Serializer (DDI 검사 포함)
# ==========================================================
class MedicationCreateUpdateSerializer(serializers.ModelSerializer):
    
    # DDI 검사를 무시할지 여부를 프론트엔드에서 받음
    override_ddi_check = serializers.BooleanField(
        write_only=True, 
        default=False, 
        required=False
    )

    class Meta:
        model = Medication
        fields = [
            # 'patient_id',       # 뷰에서 자동 처리
            'medication_id',
            'medication_name', 
            'dosage', 
            'frequency', 
            'timing', 
            'start_date', 
            'end_date', 
            'is_active',
            'override_ddi_check'  # DDI 검사 무시용 필드
        ]
        extra_kwargs = {
            'medication_id': {'read_only': True},
            'patient_id': {'required': False} 
        }

    def _get_drug_id(self, drug_name):
        """
        약물 이름(한글/영문)을 기반으로 DurDrugMapping 테이블에서
        DrugBank_ID를 조회합니다.
        """
        if not drug_name:
            return None
        try:
            drug_info = DurDrugMapping.objects.filter(
                Q(KoreanName__iexact=drug_name) | 
                Q(EnglishName__iexact=drug_name)  
            ).first()
            
            if drug_info:
                return drug_info.DrugBank_ID 
        except DurDrugMapping.DoesNotExist:
            return None
        return None

    def validate(self, data):
        # 👈 [FIX 1] DDI 검사 무시(override) 플래그를 먼저 확인합니다.
        # 이 값이 True이면, DDI 검사 로직을 모두 건너뜁니다.
        override_ddi_check = data.get('override_ddi_check', False)
        if override_ddi_check:
            print(f"[Warning] DDI 검사를 클라이언트 요청에 의해 건너뜁니다.")
            return data # 👈 유효성 검사를 통과시키고 즉시 반환

        # --- (override_ddi_check가 False일 때만 아래 로직 실행) ---

        # 1. Flutter에서 받은 약물 이름 (예: "와파린")
        new_drug_name = data.get('medication_name')
        
        # 2. 약물 이름으로 DrugBank_ID 조회
        new_drug_id = self._get_drug_id(new_drug_name)
        
        if not new_drug_id:
            print(f"[Warning] DrugBank_ID를 찾을 수 없음: {new_drug_name}")
            return data # DDI 검사를 건너뛰고 그냥 반환

        # 3. 현재 환자가 복용 중인 다른 약물들 조회
        patient = self.context['request'].user
        
        exclude_kwargs = {}
        if self.instance:
            exclude_kwargs['pk'] = self.instance.pk
            
        active_medications = Medication.objects.filter(
            patient_id=patient, 
            is_active=True
        ).exclude(**exclude_kwargs)

        # 4. DDI 검사 수행
        for existing_med in active_medications:
            existing_drug_id = self._get_drug_id(existing_med.medication_name)
            if not existing_drug_id:
                continue

            is_conflict = DurDdiDrugbank.objects.filter(
                (Q(drug1_id=new_drug_id) & Q(drug2_id=existing_drug_id)) |
                (Q(drug1_id=existing_drug_id) & Q(drug2_id=new_drug_id))
            ).exists()

            if is_conflict:
                # DDI 충돌 발생! (override_ddi_check=False 이므로 에러 반환)
                raise serializers.ValidationError({
                    'status': 'DDI_CONFLICT',
                    'message': f"'{new_drug_name}'은(는) 현재 복용 중인 '{existing_med.medication_name}'과(와) 심각한 상호작용이 있습니다.",
                    'conflict_with': existing_med.medication_name
                })

        return data

    # 👈 [FIX 2] create 메소드를 오버라이드하여 TypeError 해결
    def create(self, validated_data):
        """
        DB 모델(Medication)에 없는 'override_ddi_check' 필드를 
        validated_data에서 제거한 후 객체를 생성합니다.
        """
        
        # 'override_ddi_check' 필드를 validated_data에서 제거 (DB에 없는 필드이므로)
        validated_data.pop('override_ddi_check', None) 

        # 'override_ddi_check'가 제거된 깔끔한 데이터로 부모 create 호출
        instance = super().create(validated_data)
        
        return instance

    # 👈 (선택) 업데이트 시에도 동일한 문제가 발생할 수 있으므로
    #     update 메소드도 추가해주는 것이 좋습니다.
    def update(self, instance, validated_data):
        """
        업데이트 시에도 'override_ddi_check' 필드를 제거합니다.
        """
        validated_data.pop('override_ddi_check', None)
        
        instance = super().update(instance, validated_data)
        
        return instance

# # ==================== 의료기관 관련 Serializers ====================
# class MedicalFacilitySerializer(serializers.ModelSerializer):
#     type_display = serializers.CharField(source='get_type_display', read_only=True)

#     class Meta:
#         model = MedicalFacility
#         fields = '__all__'
#         read_only_fields = ['created_at']


# class FavoriteFacilitySerializer(serializers.ModelSerializer):
#     patient_name = serializers.CharField(source='patient.name', read_only=True)
#     facility_name = serializers.CharField(source='facility.name', read_only=True)
#     facility_type = serializers.CharField(source='facility.type', read_only=True)
#     facility_address = serializers.CharField(source='facility.address', read_only=True)

#     class Meta:
#         model = FavoriteFacility
#         fields = '__all__'
#         read_only_fields = ['created_at']

class DurDrugInfoSearchSerializer(serializers.ModelSerializer):
    """
    약물 마스터(DurDrugMapping) 검색 결과를 위한 Serializer
    """
    class Meta:
        model = DurDrugMapping # 👈 [수정] 모델 변경
        
        # 👈 [수정] DurDrugMapping의 실제 컬럼명으로 변경
        # (Flutter에서 약물명으로 'KoreanName'을 사용합니다)
        fields = ['id', 'KoreanName', 'EnglishName', 'DrugBank_ID']