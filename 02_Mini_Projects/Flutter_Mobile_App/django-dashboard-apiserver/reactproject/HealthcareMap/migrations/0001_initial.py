# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DepartmentOfTreatment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='진료과목 코드 (예: 101, 102 등)', max_length=10, unique=True, verbose_name='진료과목내용')),
                ('name', models.CharField(help_text='진료과목 명칭 (예: 내과, 신경과 등)', max_length=100, verbose_name='진료과목내용명')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일시')),
            ],
            options={
                'verbose_name': '진료과목',
                'verbose_name_plural': '진료과목',
                'db_table': 'department_of_treatment',
                'ordering': ['code'],
            },
        ),
        migrations.CreateModel(
            name='Hospital',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='소재지전화')),
                ('address', models.CharField(max_length=500, verbose_name='도로명전체주소')),
                ('name', models.CharField(max_length=200, verbose_name='사업장명')),
                ('business_type', models.CharField(blank=True, max_length=100, null=True, verbose_name='업태구분명')),
                ('coordinate_x', models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True, verbose_name='좌표(x)')),
                ('coordinate_y', models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True, verbose_name='좌표(y)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일시')),
            ],
            options={
                'verbose_name': '병원',
                'verbose_name_plural': '병원',
                'db_table': 'hospital',
            },
        ),
        migrations.CreateModel(
            name='Clinic',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='소재지전화')),
                ('address', models.CharField(max_length=500, verbose_name='도로명전체주소')),
                ('name', models.CharField(max_length=200, verbose_name='사업장명')),
                ('business_type', models.CharField(blank=True, max_length=100, null=True, verbose_name='업태구분명')),
                ('coordinate_x', models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True, verbose_name='좌표(x)')),
                ('coordinate_y', models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True, verbose_name='좌표(y)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일시')),
            ],
            options={
                'verbose_name': '의원',
                'verbose_name_plural': '의원',
                'db_table': 'clinic',
            },
        ),
        migrations.CreateModel(
            name='Pharmacy',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='요양기관명')),
                ('address', models.CharField(max_length=500, verbose_name='주소')),
                ('phone', models.CharField(blank=True, max_length=20, null=True, verbose_name='전화번호')),
                ('coordinate_x', models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True, verbose_name='좌표(x)')),
                ('coordinate_y', models.DecimalField(blank=True, decimal_places=8, max_digits=12, null=True, verbose_name='좌표(y)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='수정일시')),
            ],
            options={
                'verbose_name': '약국',
                'verbose_name_plural': '약국',
                'db_table': 'pharmacy',
            },
        ),
        migrations.CreateModel(
            name='DotHospNm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HealthcareMap.departmentoftreatment', verbose_name='진료과목')),
                ('hospital', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HealthcareMap.hospital', verbose_name='병원')),
            ],
            options={
                'verbose_name': '진료과목-병원',
                'verbose_name_plural': '진료과목-병원',
                'db_table': 'dot_hosp_nm',
                'unique_together': {('department', 'hospital')},
            },
        ),
        migrations.CreateModel(
            name='DotClinicNm',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='생성일시')),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HealthcareMap.departmentoftreatment', verbose_name='진료과목')),
                ('clinic', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='HealthcareMap.clinic', verbose_name='의원')),
            ],
            options={
                'verbose_name': '진료과목-의원',
                'verbose_name_plural': '진료과목-의원',
                'db_table': 'dot_clinic_nm',
                'unique_together': {('department', 'clinic')},
            },
        ),
        migrations.AddField(
            model_name='hospital',
            name='departments',
            field=models.ManyToManyField(related_name='hospitals', through='HealthcareMap.DotHospNm', to='HealthcareMap.departmentoftreatment', verbose_name='진료과목'),
        ),
        migrations.AddField(
            model_name='clinic',
            name='departments',
            field=models.ManyToManyField(related_name='clinics', through='HealthcareMap.DotClinicNm', to='HealthcareMap.departmentoftreatment', verbose_name='진료과목'),
        ),
    ]
