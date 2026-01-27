from django.db import models

from django.contrib.auth.hashers import make_password, check_password





class Announcements(models.Model):

    announcements_id = models.BigIntegerField(primary_key=True)

    title = models.CharField(max_length=200)

    content = models.TextField()

    created_at = models.DateTimeField()

    updated_at = models.DateTimeField(blank=True, null=True)

    user = models.ForeignKey('AuthUsers', models.DO_NOTHING, blank=True, null=True)



class Meta:

    managed = False

    db_table = 'announcements'

    verbose_name = '공지사항'

    verbose_name_plural = '공지사항'

    verbose_name = '공지사항'

    verbose_name_plural = '공지사항'





class AuthUsers(models.Model):

    user_id = models.IntegerField(primary_key=True)

    id = models.CharField(max_length=150, blank=True, null=True)

    password = models.CharField(max_length=255)

    last_login = models.DateTimeField(blank=True, null=True)

    first_name = models.CharField(max_length=150)

    last_name = models.CharField(max_length=150)

    email = models.CharField(max_length=254)

    is_staff = models.IntegerField()

    is_active = models.IntegerField()

    date_joined = models.DateTimeField()



class Meta:

    managed = False

    db_table = 'auth_users'

    verbose_name = '인증 사용자'

    verbose_name_plural = '인증 사용자'





class BloodResults(models.Model):

    blood_id = models.IntegerField(primary_key=True)

    ast = models.DecimalField(db_column='AST', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    alt = models.DecimalField(db_column='ALT', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    alp = models.DecimalField(db_column='ALP', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    ggt = models.DecimalField(db_column='GGT', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    bilirubin = models.DecimalField(db_column='Bilirubin', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    albumin = models.DecimalField(db_column='Albumin', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    inr = models.DecimalField(db_column='INR', max_digits=10, decimal_places=3, blank=True, null=True)  # Field name made lowercase.

    platelet = models.DecimalField(db_column='Platelet', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    afp = models.DecimalField(db_column='AFP', max_digits=10, decimal_places=2, blank=True, null=True)  # Field name made lowercase.

    taken_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True)

    record = models.ForeignKey('MedicalRecords', models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'blood_results'

    verbose_name = '혈액 검사'

    verbose_name_plural = '혈액 검사'

    verbose_name = '혈액 검사'

    verbose_name_plural = '혈액 검사'





class Departments(models.Model):

    department_id = models.AutoField(primary_key=True)

    department_code = models.CharField(max_length=10, blank=True, null=True)

    department = models.CharField(max_length=50, blank=True, null=True)



class Meta:

    managed = False

    db_table = 'departments'

    verbose_name = '부서'

    verbose_name_plural = '부서'

    verbose_name = '부서'

    verbose_name_plural = '부서'





class DeseaseManage(models.Model):

    desease_manage_id = models.BigIntegerField(primary_key=True)

    diagnosis_date = models.DateField(blank=True, null=True)

    bclc_stage = models.CharField(max_length=10, blank=True, null=True)

    tumor_size = models.FloatField(blank=True, null=True)

    tumor_count = models.IntegerField(blank=True, null=True)

    vascular_invasion = models.IntegerField()

    child_pugh = models.CharField(max_length=1, blank=True, null=True)

    afp_initial = models.FloatField(blank=True, null=True)

    afp_current = models.FloatField(blank=True, null=True)

    treatment_type = models.CharField(max_length=50, blank=True, null=True)

    treatment_start_date = models.DateField(blank=True, null=True)

    recurrence_risk = models.CharField(max_length=10, blank=True, null=True)

    doctor = models.ForeignKey('DoctorProfiles', models.DO_NOTHING, blank=True, null=True)

    patient = models.ForeignKey('Patients', models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'desease_manage'

    verbose_name = '질병 관리'

    verbose_name_plural = '질병 관리'





class DoctorProfiles(models.Model):

    doctor_id = models.CharField(primary_key=True, max_length=50)

    password = models.CharField(max_length=128, blank=True, null=True)  # 해시된 비밀번호 저장

    name = models.CharField(max_length=50)

    sex = models.CharField(max_length=6)

    phone = models.CharField(max_length=11, blank=True, null=True)

    email = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=9)

    profile_image = models.TextField(blank=True, null=True)

    license_number = models.CharField(max_length=50, blank=True, null=True)

    position = models.CharField(max_length=50, blank=True, null=True)

    last_login = models.DateTimeField(blank=True, null=True)  # 마지막 로그인 시간

    created_at = models.DateTimeField()

    updated_at = models.DateTimeField(blank=True, null=True)

    departments = models.ForeignKey(Departments, models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'doctor_profiles'

    verbose_name = '의사 프로필'

    verbose_name_plural = '의사 프로필'

    verbose_name = '의사 프로필'

    verbose_name_plural = '의사 프로필'



def __str__(self):

    return f"{self.name} ({self.doctor_id})"



def set_password(self, raw_password):

    """비밀번호를 해시하여 저장"""

    self.password = make_password(raw_password)



def check_password(self, raw_password):

    """비밀번호 확인"""

    if not self.password:

        return False

    return check_password(raw_password, self.password)





class DrugForm(models.Model):

    form_id = models.AutoField(primary_key=True)

    form = models.CharField(max_length=30, blank=True, null=True)



class Meta:

    managed = False

    db_table = 'drug_form'

    verbose_name = '약물 형태'

    verbose_name_plural = '약물 형태'

    verbose_name = '약물 형태'

    verbose_name_plural = '약물 형태'





class DrugFrequency(models.Model):

    frequency_id = models.AutoField(primary_key=True)

    frequency = models.CharField(max_length=10, blank=True, null=True)



class Meta:

    managed = False

    db_table = 'drug_frequency'

    verbose_name = '투약 빈도'

    verbose_name_plural = '투약 빈도'

    verbose_name = '투약 빈도'

    verbose_name_plural = '투약 빈도'





class DrugRoute(models.Model):

    route_id = models.AutoField(primary_key=True)

    route = models.CharField(max_length=10, blank=True, null=True)



class Meta:

    managed = False

    db_table = 'drug_route'

    verbose_name = '투약 경로'

    verbose_name_plural = '투약 경로'

    verbose_name = '투약 경로'

    verbose_name_plural = '투약 경로'





class Drugs(models.Model):

    drug_id = models.AutoField(primary_key=True)

    name_kr = models.TextField()

    name_eng = models.TextField()

    drug_category = models.CharField(max_length=100)

    dosage = models.TextField()

    instructions = models.TextField(blank=True, null=True)

    efficacy = models.TextField()

    precautions = models.TextField()

    common_side_effects = models.TextField()

    serious_side_effects = models.TextField()

    contraindications = models.TextField()

    smiles = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField()

    updated_at = models.DateTimeField()



class Meta:

    managed = False

    db_table = 'drugs'

    verbose_name = '약물 정보'

    verbose_name_plural = '약물 정보'

    verbose_name = '약물 정보'

    verbose_name_plural = '약물 정보'





class MedicalDiagnosis(models.Model):

    diagnosis_id = models.IntegerField(primary_key=True)

    icd_code = models.CharField(max_length=10, blank=True, null=True)

    diagnosis_name = models.CharField(max_length=255, blank=True, null=True)

    is_primary = models.IntegerField(blank=True, null=True)

    record = models.ForeignKey('MedicalRecords', models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'medical_diagnosis'

    verbose_name = '진단'

    verbose_name_plural = '진단'

    verbose_name = '진단'

    verbose_name_plural = '진단'





class MedicalRecords(models.Model):

    record_id = models.IntegerField(primary_key=True)

    visit_date = models.DateTimeField()

    chief_complatint = models.CharField(max_length=255, blank=True, null=True)

    subjective_note = models.TextField(blank=True, null=True)

    objective_note = models.TextField(blank=True, null=True)

    assessment = models.TextField(blank=True, null=True)

    plan = models.TextField(blank=True, null=True)

    doctor = models.ForeignKey(DoctorProfiles, models.DO_NOTHING, blank=True, null=True)

    patient = models.ForeignKey('Patients', models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'medical_records'

    verbose_name = '진료 기록'

    verbose_name_plural = '진료 기록'

    verbose_name = '진료 기록'

    verbose_name_plural = '진료 기록'





class MedicalSeries(models.Model):

    series_id = models.IntegerField(primary_key=True)

    slice_count = models.IntegerField(blank=True, null=True)

    thumbnail_path = models.CharField(max_length=500, blank=True, null=True)

    folder_path = models.CharField(max_length=500, blank=True, null=True)

    study = models.ForeignKey('MedicalStudy', models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'medical_series'

    verbose_name = '영상 시리즈'

    verbose_name_plural = '영상 시리즈'

    



class MedicalStudy(models.Model):

    study_id = models.AutoField(primary_key=True)

    modality = models.CharField(max_length=3, blank=True, null=True)

    instance_uid = models.CharField(max_length=100, blank=True, null=True)

    body_part = models.CharField(max_length=50, blank=True, null=True)

    study_date = models.DateTimeField(blank=True, null=True)

    description = models.CharField(max_length=200, blank=True, null=True)

    indication = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True)

    record = models.ForeignKey(MedicalRecords, models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'medical_study'

    verbose_name = '영상 검사'

    verbose_name_plural = '영상 검사'

    verbose_name = '영상 검사'

    verbose_name_plural = '영상 검사'

    



class MedicalVitals(models.Model):

    vital_id = models.IntegerField(primary_key=True)

    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    bp_systolic = models.IntegerField(blank=True, null=True)

    bp_diastolic = models.IntegerField(blank=True, null=True)

    heart_rate = models.IntegerField(blank=True, null=True)

    resp_rate = models.IntegerField(blank=True, null=True)

    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)

    oxygen_saturation = models.IntegerField(blank=True, null=True)

    measured_at = models.IntegerField(blank=True, null=True)

    record = models.ForeignKey(MedicalRecords, models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'medical_vitals'

    verbose_name = '활력 징후'

    verbose_name_plural = '활력 징후'

    verbose_name = '활력 징후'

    verbose_name_plural = '활력 징후'





class NurseProfiles(models.Model):

    nurse_id = models.IntegerField(primary_key=True)

    name = models.CharField(max_length=50, blank=True, null=True)

    sex = models.CharField(max_length=6, blank=True, null=True)

    phone = models.CharField(max_length=11, blank=True, null=True)

    email = models.CharField(max_length=100, blank=True, null=True)

    status = models.CharField(max_length=9, blank=True, null=True)

    profile_image = models.TextField(blank=True, null=True)

    license_number = models.CharField(max_length=50, blank=True, null=True)

    shift_type = models.CharField(max_length=7, blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True)

    updated_at = models.DateTimeField(blank=True, null=True)

    departments = models.ForeignKey(Departments, models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'nurse_profiles'

    verbose_name = '간호사 프로필'

    verbose_name_plural = '간호사 프로필'

    verbose_name = '간호사 프로필'

    verbose_name_plural = '간호사 프로필'





class NursingNotes(models.Model):

    note_id = models.IntegerField(primary_key=True)

    note_type = models.TextField(blank=True, null=True)

    subjective_note = models.TextField(blank=True, null=True)

    objective_note = models.TextField(blank=True, null=True)

    assessment = models.TextField(blank=True, null=True)

    plan = models.TextField(blank=True, null=True)

    intervention = models.TextField(blank=True, null=True)

    abnormal_flag = models.CharField(max_length=8, blank=True, null=True)

    next_action = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True)

    nurse = models.ForeignKey(NurseProfiles, models.DO_NOTHING, blank=True, null=True)

    record = models.ForeignKey(MedicalRecords, models.DO_NOTHING, blank=True, null=True)



class Meta:

    managed = False

    db_table = 'nursing_notes'

    verbose_name = '간호 기록'

    verbose_name_plural = '간호 기록'

    verbose_name = '간호 기록'

    verbose_name_plural = '간호 기록'




class Patients(models.Model):

    patient_id = models.BigIntegerField(primary_key=True)

    name = models.CharField(max_length=100)

    birth_date = models.DateField()

    sex = models.CharField(max_length=6)

    resident_number = models.CharField(max_length=13, blank=True, null=True)

    phone = models.CharField(max_length=11)

    address = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField()

    updated_at = models.DateTimeField()



class Meta:

    managed = False

    db_table = 'patients'

    verbose_name = '환자'

    verbose_name_plural = '환자'

    verbose_name = '환자'

    verbose_name_plural = '환자'





class PrescriptionDrug(models.Model):

    pd_id = models.IntegerField(primary_key=True)

    prescription = models.ForeignKey('Prescriptions', models.DO_NOTHING)

    drug = models.ForeignKey(Drugs, models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'prescription_drug'

    verbose_name = '처방 약물'

    verbose_name_plural = '처방 약물'





class Prescriptions(models.Model):

    prescription_id = models.IntegerField(primary_key=True)

    status = models.CharField(max_length=8, blank=True, null=True)

    medication_name = models.CharField(max_length=100, blank=True, null=True)

    dosage = models.CharField(max_length=50, blank=True, null=True)

    duration = models.CharField(max_length=50, blank=True, null=True)

    quantity = models.IntegerField(blank=True, null=True)

    due_date = models.DateTimeField()

    comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(blank=True, null=True)

    updated_at = models.DateTimeField(blank=True, null=True)

    frequency = models.ForeignKey(DrugFrequency, models.DO_NOTHING)

    form = models.ForeignKey(DrugForm, models.DO_NOTHING)

    route = models.ForeignKey(DrugRoute, models.DO_NOTHING)

    record = models.ForeignKey(MedicalRecords, models.DO_NOTHING)



class Meta:

    managed = False

    db_table = 'prescriptions'

    verbose_name = '처방전'

    verbose_name_plural = '처방전'

    verbose_name = '처방전'

    verbose_name_plural = '처방전'