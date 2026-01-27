# """
# 병원/의원 생성 시 진료과목 자동 매핑
# """
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Hospital, Clinic, DepartmentOfTreatment, DotHospNm, DotClinicNm


# @receiver(post_save, sender=Hospital)
# def create_hospital_departments(sender, instance, created, **kwargs):
#     """
#     병원이 생성될 때 진료과목을 자동으로 매핑

#     Note: 이 시그널은 Hospital 객체에 department_names_temp 속성이 설정되어 있을 때만 작동합니다.
#     CSV 데이터 import 시 다음과 같이 사용:

#     hospital = Hospital(name=..., address=...)
#     hospital.department_names_temp = "내과, 신경과, 외과"  # CSV의 진료과목내용명
#     hospital.save()
#     """
#     # 전체를 try-except로 감싸서 트랜잭션 오류 방지
#     try:
#         if not created:
#             return

#         # 임시 속성에서 진료과목명 리스트 가져오기
#         dept_names_str = getattr(instance, 'department_names_temp', None)
#         if not dept_names_str:
#             return

#         # 쉼표로 분리하여 진료과목명 리스트 생성
#         dept_names = [name.strip() for name in str(dept_names_str).split(',')]

#         # 각 진료과목명에 대해 DepartmentOfTreatment에서 찾아서 매핑
#         for dept_name in dept_names:
#             if not dept_name:
#                 continue

#             try:
#                 department = DepartmentOfTreatment.objects.get(name=dept_name)
#                 # 중복 방지를 위해 get_or_create 사용
#                 DotHospNm.objects.get_or_create(
#                     department=department,
#                     hospital=instance
#                 )
#             except DepartmentOfTreatment.DoesNotExist:
#                 print(f"경고: 진료과목 '{dept_name}'을(를) 찾을 수 없습니다. (병원: {instance.name})")
#             except Exception as e:
#                 print(f"오류: 병원 '{instance.name}'의 진료과목 '{dept_name}' 매핑 중 오류 발생: {e}")
#     except Exception as e:
#         print(f"치명적 오류: 병원 '{instance.name}'의 시그널 처리 중 오류 발생: {e}")


# @receiver(post_save, sender=Clinic)
# def create_clinic_departments(sender, instance, created, **kwargs):
#     """
#     의원이 생성될 때 진료과목을 자동으로 매핑

#     Note: 이 시그널은 Clinic 객체에 department_names_temp 속성이 설정되어 있을 때만 작동합니다.
#     CSV 데이터 import 시 다음과 같이 사용:

#     clinic = Clinic(name=..., address=...)
#     clinic.department_names_temp = "내과, 신경과, 외과"  # CSV의 진료과목내용명
#     clinic.save()
#     """
#     # 전체를 try-except로 감싸서 트랜잭션 오류 방지
#     try:
#         if not created:
#             return

#         # 임시 속성에서 진료과목명 리스트 가져오기
#         dept_names_str = getattr(instance, 'department_names_temp', None)
#         if not dept_names_str:
#             return

#         # 쉼표로 분리하여 진료과목명 리스트 생성
#         dept_names = [name.strip() for name in str(dept_names_str).split(',')]

#         # 각 진료과목명에 대해 DepartmentOfTreatment에서 찾아서 매핑
#         for dept_name in dept_names:
#             if not dept_name:
#                 continue

#             try:
#                 department = DepartmentOfTreatment.objects.get(name=dept_name)
#                 # 중복 방지를 위해 get_or_create 사용
#                 DotClinicNm.objects.get_or_create(
#                     department=department,
#                     clinic=instance
#                 )
#             except DepartmentOfTreatment.DoesNotExist:
#                 print(f"경고: 진료과목 '{dept_name}'을(를) 찾을 수 없습니다. (의원: {instance.name})")
#             except Exception as e:
#                 print(f"오류: 의원 '{instance.name}'의 진료과목 '{dept_name}' 매핑 중 오류 발생: {e}")
#     except Exception as e:
#         print(f"치명적 오류: 의원 '{instance.name}'의 시그널 처리 중 오류 발생: {e}")
