from django.db import models


class DepartmentOfTreatment(models.Model):
    """진료과목 모델"""
    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name='진료과목내용',
        help_text='진료과목 코드 (예: 101, 102 등)'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='진료과목내용명',
        help_text='진료과목 명칭 (예: 내과, 신경과 등)'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        db_table = 'department_of_treatment'
        verbose_name = '진료과목'
        verbose_name_plural = '진료과목'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Hospital(models.Model):
    """병원 모델 (hospital_converted.csv)"""
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='소재지전화')
    address = models.CharField(max_length=500, verbose_name='도로명전체주소')
    name = models.CharField(max_length=200, verbose_name='사업장명')
    business_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='업태구분명')
    coordinate_x = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name='좌표(x)')
    coordinate_y = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name='좌표(y)')
    departments = models.ManyToManyField(
        DepartmentOfTreatment,
        through='DotHospNm',
        related_name='hospitals',
        verbose_name='진료과목'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        db_table = 'hospital'
        verbose_name = '병원'
        verbose_name_plural = '병원'
        unique_together = [['name', 'address']]

    def __str__(self):
        return self.name


class Clinic(models.Model):
    """의원 모델 (host2_converted.csv)"""
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='소재지전화')
    address = models.CharField(max_length=500, verbose_name='도로명전체주소')
    name = models.CharField(max_length=200, verbose_name='사업장명')
    business_type = models.CharField(max_length=100, blank=True, null=True, verbose_name='업태구분명')
    coordinate_x = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name='좌표(x)')
    coordinate_y = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name='좌표(y)')
    departments = models.ManyToManyField(
        DepartmentOfTreatment,
        through='DotClinicNm',
        related_name='clinics',
        verbose_name='진료과목'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        db_table = 'clinic'
        verbose_name = '의원'
        verbose_name_plural = '의원'
        unique_together = [['name', 'address']]

    def __str__(self):
        return self.name


class Pharmacy(models.Model):
    """약국 모델 (pha_data.csv)"""
    name = models.CharField(max_length=200, verbose_name='요양기관명')
    address = models.CharField(max_length=500, verbose_name='주소')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='전화번호')
    coordinate_x = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name='좌표(x)')
    coordinate_y = models.DecimalField(max_digits=12, decimal_places=8, blank=True, null=True, verbose_name='좌표(y)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일시')

    class Meta:
        db_table = 'pharmacy'
        verbose_name = '약국'
        verbose_name_plural = '약국'
        unique_together = [['name', 'address']]

    def __str__(self):
        return self.name


class DotHospNm(models.Model):
    """진료과목-병원 다대다 관계 테이블"""
    department = models.ForeignKey(
        DepartmentOfTreatment,
        on_delete=models.CASCADE,
        verbose_name='진료과목'
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        verbose_name='병원'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table = 'dot_hosp_nm'
        verbose_name = '진료과목-병원'
        verbose_name_plural = '진료과목-병원'
        unique_together = [['department', 'hospital']]

    def __str__(self):
        return f"{self.department.name} - {self.hospital.name}"


class DotClinicNm(models.Model):
    """진료과목-의원 다대다 관계 테이블"""
    department = models.ForeignKey(
        DepartmentOfTreatment,
        on_delete=models.CASCADE,
        verbose_name='진료과목'
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        verbose_name='의원'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table = 'dot_clinic_nm'
        verbose_name = '진료과목-의원'
        verbose_name_plural = '진료과목-의원'
        unique_together = [['department', 'clinic']]

    def __str__(self):
        return f"{self.department.name} - {self.clinic.name}"


class FavoriteHospital(models.Model):
    """병원 즐겨찾기 모델"""
    favorite_id = models.AutoField(primary_key=True, verbose_name='즐겨찾기 ID')
    patient = models.ForeignKey(
        'dashboard.DbrPatients',
        on_delete=models.CASCADE,
        related_name='favorite_hospitals',
        db_column='patient_id',
        verbose_name='환자 ID'
    )
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        db_column='hospital_id',
        verbose_name='병원 ID'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table = 'favorite_hospital'
        verbose_name = '병원 즐겨찾기'
        verbose_name_plural = '병원 즐겨찾기'
        unique_together = [['patient', 'hospital']]

    def __str__(self):
        return f"{self.patient} - {self.hospital.name}"


class FavoriteClinic(models.Model):
    """의원 즐겨찾기 모델"""
    favorite_id = models.AutoField(primary_key=True, verbose_name='즐겨찾기 ID')
    patient = models.ForeignKey(
        'dashboard.DbrPatients',
        on_delete=models.CASCADE,
        related_name='favorite_clinics',
        db_column='patient_id',
        verbose_name='환자 ID'
    )
    clinic = models.ForeignKey(
        Clinic,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        db_column='clinic_id',
        verbose_name='의원 ID'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일시')

    class Meta:
        db_table = 'favorite_clinic'
        verbose_name = '의원 즐겨찾기'
        verbose_name_plural = '의원 즐겨찾기'
        unique_together = [['patient', 'clinic']]

    def __str__(self):
        return f"{self.patient} - {self.clinic.name}"
