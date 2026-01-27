from django.db import models
import uuid


# ----------------------------------------
# 1. 환자 정보 테이블 (dbr_patients)
# ----------------------------------------
class DbrPatients(models.Model):
    SEX_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
    ]

    patient_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="환자 ID"
    )
    name = models.CharField(max_length=100, verbose_name="이름")
    birth_date = models.DateField(verbose_name="생년월일")
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, verbose_name="성별")
    # resident_number = models.CharField(max_length=13, blank=True, null=True, verbose_name="주민등록번호")
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name="전화번호")
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name="주소")
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="신장(cm)")
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="체중(kg)")
    user_id = models.CharField(max_length=150, unique=True, verbose_name="로그인 ID")
    password = models.CharField(max_length=128, verbose_name="비밀번호")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        managed = True
        db_table = "dbr_patients"
        verbose_name = "환자"
        verbose_name_plural = "환자 목록"

    def __str__(self):
        return f"{self.name} ({self.user_id})"

    @property
    def is_authenticated(self):
        """DRF의 IsAuthenticated 권한 검사용"""
        return True

    @property
    def is_active(self):
        """JWT 토큰 발급을 위해 필수"""
        return True

# ----------------------------------------
# 2️. 혈액검사 결과 테이블 (dbr_blood_results)
# ----------------------------------------
class DbrBloodResults(models.Model):
    blood_result_id = models.AutoField(primary_key=True)
    patient_id = models.ForeignKey(
        DbrPatients,
        on_delete=models.CASCADE,
        related_name="blood_results",
        db_column="patient_id",
        verbose_name="환자 ID"
    )
    ast = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    alt = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    alp = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    ggt = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    bilirubin = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    albumin = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    inr = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    platelet = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    afp = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    albi = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    taken_at = models.DateField(verbose_name="검사일자")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    
    r_gtp = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    total_protein = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    pt = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    albi_grade = models.CharField(max_length=7, blank=True, null=True,)
    risk_level = models.CharField(max_length=7, choices=[('safe', 'safe'),('warning','warning'),('danger','danger')],
                                     blank=True, null=True)

    class Meta:
        managed = True
        db_table = "dbr_blood_results"
        verbose_name = "혈액검사 결과"
        verbose_name_plural = "혈액검사 결과 목록"

    def save(self, *args, **kwargs):
        if self.bilirubin and self.albumin > 0:
            import math
            log10_bilirubin = math.log10(float(self.bilirubin))
            self.albi = (0.66 * log10_bilirubin) - (0.085 * float(self.albumin))
        
            if self.albi <= -2.60:
                self.albi_grade = 'Grade 1'
                self.risk_level = 'safe'
            elif self.albi <= -1.39:
                self.albi_grade = 'Grade 2'
                self.risk_level = 'warning'
            else:
                self.albi_grade = 'Grade 3'
                self.risk_level = 'danger'
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.patient.name} - {self.taken_at}"


# ----------------------------------------
# 3️. 혈액검사 기준 테이블 (dbr_blood_test_references)
# ----------------------------------------
class DbrBloodTestReferences(models.Model):
    reference_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, verbose_name="검사 항목명")
    normal_range_min = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    normal_range_max = models.DecimalField(max_digits=7, decimal_places=2, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True, verbose_name="단위")
    description = models.TextField(blank=True, null=True, verbose_name="설명")

    class Meta:
        managed = True
        db_table = "dbr_blood_test_references"
        verbose_name = "혈액검사 기준"
        verbose_name_plural = "혈액검사 기준 목록"

    def __str__(self):
        return f"{self.name} ({self.unit or '-'})"


# ----------------------------------------
# 4️. 일정관리 테이블 (dbr_appointments)
# ----------------------------------------
class DbrAppointments(models.Model):
    APPOINTMENT_TYPE_CHOICES = [
        ('blood_test', '혈액검사'),
        ('ct', 'CT 검사'),
        ('mri', 'MRI 검사'),
        ('ultrasound', '초음파 검사'),
        ('consultation', '진료 상담'),
        ('other', '기타'),
    ]

    STATUS_CHOICES = [
        ('scheduled', '예정'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]

    appointment_id = models.AutoField(primary_key=True)
    patient_id = models.ForeignKey(
        DbrPatients,
        on_delete=models.CASCADE,
        related_name="appointments",
        db_column="patient_id",
        verbose_name="환자 ID"
    )
    appointment_date = models.DateField(verbose_name="검사 일정")
    appointment_time = models.TimeField(blank=True, null=True, verbose_name="검사 시간")
    hospital = models.CharField(max_length=100, verbose_name="병원명")
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='blood_test',
        verbose_name="검사 종류"
    )
    details = models.TextField(blank=True, null=True, verbose_name="자세한 내용")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name="상태"
    )
    reminder_enabled = models.BooleanField(default=True, verbose_name="알림 설정")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        managed = True
        db_table = "dbr_appointments"
        verbose_name = "검사 일정"
        verbose_name_plural = "검사 일정 목록"
        ordering = ['appointment_date', 'appointment_time']

    def __str__(self):
        return f"{self.patient.name} - {self.hospital} ({self.appointment_date})"


# ----------------------------------------
# 4. Medications (약물 정보)
# ----------------------------------------
class Medication(models.Model):
    medication_id = models.AutoField(primary_key=True)
    patient_id = models.ForeignKey(
        DbrPatients,
        on_delete=models.CASCADE,
        related_name="medications",
        db_column="patient_id",
        verbose_name="환자 ID"
    )
    medication_name = models.CharField(max_length=200, verbose_name="약물명")
    dosage = models.CharField(max_length=100, verbose_name="용량")  # "100mg"
    frequency = models.CharField(max_length=100, verbose_name="복용 빈도")  # "1일 2회"
    timing = models.CharField(max_length=100, verbose_name="복용 시간")  # "아침/저녁 식후"
    start_date = models.DateField(verbose_name="복용 시작일")
    end_date = models.DateField(null=True, blank=True, verbose_name="복용 종료일")
    is_active = models.BooleanField(default=True, verbose_name="활성 상태")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        managed = True
        db_table = "dbr_medications"
        verbose_name = "약물 정보"
        verbose_name_plural = "약물 정보 목록"
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.patient.name} - {self.medication_name}"


# ----------------------------------------
# 5. MedicationLog (복용 기록)
# ----------------------------------------
class MedicationLog(models.Model):
    log_id = models.AutoField(primary_key=True)
    medication = models.ForeignKey(
        Medication,
        on_delete=models.CASCADE,
        related_name="logs",
        db_column="medication_id",
        verbose_name="약물 ID"
    )
    taken_date = models.DateField(verbose_name="복용 날짜")
    taken_time = models.TimeField(verbose_name="복용 시간")
    is_taken = models.BooleanField(default=True, verbose_name="복용 여부")
    notes = models.TextField(blank=True, null=True, verbose_name="메모")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

    class Meta:
        managed = True
        db_table = "dbr_medication_logs"
        verbose_name = "복용 기록"
        verbose_name_plural = "복용 기록 목록"
        ordering = ['-taken_date', '-taken_time']

    def __str__(self):
        return f"{self.medication.medication_name} - {self.taken_date}"

# (추가) 6. DUR Drug Info (기존 DB 읽기용)
# (DDI 검사 시 약물 이름 <-> DrugBank ID 변환용)
# ----------------------------------------
class DurDrugInfo(models.Model):
    # 'drugbank_id'가 "DB01115" 같은 문자열 ID라고 가정
    drugbank_id = models.CharField(
        primary_key=True, 
        max_length=100, 
        db_column="drugbank_id"
    )
    # 약물 영문명 (검색용)
    name = models.CharField(max_length=255, db_column="name")

    class Meta:
        managed = False  # Django가 이 테이블을 관리하지 않음 (이미 존재함)
        db_table = "dur_drug_info" # 👈 실제 테이블명
        verbose_name = "DUR 약물 정보"

# ==========================================================
# 👈 [추가] 7. DurDrugMapping 모델 (검색용)
# (이전에 보여주신 dur_drug_mapping 테이블 스크린샷 기준)
# ==========================================================
class DurDrugMapping(models.Model):
    id = models.AutoField(primary_key=True)
    KoreanName = models.CharField(max_length=255, null=True, blank=True)
    EnglishName = models.CharField(max_length=255, null=True, blank=True)
    DrugBank_ID = models.CharField(max_length=50, null=True, blank=True)
    HIRA_Code = models.CharField(max_length=100, null=True, blank=True)
    ATC_Code = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        managed = False # Django가 관리하지 않음 (읽기 전용)
        db_table = "dur_drug_mapping" # 👈 실제 테이블명
        verbose_name = "DUR 약물 매핑"
# ----------------------------------------
# (추가) 7. DUR DDI DrugBank (기존 DB 읽기용)
# (병용 금기 규칙 테이블)
# ----------------------------------------
class DurDdiDrugbank(models.Model):
    id = models.AutoField(primary_key=True)
    drug1_id = models.CharField(max_length=100, db_column="drug1_id")
    drug2_id = models.CharField(max_length=100, db_column="drug2_id")
    interaction_type = models.IntegerField(db_column="interaction_type")
    
    class Meta:
        managed = False
        db_table = "dur_ddi_drugbank"
        verbose_name = "DUR DrugBank 상호작용"
# # ----------------------------------------
# # 6. MedicalFacility (의료 시설 - HealthcareMap 연동)
# # ----------------------------------------
# class MedicalFacility(models.Model):
#     FACILITY_TYPE_CHOICES = [
#         ('hospital', '병원'),
#         ('clinic', '의원'),
#         ('pharmacy', '약국'),
#     ]

#     facility_id = models.AutoField(primary_key=True)
#     facility_type = models.CharField(max_length=20, choices=FACILITY_TYPE_CHOICES, verbose_name="시설 유형")
#     name = models.CharField(max_length=200, verbose_name="시설명")
#     address = models.CharField(max_length=500, verbose_name="주소")
#     phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="전화번호")
#     coordinate_x = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name="좌표(x)")
#     coordinate_y = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name="좌표(y)")
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

#     class Meta:
#         managed = True
#         db_table = "dbr_medical_facilities"
#         verbose_name = "의료 시설"
#         verbose_name_plural = "의료 시설 목록"

#     def __str__(self):
#         return f"{self.get_facility_type_display()} - {self.name}"


# # ----------------------------------------
# # 7. FavoriteFacility (즐겨찾기 시설)
# # ----------------------------------------
# class FavoriteFacility(models.Model):
#     favorite_id = models.AutoField(primary_key=True)
#     patient = models.ForeignKey(
#         DbrPatients,
#         on_delete=models.CASCADE,
#         related_name="favorite_facilities",
#         db_column="patient_id",
#         verbose_name="환자 ID"
#     )
#     facility = models.ForeignKey(
#         MedicalFacility,
#         on_delete=models.CASCADE,
#         related_name="favorited_by",
#         db_column="facility_id",
#         verbose_name="시설 ID"
#     )
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")

#     class Meta:
#         managed = True
#         db_table = "dbr_favorite_facilities"
#         verbose_name = "즐겨찾기 시설"
#         verbose_name_plural = "즐겨찾기 시설 목록"
#         unique_together = [['patient', 'facility']]

#     def __str__(self):
#         return f"{self.patient.name} - {self.facility.name}"

