from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    department_id = models.AutoField(primary_key=True, verbose_name='부서 ID')
    department_code = models.CharField(max_length=10, null=True, blank=True, verbose_name='부서코드')
    department = models.CharField(max_length=50, null=True, blank=True, verbose_name='부서')

    class Meta:
        db_table = 'departments'
        verbose_name = '부서'
        verbose_name_plural = '부서'

    def __str__(self):
        return self.department or f'부서 {self.department_id}'


class DoctorProfile(models.Model):
    SEX_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
    ]

    STATUS_CHOICES = [
        ('on_duty', '근무중'),
        ('available', '대기중'),
        ('off_duty', '퇴근'),
    ]

    doctor_id = models.AutoField(primary_key=True, verbose_name='의사 ID')
    name = models.CharField(max_length=50, verbose_name='이름')
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, verbose_name='성별')
    phone = models.CharField(max_length=11, unique=True, null=True, blank=True, verbose_name='연락처')
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True, verbose_name='이메일')
    # password = models.CharField(max_length=50, null=True, blank=True, verbose_name='패스워드')
    status = models.CharField(
        max_length=9,
        choices=STATUS_CHOICES,
        default='off_duty',
        verbose_name='근무상태'
    )
    position = models.CharField(max_length=50, null=True, blank=True, verbose_name='직책')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True, verbose_name='수정일')
    departments = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        db_column='departments_id',
        verbose_name='부서 ID'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        verbose_name='관리자 ID'
    )

    class Meta:
        db_table = 'doctor_profiles'
        verbose_name = '의사 프로필'
        verbose_name_plural = '의사 프로필'

    def __str__(self):
        return self.name


class NurseProfile(models.Model):
    SEX_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
    ]

    STATUS_CHOICES = [
        ('on_duty', '근무중'),
        ('off_duty', '퇴근'),
        ('vacation', '휴가'),
    ]

    nurse_id = models.AutoField(primary_key=True, verbose_name='간호사 ID')
    name = models.CharField(max_length=50, verbose_name='이름')
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, verbose_name='성별')
    phone = models.CharField(max_length=11, verbose_name='연락처')
    email = models.EmailField(max_length=100, verbose_name='이메일')
    position = models.CharField(max_length=50, null=True, blank=True, verbose_name='직급')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='on_duty',
        verbose_name='근무상태'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        verbose_name='계정 ID'
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        db_column='department_id',
        verbose_name='부서 ID'
    )

    class Meta:
        db_table = 'nurse_profiles'
        verbose_name = '간호사 프로필'
        verbose_name_plural = '간호사 프로필'

    def __str__(self):
        return self.name


class Patient(models.Model):
    SEX_CHOICES = [
        ('male', '남성'),
        ('female', '여성'),
    ]

    patient_id = models.BigAutoField(primary_key=True, verbose_name='환자 ID')
    name = models.CharField(max_length=100, verbose_name='이름')
    birth_date = models.DateField(null=True, blank=True, verbose_name='생년월일')
    sex = models.CharField(max_length=6, choices=SEX_CHOICES, verbose_name='성별')
    resident_number = models.CharField(max_length=20, verbose_name='주민번호')
    phone = models.CharField(max_length=11, verbose_name='연락처')
    address = models.CharField(max_length=255, null=True, blank=True, verbose_name='주소')
    diagnosis_date = models.DateField(null=True, blank=True, verbose_name='최초 암 진단일')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')

    class Meta:
        db_table = 'patients'
        verbose_name = '환자'
        verbose_name_plural = '환자'

    def __str__(self):
        return f"{self.name} ({self.patient_id})"


class Drug(models.Model):
    drug_id = models.AutoField(primary_key=True, verbose_name='약물 ID')
    name_kr = models.TextField(verbose_name='한글 약품명')
    name_eng = models.TextField(verbose_name='영문 약품명')
    drug_category = models.CharField(max_length=100, null=True, blank=True, verbose_name='약물 분류')
    efficacy = models.TextField(null=True, blank=True, verbose_name='효능')
    precautions = models.TextField(null=True, blank=True, verbose_name='주의사항')

    class Meta:
        db_table = 'drugs'
        verbose_name = '약물'
        verbose_name_plural = '약물'

    def __str__(self):
        return (self.name_kr or self.name_eng)[:50]


class MedicalRecord(models.Model):
    record_id = models.AutoField(primary_key=True, verbose_name='진료기록 ID')
    visit_date = models.DateTimeField(auto_now_add=True, verbose_name='진료일시')
    chief_complaint = models.CharField(max_length=255, null=True, blank=True, verbose_name='주증상')
    subjective = models.TextField(null=True, blank=True, verbose_name='주관적 소견')
    objective = models.TextField(null=True, blank=True, verbose_name='객관적 소견')
    assessment = models.TextField(null=True, blank=True, verbose_name='진단 소견')
    plan = models.TextField(null=True, blank=True, verbose_name='치료 계획')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id',
        verbose_name='환자'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        db_column='doctor_id',
        verbose_name='담당 의사'
    )

    class Meta:
        db_table = 'medical_records'
        verbose_name = '진료기록'
        verbose_name_plural = '진료기록'

    def __str__(self):
        return f"Record {self.record_id} - Patient {self.patient_id}"


class TestOrder(models.Model):
    TEST_CHOICES = [
        ('CT', 'CT'),
        ('MRI', 'MRI'),
        ('US', 'US'),
        ('Blood', 'Blood'),
        ('Genomic', 'Genomic'),
    ]

    STATUS_CHOICES = [
        ('Requested', 'Requested'),
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Canceled', 'Canceled'),
    ]

    order_id = models.AutoField(primary_key=True, verbose_name='오더 ID')
    test_type = models.CharField(max_length=10, choices=TEST_CHOICES, verbose_name='검사 종류')
    body_part = models.CharField(max_length=50, null=True, blank=True, verbose_name='촬영 부위')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Requested',
        verbose_name='진행 상태'
    )
    ordered_at = models.DateTimeField(auto_now_add=True, verbose_name='오더 시간')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='완료 시간')
    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        db_column='record_id',
        verbose_name='진료기록'
    )

    class Meta:
        db_table = 'test_orders'
        verbose_name = '검사 오더'
        verbose_name_plural = '검사 오더'

    def __str__(self):
        return f"Order {self.order_id} ({self.test_type})"


class MedicalDiagnosis(models.Model):
    diagnosis_id = models.AutoField(primary_key=True, verbose_name='진단 ID')
    icd_code = models.CharField(max_length=10, null=True, blank=True, verbose_name='ICD-10 코드')
    diagnosis_name = models.CharField(max_length=255, null=True, blank=True, verbose_name='진단명')
    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        db_column='record_id',
        verbose_name='진료기록'
    )

    class Meta:
        db_table = 'medical_diagnosis'
        verbose_name = '의학적 진단'
        verbose_name_plural = '의학적 진단'

    def __str__(self):
        return self.diagnosis_name or str(self.diagnosis_id)


class MedicalVitals(models.Model):
    vital_id = models.AutoField(primary_key=True, verbose_name='바이탈 ID')
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='신장')
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name='체중')
    bp_systolic = models.IntegerField(null=True, blank=True, verbose_name='수축기 혈압')
    bp_diastolic = models.IntegerField(null=True, blank=True, verbose_name='이완기 혈압')
    heart_rate = models.IntegerField(null=True, blank=True, verbose_name='심박수')
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, verbose_name='체온')
    measured_at = models.DateTimeField(auto_now_add=True, verbose_name='측정시각')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id',
        verbose_name='환자'
    )

    class Meta:
        db_table = 'medical_vitals'
        verbose_name = '바이탈'
        verbose_name_plural = '바이탈'

    def __str__(self):
        return f"Vitals {self.vital_id} - Patient {self.patient_id}"


class ClinicalRecord(models.Model):
    clinical_id = models.AutoField(primary_key=True, verbose_name='임상검사 ID')
    tumor_stage = models.CharField(max_length=20, null=True, blank=True, verbose_name='TNM 병기')
    child_pugh = models.CharField(max_length=5, null=True, blank=True, verbose_name='Child-Pugh 등급')
    afp = models.FloatField(null=True, blank=True, verbose_name='AFP 수치')
    albumin = models.FloatField(null=True, blank=True, verbose_name='알부민')
    bilirubin = models.FloatField(null=True, blank=True, verbose_name='빌리루빈')
    platelet = models.FloatField(null=True, blank=True, verbose_name='혈소판')
    creatinine = models.FloatField(null=True, blank=True, verbose_name='크레아티닌')
    test_date = models.DateTimeField(auto_now_add=True, verbose_name='검사일')
    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        db_column='record_id',
        verbose_name='관련 진료기록'
    )

    class Meta:
        db_table = 'clinical_records'
        verbose_name = '임상기록'
        verbose_name_plural = '임상기록'

    def __str__(self):
        return f"Clinical {self.clinical_id}"


class Prescription(models.Model):
    prescription_id = models.AutoField(primary_key=True, verbose_name='처방전 ID')
    drug_name = models.CharField(max_length=100, null=True, blank=True, verbose_name='약물명')
    dosage = models.CharField(max_length=50, null=True, blank=True, verbose_name='용량')
    frequency = models.CharField(max_length=20, null=True, blank=True, verbose_name='횟수')
    duration = models.CharField(max_length=20, null=True, blank=True, verbose_name='기간')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='처방일')
    record = models.ForeignKey(
        MedicalRecord,
        on_delete=models.CASCADE,
        db_column='record_id',
        verbose_name='진료기록'
    )

    class Meta:
        db_table = 'prescriptions'
        verbose_name = '처방전'
        verbose_name_plural = '처방전'

    def __str__(self):
        return f"Prescription {self.prescription_id}"


class NursingNote(models.Model):
    note_id = models.AutoField(primary_key=True, verbose_name='간호기록 ID')
    note_content = models.TextField(null=True, blank=True, verbose_name='간호 기록 내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    nurse = models.ForeignKey(
        NurseProfile,
        on_delete=models.CASCADE,
        db_column='nurse_id',
        verbose_name='작성 간호사'
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id',
        verbose_name='환자'
    )

    class Meta:
        db_table = 'nursing_notes'
        verbose_name = '간호기록'
        verbose_name_plural = '간호기록'

    def __str__(self):
        return f"Note {self.note_id} - Patient {self.patient_id}"


class GenomicRecord(models.Model):
    sample_id = models.AutoField(primary_key=True, verbose_name='샘플 ID')
    sample_date = models.DateField(verbose_name='채취일')
    gene_data = models.JSONField(verbose_name='유전자 발현량')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id',
        verbose_name='환자'
    )
    order = models.ForeignKey(
        TestOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='order_id',
        verbose_name='오더'
    )

    class Meta:
        db_table = 'genomic_records'
        verbose_name = '유전체 기록'
        verbose_name_plural = '유전체 기록'

    def __str__(self):
        return f"Genomic {self.sample_id} - Patient {self.patient_id}"


class DicomStudy(models.Model):
    study_uid = models.CharField(max_length=100, primary_key=True, verbose_name='Study UID')
    study_date = models.DateField(verbose_name='촬영 날짜')
    study_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name='검사 설명')
    modality = models.CharField(max_length=10, default='CT', verbose_name='장비 종류')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id',
        verbose_name='환자'
    )
    order = models.ForeignKey(
        TestOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column='order_id',
        verbose_name='오더'
    )

    class Meta:
        db_table = 'dicom_studies'
        verbose_name = 'DICOM Study'
        verbose_name_plural = 'DICOM Study'

    def __str__(self):
        return self.study_uid


class DicomSeries(models.Model):
    PHASE_CHOICES = [
        ('Arterial', 'Arterial'),
        ('Venous', 'Venous'),
        ('Delayed', 'Delayed'),
        ('Unknown', 'Unknown'),
    ]

    series_uid = models.CharField(max_length=100, primary_key=True, verbose_name='Series UID')
    series_number = models.IntegerField(null=True, blank=True, verbose_name='시리즈 번호')
    series_desc = models.CharField(max_length=255, null=True, blank=True, verbose_name='시리즈 설명')
    phase_label = models.CharField(
        max_length=10,
        choices=PHASE_CHOICES,
        null=True,
        blank=True,
        verbose_name='페이즈 라벨'
    )
    slice_count = models.IntegerField(null=True, blank=True, verbose_name='슬라이스 장수')
    npy_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='.npy 경로')
    thumbnail_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='썸네일 경로')
    is_selected = models.BooleanField(default=False, verbose_name='학습 사용 여부')
    study = models.ForeignKey(
        DicomStudy,
        to_field='study_uid',
        db_column='study_uid',
        on_delete=models.CASCADE,
        verbose_name='Study UID'
    )

    class Meta:
        db_table = 'dicom_series'
        verbose_name = 'DICOM Series'
        verbose_name_plural = 'DICOM Series'

    def __str__(self):
        return self.series_uid


class AiPrediction(models.Model):
    prediction_id = models.BigAutoField(primary_key=True, verbose_name='예측 ID')
    risk_score = models.FloatField(null=True, blank=True, verbose_name='위험도 점수')
    survival_prob_1yr = models.FloatField(null=True, blank=True, verbose_name='1년 생존확률')
    survival_prob_3yr = models.FloatField(null=True, blank=True, verbose_name='3년 생존확률')
    gradcam_path = models.CharField(max_length=500, null=True, blank=True, verbose_name='Grad-CAM 경로')
    input_clinical_features = models.JSONField(null=True, blank=True, verbose_name='임상 특성 스냅샷')
    input_gene_data = models.JSONField(null=True, blank=True, verbose_name='유전자 데이터 스냅샷')
    analyzed_at = models.DateTimeField(auto_now_add=True, verbose_name='분석 시각')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id',
        verbose_name='환자'
    )
    series = models.ForeignKey(
        DicomSeries,
        to_field='series_uid',
        db_column='series_uid',
        on_delete=models.CASCADE,
        verbose_name='시리즈 UID'
    )

    class Meta:
        db_table = 'ai_predictions'
        verbose_name = 'AI 예측'
        verbose_name_plural = 'AI 예측'

    def __str__(self):
        return f"Prediction {self.prediction_id}"


class Announcement(models.Model):
    announcement_id = models.BigAutoField(primary_key=True, verbose_name='공지 ID')
    title = models.CharField(max_length=200, verbose_name='제목')
    content = models.TextField(verbose_name='내용')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='작성일')
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='user_id',
        verbose_name='작성자'
    )

    class Meta:
        db_table = 'announcements'
        verbose_name = '공지사항'
        verbose_name_plural = '공지사항'

    def __str__(self):
        return self.title


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', '예약됨'),
        ('completed', '완료'),
        ('cancelled', '취소'),
    ]

    appointment_id = models.AutoField(primary_key=True, verbose_name='예약 ID')
    appointment_date = models.DateField(verbose_name='예약 날짜')
    appointment_time = models.TimeField(verbose_name='예약 시간')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='scheduled',
        verbose_name='예약 상태'
    )
    notes = models.TextField(null=True, blank=True, verbose_name='메모')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        db_column='patient_id',
        verbose_name='환자'
    )
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        db_column='doctor_id',
        verbose_name='담당 의사'
    )

    class Meta:
        db_table = 'appointments'
        verbose_name = '예약'
        verbose_name_plural = '예약'

    def __str__(self):
        return f"Appointment {self.appointment_id} - {self.appointment_date} {self.appointment_time}"