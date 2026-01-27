from django.db import models
from django.contrib.auth.models import User

class DoctorProfile(models.Model):
    """의사 프로필 모델"""
    doctor_id = models.CharField(max_length=50, primary_key=True, verbose_name="의사 ID")
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    doctor_name = models.CharField(max_length=100, verbose_name="이름")
    doctor_sex = models.CharField(
        max_length=10,
        choices=[('male', '남성'), ('female', '여성')],
        verbose_name="성별"
    )
    doctor_phone = models.CharField(max_length=20, verbose_name="전화번호", blank=True, null=True)
    doctor_email = models.EmailField(max_length=100, verbose_name="이메일", blank=True, null=True)
    doctor_status = models.CharField(
        max_length=20,
        choices=[
            ('진료중', '진료중'),
            ('진료외', '진료외'),
            ('휴무', '휴무')
        ],
        default='진료외',
        verbose_name="상태"
    )
    profile_image = models.ImageField(upload_to='doctor_profiles/', verbose_name="프로필 이미지", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "의사 프로필"
        verbose_name_plural = "의사 프로필"

    def __str__(self):
        return f"{self.doctor_name} ({self.doctor_id})"


class Announcement(models.Model):
    """오늘의 공지사항 모델"""
    title = models.CharField(max_length=200, verbose_name="제목")
    content = models.TextField(verbose_name="내용")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="작성일")
    is_active = models.BooleanField(default=True, verbose_name="활성화")

    class Meta:
        verbose_name = "공지사항"
        verbose_name_plural = "공지사항"
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Patient(models.Model):
    """환자 기본 정보 모델"""
    patient_id = models.CharField(max_length=20, unique=True, verbose_name="환자번호")
    name = models.CharField(max_length=100, verbose_name="이름")
    birth_date = models.DateField(verbose_name="생년월일")
    gender = models.CharField(max_length=10, choices=[('M', '남성'), ('F', '여성')], verbose_name="성별")
    phone = models.CharField(max_length=20, verbose_name="전화번호", blank=True)

    # 간암 진단 정보
    diagnosis_date = models.DateField(verbose_name="진단일", null=True, blank=True)
    bclc_stage = models.CharField(
        max_length=10,
        choices=[
            ('0', 'Stage 0 (Very early)'),
            ('A', 'Stage A (Early)'),
            ('B', 'Stage B (Intermediate)'),
            ('C', 'Stage C (Advanced)'),
            ('D', 'Stage D (Terminal)')
        ],
        verbose_name="BCLC 병기",
        null=True,
        blank=True
    )

    # 종양 특성
    tumor_size = models.FloatField(verbose_name="종양크기(cm)", null=True, blank=True)
    tumor_count = models.IntegerField(verbose_name="종양개수", null=True, blank=True)
    vascular_invasion = models.BooleanField(verbose_name="혈관침범", default=False)

    # 간기능
    child_pugh = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C')],
        verbose_name="Child-Pugh 등급",
        null=True,
        blank=True
    )

    # 바이오마커
    afp_initial = models.FloatField(verbose_name="초기 AFP(ng/mL)", null=True, blank=True)
    afp_current = models.FloatField(verbose_name="최근 AFP(ng/mL)", null=True, blank=True)

    # 치료 정보
    treatment_type = models.CharField(
        max_length=50,
        choices=[
            ('surgery', '수술적 절제'),
            ('transplant', '간이식'),
            ('tace', 'TACE'),
            ('sorafenib', '소라페닙'),
            ('lenvatinib', '렌바티닙')
        ],
        verbose_name="치료방식",
        null=True,
        blank=True
    )
    treatment_start_date = models.DateField(verbose_name="치료시작일", null=True, blank=True)

    # 예후 정보
    survival_1year = models.FloatField(verbose_name="1년 생존율(%)", null=True, blank=True)
    survival_3year = models.FloatField(verbose_name="3년 생존율(%)", null=True, blank=True)
    survival_5year = models.FloatField(verbose_name="5년 생존율(%)", null=True, blank=True)

    recurrence_risk = models.CharField(
        max_length=10,
        choices=[
            ('low', '저위험'),
            ('medium', '중위험'),
            ('high', '고위험')
        ],
        verbose_name="재발위험도",
        null=True,
        blank=True
    )

    # 추적관찰
    next_ct_date = models.DateField(verbose_name="다음 CT 검사일", null=True, blank=True)
    next_blood_test_date = models.DateField(verbose_name="다음 혈액검사일", null=True, blank=True)

    # 담당의
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.SET_NULL, null=True, verbose_name="담당의")

    # CT 이미지
    ct_image = models.ImageField(upload_to='ct_images/', verbose_name="간암 CT 이미지", blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "환자"
        verbose_name_plural = "환자"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient_id} - {self.name}"


class Drug(models.Model):
    """약물 정보 마스터 데이터"""
    drug_code = models.CharField(max_length=50, primary_key=True, verbose_name="약물 코드")
    drug_name_kr = models.CharField(max_length=200, verbose_name="약물명(한글)")
    drug_name_en = models.CharField(max_length=200, verbose_name="약물명(영문)", blank=True)

    # 기본 정보
    drug_category = models.CharField(
        max_length=100,
        verbose_name="약물 분류",
        help_text="예: 항암제, 면역억제제 등"
    )

    # 용법/용량
    dosage = models.TextField(verbose_name="용법/용량", blank=True)

    # 효능/효과
    efficacy = models.TextField(verbose_name="효능/효과", blank=True)

    # 주의사항
    precautions = models.TextField(verbose_name="주의사항", blank=True)

    # 일반적인 부작용
    common_side_effects = models.TextField(verbose_name="일반적인 부작용", help_text="줄바꿈으로 구분", blank=True)

    # 심각한 부작용
    serious_side_effects = models.TextField(verbose_name="심각한 부작용", help_text="줄바꿈으로 구분", blank=True)

    # 금기사항
    contraindications = models.TextField(verbose_name="금기사항", blank=True)

    # 상호작용
    interactions = models.TextField(verbose_name="약물 상호작용", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "약물 정보"
        verbose_name_plural = "약물 정보"
        ordering = ['drug_name_kr']

    def __str__(self):
        return f"{self.drug_name_kr} ({self.drug_code})"


class DrugInteraction(models.Model):
    """약물 상호작용 정보"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, verbose_name="환자", related_name="drug_interactions")
    drug_name = models.CharField(max_length=200, verbose_name="약물명")
    risk_level = models.CharField(
        max_length=20,
        choices=[
            ('high', '고위험 (>50%)'),
            ('medium', '중위험 (20-50%)'),
            ('low', '저위험 (<20%)')
        ],
        verbose_name="위험도"
    )
    side_effect = models.CharField(max_length=200, verbose_name="부작용")
    probability = models.IntegerField(verbose_name="발생 확률(%)")
    color_code = models.CharField(max_length=20, verbose_name="색상코드", help_text="예: red, yellow, green")
    action_plan = models.TextField(verbose_name="조치 계획", blank=True)
    monitoring = models.TextField(verbose_name="모니터링 항목", blank=True, help_text="관찰해야 할 증상이나 검사 항목")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "약물 상호작용"
        verbose_name_plural = "약물 상호작용"
        ordering = ['-probability']

    def __str__(self):
        return f"{self.patient.name} - {self.drug_name} ({self.side_effect})"
