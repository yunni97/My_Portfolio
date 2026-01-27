# 병원/의원 insert 시 진료과목 자동 매핑
# Django signals를 사용하여 처리 (signals.py 참조)

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('HealthcareMap', '0001_initial'),
    ]

    operations = [
        # Django signals를 사용하여 병원/의원 생성 시 진료과목 자동 매핑
        # HealthcareMap/signals.py 파일 참조
        #
        # 사용 예시:
        # hospital = Hospital(name="병원명", address="주소", ...)
        # hospital.department_names_temp = "내과, 신경과, 외과"  # CSV의 진료과목내용명
        # hospital.save()  # 저장 시 signal이 자동으로 진료과목 매핑
    ]
