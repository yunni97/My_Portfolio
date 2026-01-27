"""
간단한 테스트 스크립트 - 병원 1개만 삽입해보기
"""

import os
import sys
import django

# Django 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reactproject.settings')
django.setup()

from HealthcareMap.models import Hospital, DepartmentOfTreatment

def test_simple_insert():
    """아주 간단한 삽입 테스트"""
    print("=== 간단한 삽입 테스트 시작 ===")

    # 1. 데이터베이스 연결 확인
    print("\n1. 데이터베이스 연결 확인...")
    try:
        count = Hospital.objects.count()
        print(f"   현재 병원 수: {count}개")
    except Exception as e:
        print(f"   오류: {e}")
        return

    # 2. 진료과목 확인
    print("\n2. 진료과목 확인...")
    try:
        dept_count = DepartmentOfTreatment.objects.count()
        print(f"   진료과목 수: {dept_count}개")

        # 첫 번째 진료과목 출력
        if dept_count > 0:
            first_dept = DepartmentOfTreatment.objects.first()
            print(f"   예시: {first_dept.code} - {first_dept.name}")
    except Exception as e:
        print(f"   오류: {e}")
        return

    # 3. 테스트 병원 1개 삽입
    print("\n3. 테스트 병원 삽입 시도...")
    try:
        hospital = Hospital(
            name="테스트병원",
            address="서울시 강남구 테스트로 123",
            phone="02-1234-5678",
            business_type="종합병원"
        )

        # 진료과목 설정
        hospital.department_names_temp = "내과, 외과"

        print(f"   병원 객체 생성: {hospital.name}")

        # 저장
        hospital.save()
        print(f"   ✓ 저장 성공! ID: {hospital.id}")

        # 진료과목 매핑 확인
        dept_relations = hospital.departments.all()
        print(f"   매핑된 진료과목 수: {dept_relations.count()}개")
        for dept in dept_relations:
            print(f"     - {dept.name}")

    except Exception as e:
        print(f"   ✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. 삽입 확인
    print("\n4. 삽입 확인...")
    try:
        new_count = Hospital.objects.count()
        print(f"   현재 병원 수: {new_count}개")

        # 방금 삽입한 병원 다시 조회
        test_hospital = Hospital.objects.filter(name="테스트병원").first()
        if test_hospital:
            print(f"   ✓ 조회 성공: {test_hospital.name} (ID: {test_hospital.id})")
        else:
            print(f"   ✗ 조회 실패")
    except Exception as e:
        print(f"   오류: {e}")

    print("\n=== 테스트 완료 ===")

if __name__ == "__main__":
    test_simple_insert()
