"""                                                                     
CSV 파일을 Django ORM을 사용하여 데이터베이스에 삽입하는 스크립트

사용법:
    python manage.py shell -c "from HealthcareMap.csvTodb import main; main()"
"""

import os
import sys
import django
import csv
from decimal import Decimal

# 프로젝트 루트 디렉토리를 Python 경로에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'reactproject.settings')
django.setup()

from django.db import transaction, IntegrityError
from HealthcareMap.models import (
    DepartmentOfTreatment,
    Hospital,
    Clinic,
    Pharmacy,
)


# 표준 진료과목 데이터
STANDARD_DEPARTMENTS = {
    '101': '내과',
    '102': '신경과',
    '103': '정신건강의학과',
    '104': '외과',
    '105': '정형외과',
    '106': '신경외과',
    '107': '흉부외과',
    '108': '성형외과',
    '109': '마취통증의학과',
    '110': '산부인과',
    '111': '소아청소년과',
    '112': '안과',
    '113': '이비인후과',
    '114': '피부과',
    '115': '비뇨의학과',
    '116': '영상의학과',
    '117': '방사선종양학과',
    '118': '병리과',
    '119': '진단검사의학과',
    '120': '결핵과',
    '121': '재활의학과',
    '122': '핵의학과',
    '123': '가정의학과',
    '124': '응급의학과',
    '125': '직업환경의학과',
    '126': '예방의학과',
    '127': '치과',
    '128': '구강악안면외과',
    '129': '치과보철과',
    '130': '치과교정과',
    '131': '소아치과',
    '132': '치주과',
    '133': '치과보존과',
    '134': '구강내과',
    '135': '영상치의학과',
    '136': '구강병리과',
    '137': '예방치과',
    '138': '통합치의학과',
    '200': '한방내과',
    '201': '한방부인과',
    '202': '한방소아과',
    '203': '한방안·이비인후·피부과',
    '204': '한방신경정신과',
    '205': '침구과',
    '206': '한방재활의학과',
    '207': '사상체질과',
    '208': '한방응급과',
}

# CSV의 진료과목명을 표준 진료과목명으로 매핑
DEPARTMENT_NAME_MAPPING = {
    '심장혈관흉부외과': '흉부외과',
}


def is_empty(value):
    """값이 비어있는지 확인"""
    return value is None or value == '' or value == 'nan'


def normalize_department_names(dept_names_str):
    """
    CSV의 진료과목명을 표준 진료과목명으로 변환

    Args:
        dept_names_str: 쉼표로 구분된 진료과목명 문자열

    Returns:
        str: 표준 진료과목명으로 변환된 문자열
    """
    if is_empty(dept_names_str):
        return None

    names = [name.strip() for name in str(dept_names_str).split(',')]
    normalized_names = []

    for name in names:
        # 매핑 테이블에서 변환
        normalized_name = DEPARTMENT_NAME_MAPPING.get(name, name)
        if normalized_name:
            normalized_names.append(normalized_name)

    return ', '.join(normalized_names) if normalized_names else None


def import_hospitals():
    """병원 데이터 삽입 (hospital_converted.csv)"""
    print("\n=== 병원 데이터 삽입 시작 ===")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(base_dir, "hospital_converted.csv")

    print(f"CSV 파일 경로: {csv_file}")
    print(f"파일 존재 여부: {os.path.exists(csv_file)}")

    created_count = 0
    skipped_count = 0
    duplicate_count = 0
    error_count = 0

    BATCH_SIZE = 50  # 배치 크기
    batch_data = []

    print("CSV 파일 읽기 시작...")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, 1):  # 1부터 시작

            # 10개마다 진행 상황 표시
            if idx % 10 == 0:
                print(f"  {idx}행 읽는 중... (배치: {len(batch_data)}개, 생성: {created_count})")

            try:
                # 폐업일자가 있으면 건너뛰기
                if not is_empty(row['폐업일자']):
                    skipped_count += 1
                    continue

                # 필수 필드 검증 (이름, 주소, 전화번호, 좌표 x, 좌표 y)
                if (is_empty(row['사업장명']) or
                    is_empty(row['도로명전체주소']) or
                    is_empty(row['소재지전화']) or
                    is_empty(row['좌표(x)']) or
                    is_empty(row['좌표(y)'])):
                    skipped_count += 1
                    continue

                # Hospital 객체 생성
                hospital = Hospital(
                    phone=row['소재지전화'],
                    address=row['도로명전체주소'],
                    name=row['사업장명'],
                    business_type=row['업태구분명'] if not is_empty(row['업태구분명']) else None,
                    coordinate_x=Decimal(str(row['좌표(x)'])),
                    coordinate_y=Decimal(str(row['좌표(y)'])),
                )

                batch_data.append(hospital)

                # 배치 크기에 도달하면 저장
                if len(batch_data) >= BATCH_SIZE:
                    for h in batch_data:
                        try:
                            with transaction.atomic():
                                h.save()
                                created_count += 1
                        except IntegrityError:
                            # 중복 데이터는 건너뛰기
                            duplicate_count += 1
                        except Exception as e:
                            error_count += 1
                            print(f"  저장 오류: {e}")

                    print(f"  [{idx}행 처리] 생성: {created_count}, 중복: {duplicate_count}, 건너뜀: {skipped_count}")
                    batch_data = []

            except Exception as e:
                error_count += 1
                print(f"오류 (행 {idx}): {e}")

    # 남은 데이터 저장
    if batch_data:
        for h in batch_data:
            try:
                with transaction.atomic():
                    h.save()
                    created_count += 1
            except IntegrityError:
                duplicate_count += 1
            except Exception as e:
                error_count += 1
                print(f"  저장 오류: {e}")

    print(f"\n병원 삽입 완료:")
    print(f"  생성: {created_count}개")
    print(f"  중복: {duplicate_count}개")
    print(f"  건너뜀: {skipped_count}개")
    print(f"  오류: {error_count}개")
    return created_count


def import_clinics():
    """의원 데이터 삽입 (host2_converted.csv)"""
    print("\n=== 의원 데이터 삽입 시작 ===")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(base_dir, "host2_converted.csv")

    created_count = 0
    skipped_count = 0
    duplicate_count = 0
    error_count = 0

    BATCH_SIZE = 50  # 배치 크기
    batch_data = []

    print("CSV 파일 읽기 시작...")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, 1):  # 1부터 시작

            # 10개마다 진행 상황 표시
            if idx % 10 == 0:
                print(f"  {idx}행 읽는 중... (배치: {len(batch_data)}개, 생성: {created_count})")

            try:
                # 폐업일자가 있으면 건너뛰기
                if not is_empty(row['폐업일자']):
                    skipped_count += 1
                    continue

                # 필수 필드 검증 (이름, 주소, 전화번호, 좌표 x, 좌표 y)
                if (is_empty(row['사업장명']) or
                    is_empty(row['도로명전체주소']) or
                    is_empty(row['소재지전화']) or
                    is_empty(row['좌표(x)']) or
                    is_empty(row['좌표(y)'])):
                    skipped_count += 1
                    continue

                # Clinic 객체 생성
                clinic = Clinic(
                    phone=row['소재지전화'],
                    address=row['도로명전체주소'],
                    name=row['사업장명'],
                    business_type=row['업태구분명'] if not is_empty(row['업태구분명']) else None,
                    coordinate_x=Decimal(str(row['좌표(x)'])),
                    coordinate_y=Decimal(str(row['좌표(y)'])),
                )

                batch_data.append(clinic)

                # 배치 크기에 도달하면 저장
                if len(batch_data) >= BATCH_SIZE:
                    for c in batch_data:
                        try:
                            with transaction.atomic():
                                c.save()
                                created_count += 1
                        except IntegrityError:
                            duplicate_count += 1
                        except Exception as e:
                            error_count += 1
                            print(f"  저장 오류: {e}")

                    print(f"  [{idx}행 처리] 생성: {created_count}, 중복: {duplicate_count}, 건너뜀: {skipped_count}")
                    batch_data = []

            except Exception as e:
                error_count += 1
                print(f"오류 (행 {idx}): {e}")

    # 남은 데이터 저장
    if batch_data:
        for c in batch_data:
            try:
                with transaction.atomic():
                    c.save()
                    created_count += 1
            except IntegrityError:
                duplicate_count += 1
            except Exception as e:
                error_count += 1
                print(f"  저장 오류: {e}")

    print(f"\n의원 삽입 완료:")
    print(f"  생성: {created_count}개")
    print(f"  중복: {duplicate_count}개")
    print(f"  건너뜀: {skipped_count}개")
    print(f"  오류: {error_count}개")
    return created_count


def import_pharmacies():
    """약국 데이터 삽입 (pha_data.csv)"""
    print("\n=== 약국 데이터 삽입 시작 ===")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(base_dir, "pha_data.csv")

    created_count = 0
    skipped_count = 0
    duplicate_count = 0
    error_count = 0

    BATCH_SIZE = 50  # 배치 크기
    batch_data = []

    print("CSV 파일 읽기 시작...")

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for idx, row in enumerate(reader, 1):  # 1부터 시작

            # 10개마다 진행 상황 표시
            if idx % 10 == 0:
                print(f"  {idx}행 읽는 중... (배치: {len(batch_data)}개, 생성: {created_count})")

            try:
                # 필수 필드 검증 (이름, 주소, 전화번호, 좌표 x, 좌표 y)
                if (is_empty(row['요양기관명']) or
                    is_empty(row['주소']) or
                    is_empty(row['전화번호']) or
                    is_empty(row['좌표(x)']) or
                    is_empty(row['좌표(y)'])):
                    skipped_count += 1
                    continue

                # Pharmacy 객체 생성
                pharmacy = Pharmacy(
                    name=row['요양기관명'],
                    address=row['주소'],
                    phone=row['전화번호'],
                    coordinate_x=Decimal(str(row['좌표(x)'])),
                    coordinate_y=Decimal(str(row['좌표(y)'])),
                )

                batch_data.append(pharmacy)

                # 배치 크기에 도달하면 저장
                if len(batch_data) >= BATCH_SIZE:
                    for p in batch_data:
                        try:
                            with transaction.atomic():
                                p.save()
                                created_count += 1
                        except IntegrityError:
                            duplicate_count += 1
                        except Exception as e:
                            error_count += 1
                            print(f"  저장 오류: {e}")

                    print(f"  [{idx}행 처리] 생성: {created_count}, 중복: {duplicate_count}, 건너뜀: {skipped_count}")
                    batch_data = []

            except Exception as e:
                error_count += 1
                print(f"오류 (행 {idx}): {e}")

    # 남은 데이터 저장
    if batch_data:
        for p in batch_data:
            try:
                with transaction.atomic():
                    p.save()
                    created_count += 1
            except IntegrityError:
                duplicate_count += 1
            except Exception as e:
                error_count += 1
                print(f"  저장 오류: {e}")

    print(f"\n약국 삽입 완료:")
    print(f"  생성: {created_count}개")
    print(f"  중복: {duplicate_count}개")
    print(f"  건너뜀: {skipped_count}개")
    print(f"  오류: {error_count}개")
    return created_count


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("CSV 데이터를 데이터베이스로 가져오기")
    print("=" * 60)

    try:
        # 진료과목은 이미 삽입 완료됨
        dept_count = 48

        # 병원 데이터 삽입
        hospital_count = import_hospitals()

        # 의원 데이터 삽입
        clinic_count = import_clinics()

        # 약국 데이터 삽입
        pharmacy_count = import_pharmacies()

        print("\n" + "=" * 60)
        print("데이터 가져오기 완료!")
        print("=" * 60)
        print(f"진료과목: {dept_count}개")
        print(f"병원: {hospital_count}개")
        print(f"의원: {clinic_count}개")
        print(f"약국: {pharmacy_count}개")
        print("=" * 60)

    except Exception as e:
        print(f"\n치명적 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
