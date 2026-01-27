import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import (
    DoctorProfile, NurseProfile, Patient, MedicalRecord,
    MedicalVitals, ClinicalRecord, TestOrder, Appointment
)
from .utils import upload_dicom_to_orthanc
from django.contrib.auth.hashers import check_password, make_password
from .models import DoctorProfile
from rest_framework.views import APIView       # <- 이거 꼭 있어야 함
from django.conf import settings
import requests
import os
from requests.auth import HTTPBasicAuth
import shutil
from datetime import datetime

@api_view(['POST'])
def login(request):
    """
    의사 로그인 API

    Request Body:
    {
        "userId": "doctor_id",
        "password": "password"
    }

    Response:
    {
        "success": true,
        "message": "로그인 성공",
        "data": {
            "doctor_id": 1,
            "name": "홍길동",
            "email": "doctor@hospital.com",
            "department": "내과",
            "position": "전문의",
            "status": "on_duty"
        }
    }
    """
    user_id = request.data.get('userId')
    password = request.data.get('password')

    if not user_id or not password:
        return Response({
            'success': False,
            'message': '아이디와 비밀번호를 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Django 인증 시스템으로 사용자 확인
        from django.contrib.auth import authenticate

        user = authenticate(username=user_id, password=password)

        if not user:
            return Response({
                'success': False,
                'message': '아이디 또는 비밀번호가 일치하지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 해당 User와 연결된 DoctorProfile 찾기
        try:
            doctor = DoctorProfile.objects.select_related('departments', 'user').get(user=user)
        except DoctorProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '의사 프로필이 존재하지 않습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 로그인 성공
        return Response({
            'success': True,
            'message': '로그인 성공',
            'data': {
                'doctor_id': doctor.doctor_id,
                'name': doctor.name,
                'email': doctor.email,
                'phone': doctor.phone,
                'department': doctor.departments.department if doctor.departments else None,
                'department_code': doctor.departments.department_code if doctor.departments else None,
                'position': doctor.position,
                'status': doctor.status,
                'sex': doctor.sex,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'로그인 처리 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def nurse_login(request):
    """
    간호사 로그인 API

    Request Body:
    {
        "userId": "nurse_id",
        "password": "password"
    }

    Response:
    {
        "success": true,
        "message": "로그인 성공",
        "data": {
            "nurse_id": 1,
            "name": "김간호",
            "email": "nurse@hospital.com",
            "department": "내과",
            "position": "수간호사",
            "status": "on_duty"
        }
    }
    """
    user_id = request.data.get('userId')
    password = request.data.get('password')

    if not user_id or not password:
        return Response({
            'success': False,
            'message': '아이디와 비밀번호를 입력해주세요.'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Django 인증 시스템으로 사용자 확인
        from django.contrib.auth import authenticate

        user = authenticate(username=user_id, password=password)

        if not user:
            return Response({
                'success': False,
                'message': '아이디 또는 비밀번호가 일치하지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 해당 User와 연결된 NurseProfile 찾기
        try:
            nurse = NurseProfile.objects.select_related('department', 'user').get(user=user)
        except NurseProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '간호사 프로필이 존재하지 않습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 로그인 성공
        return Response({
            'success': True,
            'message': '로그인 성공',
            'data': {
                'nurse_id': nurse.nurse_id,
                'name': nurse.name,
                'email': nurse.email,
                'phone': nurse.phone,
                'department': nurse.department.department if nurse.department else None,
                'department_code': nurse.department.department_code if nurse.department else None,
                'position': nurse.position,
                'status': nurse.status,
                'sex': nurse.sex,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'로그인 처리 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def patient_list(request):
    """
    환자 리스트 조회 및 검색 API

    Query Parameters:
    - search_type: 'patient_id', 'name', 'resident_number'
    - search_value: 검색어
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지 크기 (기본값: 10)
    """
    try:
        search_type = request.GET.get('search_type', '')
        search_value = request.GET.get('search_value', '')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        # 기본 쿼리셋
        patients = Patient.objects.all()

        # 검색 조건 적용
        if search_type and search_value:
            if search_type == 'patient_id':
                patients = patients.filter(patient_id=search_value)
            elif search_type == 'name':
                patients = patients.filter(name__icontains=search_value)
            elif search_type == 'resident_number':
                patients = patients.filter(resident_number__icontains=search_value)

        # 전체 개수
        total_count = patients.count()

        # 페이징 처리
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        patients = patients[start_idx:end_idx]

        # 데이터 직렬화
        patient_data = []
        for patient in patients:
            patient_data.append({
                'patient_id': patient.patient_id,
                'name': patient.name,
                'birth_date': patient.birth_date.strftime('%Y-%m-%d') if patient.birth_date else None,
                'sex': patient.sex,
                'phone': patient.phone,
                'address': patient.address,
                'diagnosis_date': patient.diagnosis_date.strftime('%Y-%m-%d') if patient.diagnosis_date else None,
                'created_at': patient.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return Response({
            'success': True,
            'data': {
                'patients': patient_data,
                'pagination': {
                    'total_count': total_count,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_count + page_size - 1) // page_size
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'환자 목록 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def patient_detail(request, patient_id):
    """
    환자 상세 정보 조회 API
    """
    try:
        patient = Patient.objects.get(patient_id=patient_id)

        # 최근 진료 기록
        recent_records = MedicalRecord.objects.filter(
            patient=patient
        ).select_related('doctor').order_by('-visit_date')[:5]

        # 최근 바이탈
        recent_vital = MedicalVitals.objects.filter(
            patient=patient
        ).order_by('-measured_at').first()

        # 최근 임상 기록
        recent_clinical = ClinicalRecord.objects.filter(
            record__patient=patient
        ).select_related('record').order_by('-test_date').first()

        # 진료 기록 데이터
        records_data = []
        for record in recent_records:
            records_data.append({
                'record_id': record.record_id,
                'visit_date': record.visit_date.strftime('%Y-%m-%d %H:%M:%S'),
                'doctor_name': record.doctor.name,
                'chief_complaint': record.chief_complaint,
                'assessment': record.assessment,
            })

        # 바이탈 데이터
        vital_data = None
        if recent_vital:
            vital_data = {
                'height': float(recent_vital.height) if recent_vital.height else None,
                'weight': float(recent_vital.weight) if recent_vital.weight else None,
                'bp_systolic': recent_vital.bp_systolic,
                'bp_diastolic': recent_vital.bp_diastolic,
                'heart_rate': recent_vital.heart_rate,
                'temperature': float(recent_vital.temperature) if recent_vital.temperature else None,
                'measured_at': recent_vital.measured_at.strftime('%Y-%m-%d %H:%M:%S'),
            }

        # 임상 데이터
        clinical_data = None
        if recent_clinical:
            clinical_data = {
                'tumor_stage': recent_clinical.tumor_stage,
                'child_pugh': recent_clinical.child_pugh,
                'afp': recent_clinical.afp,
                'albumin': recent_clinical.albumin,
                'bilirubin': recent_clinical.bilirubin,
                'platelet': recent_clinical.platelet,
                'creatinine': recent_clinical.creatinine,
                'test_date': recent_clinical.test_date.strftime('%Y-%m-%d %H:%M:%S'),
            }

        return Response({
            'success': True,
            'data': {
                'patient': {
                    'patient_id': patient.patient_id,
                    'name': patient.name,
                    'birth_date': patient.birth_date.strftime('%Y-%m-%d') if patient.birth_date else None,
                    'sex': patient.sex,
                    'resident_number': patient.resident_number,
                    'phone': patient.phone,
                    'address': patient.address,
                    'diagnosis_date': patient.diagnosis_date.strftime('%Y-%m-%d') if patient.diagnosis_date else None,
                    'created_at': patient.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                },
                'recent_records': records_data,
                'vital': vital_data,
                'clinical': clinical_data,
            }
        }, status=status.HTTP_200_OK)

    except Patient.DoesNotExist:
        return Response({
            'success': False,
            'message': '존재하지 않는 환자입니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'환자 상세 정보 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
def medical_record(request, patient_id):
    """
    진료 기록 조회/생성 API
    """
    if request.method == 'GET':
        try:
            records = MedicalRecord.objects.filter(
                patient_id=patient_id
            ).select_related('doctor', 'patient').order_by('-visit_date')

            records_data = []
            for record in records:
                records_data.append({
                    'record_id': record.record_id,
                    'visit_date': record.visit_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'doctor_name': record.doctor.name,
                    'patient_name': record.patient.name,
                    'chief_complaint': record.chief_complaint,
                    'subjective': record.subjective,
                    'objective': record.objective,
                    'assessment': record.assessment,
                    'plan': record.plan,
                })

            return Response({
                'success': True,
                'data': records_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'진료 기록 조회 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            patient = Patient.objects.get(patient_id=patient_id)
            doctor_id = request.data.get('doctor_id')
            doctor = DoctorProfile.objects.get(doctor_id=doctor_id)

            record = MedicalRecord.objects.create(
                patient=patient,
                doctor=doctor,
                chief_complaint=request.data.get('chief_complaint', ''),
                subjective=request.data.get('subjective', ''),
                objective=request.data.get('objective', ''),
                assessment=request.data.get('assessment', ''),
                plan=request.data.get('plan', ''),
            )

            return Response({
                'success': True,
                'message': '진료 기록이 등록되었습니다.',
                'data': {
                    'record_id': record.record_id,
                }
            }, status=status.HTTP_201_CREATED)

        except Patient.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 환자입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except DoctorProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 의사입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'진료 기록 등록 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def change_password(request, doctor_id):
    """
    의사 비밀번호 변경 API

    Request Body:
    {
        "current_password": "현재 비밀번호",
        "new_password": "새 비밀번호"
    }
    """
    try:
        doctor = DoctorProfile.objects.select_related('user').get(doctor_id=doctor_id)
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({
                'success': False,
                'message': '현재 비밀번호와 새 비밀번호를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # auth_user의 현재 비밀번호 확인
        if not check_password(current_password, doctor.user.password):
            return Response({
                'success': False,
                'message': '현재 비밀번호가 일치하지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # auth_user의 비밀번호 변경 (해시화)
        doctor.user.set_password(new_password)
        doctor.user.save()

        return Response({
            'success': True,
            'message': '비밀번호가 성공적으로 변경되었습니다.'
        }, status=status.HTTP_200_OK)

    except DoctorProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': '존재하지 않는 의사입니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
def doctor_profile(request, doctor_id):
    """
    의사 개인정보 조회/수정 API
    """
    if request.method == 'GET':
        try:
            doctor = DoctorProfile.objects.select_related('departments').get(doctor_id=doctor_id)

            return Response({
                'success': True,
                'data': {
                    'doctor_id': doctor.doctor_id,
                    'name': doctor.name,
                    'sex': doctor.sex,
                    'phone': doctor.phone,
                    'email': doctor.email,
                    'position': doctor.position,
                    'status': doctor.status,
                    'department': doctor.departments.department if doctor.departments else None,
                    'department_code': doctor.departments.department_code if doctor.departments else None,
                    'created_at': doctor.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
            }, status=status.HTTP_200_OK)

        except DoctorProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 의사입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'프로필 조회 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PUT':
        try:
            doctor = DoctorProfile.objects.get(doctor_id=doctor_id)

            # 수정 가능한 필드들
            if 'phone' in request.data:
                doctor.phone = request.data['phone']
            if 'email' in request.data:
                doctor.email = request.data['email']
            if 'position' in request.data:
                doctor.position = request.data['position']
            if 'status' in request.data:
                doctor.status = request.data['status']

            doctor.save()

            return Response({
                'success': True,
                'message': '개인정보가 수정되었습니다.'
            }, status=status.HTTP_200_OK)

        except DoctorProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 의사입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'개인정보 수정 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
def nurse_profile(request, nurse_id):
    """
    간호사 개인정보 조회/수정 API
    """
    if request.method == 'GET':
        try:
            nurse = NurseProfile.objects.select_related('department').get(nurse_id=nurse_id)

            return Response({
                'success': True,
                'data': {
                    'nurse_id': nurse.nurse_id,
                    'name': nurse.name,
                    'sex': nurse.sex,
                    'phone': nurse.phone,
                    'email': nurse.email,
                    'position': nurse.position,
                    'status': nurse.status,
                    'department': nurse.department.department if nurse.department else None,
                    'department_code': nurse.department.department_code if nurse.department else None,
                    'created_at': nurse.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
            }, status=status.HTTP_200_OK)

        except NurseProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 간호사입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'프로필 조회 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PUT':
        try:
            nurse = NurseProfile.objects.get(nurse_id=nurse_id)

            # 수정 가능한 필드들
            if 'phone' in request.data:
                nurse.phone = request.data['phone']
            if 'email' in request.data:
                nurse.email = request.data['email']
            if 'position' in request.data:
                nurse.position = request.data['position']
            if 'status' in request.data:
                nurse.status = request.data['status']

            nurse.save()

            return Response({
                'success': True,
                'message': '개인정보가 수정되었습니다.'
            }, status=status.HTTP_200_OK)

        except NurseProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 간호사입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'개인정보 수정 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def nurse_change_password(request, nurse_id):
    """
    간호사 비밀번호 변경 API
    """
    try:
        nurse = NurseProfile.objects.select_related('user').get(nurse_id=nurse_id)
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')

        if not current_password or not new_password:
            return Response({
                'success': False,
                'message': '현재 비밀번호와 새 비밀번호를 모두 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # auth_user의 현재 비밀번호 확인
        if not check_password(current_password, nurse.user.password):
            return Response({
                'success': False,
                'message': '현재 비밀번호가 일치하지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # auth_user의 비밀번호 변경 (해시화)
        nurse.user.set_password(new_password)
        nurse.user.save()

        return Response({
            'success': True,
            'message': '비밀번호가 성공적으로 변경되었습니다.'
        })

    except NurseProfile.DoesNotExist:
        return Response({
            'success': False,
            'message': '존재하지 않는 간호사입니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
def appointment_list(request):
    """
    예약 리스트 조회/생성 API
    """
    if request.method == 'GET':
        try:
            doctor_id = request.GET.get('doctor_id')
            patient_id = request.GET.get('patient_id')
            date = request.GET.get('date')
            status_filter = request.GET.get('status')

            appointments = Appointment.objects.all().select_related('patient', 'doctor')

            # 필터 적용
            if doctor_id:
                appointments = appointments.filter(doctor_id=doctor_id)
            if patient_id:
                appointments = appointments.filter(patient_id=patient_id)
            if date:
                appointments = appointments.filter(appointment_date=date)
            if status_filter:
                appointments = appointments.filter(status=status_filter)

            appointments = appointments.order_by('appointment_date', 'appointment_time')

            appointments_data = []
            for apt in appointments:
                appointments_data.append({
                    'appointment_id': apt.appointment_id,
                    'appointment_date': apt.appointment_date.strftime('%Y-%m-%d'),
                    'appointment_time': apt.appointment_time.strftime('%H:%M'),
                    'status': apt.status,
                    'notes': apt.notes,
                    'patient': {
                        'patient_id': apt.patient.patient_id,
                        'name': apt.patient.name,
                        'phone': apt.patient.phone,
                    },
                    'doctor': {
                        'doctor_id': apt.doctor.doctor_id,
                        'name': apt.doctor.name,
                    },
                    'created_at': apt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                })

            return Response({
                'success': True,
                'data': appointments_data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'success': False,
                'message': f'예약 목록 조회 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        try:
            patient_id = request.data.get('patient_id')
            doctor_id = request.data.get('doctor_id')
            appointment_date = request.data.get('appointment_date')
            appointment_time = request.data.get('appointment_time')
            notes = request.data.get('notes', '')

            if not all([patient_id, doctor_id, appointment_date, appointment_time]):
                return Response({
                    'success': False,
                    'message': '필수 항목을 모두 입력해주세요.'
                }, status=status.HTTP_400_BAD_REQUEST)

            patient = Patient.objects.get(patient_id=patient_id)
            doctor = DoctorProfile.objects.get(doctor_id=doctor_id)

            # 중복 예약 확인
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='scheduled'
            ).exists()

            if existing:
                return Response({
                    'success': False,
                    'message': '해당 시간에 이미 예약이 존재합니다.'
                }, status=status.HTTP_400_BAD_REQUEST)

            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                notes=notes
            )

            return Response({
                'success': True,
                'message': '예약이 등록되었습니다.',
                'data': {
                    'appointment_id': appointment.appointment_id,
                }
            }, status=status.HTTP_201_CREATED)

        except Patient.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 환자입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except DoctorProfile.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 의사입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'예약 등록 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
def appointment_detail(request, appointment_id):
    """
    예약 상세 조회/수정/삭제 API
    """
    if request.method == 'GET':
        try:
            appointment = Appointment.objects.select_related('patient', 'doctor').get(
                appointment_id=appointment_id
            )

            return Response({
                'success': True,
                'data': {
                    'appointment_id': appointment.appointment_id,
                    'appointment_date': appointment.appointment_date.strftime('%Y-%m-%d'),
                    'appointment_time': appointment.appointment_time.strftime('%H:%M'),
                    'status': appointment.status,
                    'notes': appointment.notes,
                    'patient': {
                        'patient_id': appointment.patient.patient_id,
                        'name': appointment.patient.name,
                        'phone': appointment.patient.phone,
                    },
                    'doctor': {
                        'doctor_id': appointment.doctor.doctor_id,
                        'name': appointment.doctor.name,
                    },
                    'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                }
            }, status=status.HTTP_200_OK)

        except Appointment.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 예약입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'예약 조회 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PUT':
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)

            if 'appointment_date' in request.data:
                appointment.appointment_date = request.data['appointment_date']
            if 'appointment_time' in request.data:
                appointment.appointment_time = request.data['appointment_time']
            if 'status' in request.data:
                appointment.status = request.data['status']
            if 'notes' in request.data:
                appointment.notes = request.data['notes']

            appointment.save()

            return Response({
                'success': True,
                'message': '예약이 수정되었습니다.'
            }, status=status.HTTP_200_OK)

        except Appointment.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 예약입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'예약 수정 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
            appointment.status = 'cancelled'
            appointment.save()

            return Response({
                'success': True,
                'message': '예약이 취소되었습니다.'
            }, status=status.HTTP_200_OK)

        except Appointment.DoesNotExist:
            return Response({
                'success': False,
                'message': '존재하지 않는 예약입니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'예약 취소 중 오류가 발생했습니다: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def available_slots(request, doctor_id):
    """
    특정 의사의 특정 날짜 예약 가능 시간 조회 API

    Query Parameters:
    - date: 조회할 날짜 (YYYY-MM-DD)
    """
    try:
        date = request.GET.get('date')

        if not date:
            return Response({
                'success': False,
                'message': '날짜를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 해당 날짜의 예약된 시간 조회
        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=date,
            status='scheduled'
        ).values_list('appointment_time', flat=True)

        booked_times = [time.strftime('%H:%M') for time in booked_appointments]

        # 진료 가능 시간 (09:00 ~ 18:00, 30분 단위)
        all_slots = []
        for hour in range(9, 18):
            all_slots.append(f'{hour:02d}:00')
            all_slots.append(f'{hour:02d}:30')

        # 예약 가능한 시간
        available = [slot for slot in all_slots if slot not in booked_times]

        return Response({
            'success': True,
            'data': {
                'date': date,
                'available_slots': available,
                'booked_slots': booked_times
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'예약 가능 시간 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# 대시보드 통계 API
# ========================================
@api_view(['GET'])
def dashboard_stats(request):
    """
    대시보드 통계 API
    GET /api/dashboard/stats/
    """
    try:
        from .models import AiPrediction
        from django.utils import timezone
        from datetime import timedelta

        total_patients = Patient.objects.count()
        
        # 최근 30일 내 진료받은 환자 (active)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        active_patients = MedicalRecord.objects.filter(
            visit_date__gte=thirty_days_ago
        ).values('patient').distinct().count()

        # 고위험 환자 (risk_score >= 0.7)
        high_risk_patients = AiPrediction.objects.filter(
            risk_score__gte=0.7
        ).values('patient').distinct().count()

        # 최근 7일 예측 수
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_predictions = AiPrediction.objects.filter(
            analyzed_at__gte=seven_days_ago
        ).count()

        return Response({
            'success': True,
            'data': {
                'totalPatients': total_patients,
                'activePatients': active_patients,
                'highRiskPatients': high_risk_patients,
                'recentPredictions': recent_predictions,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'통계 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ========================================
# 환자 등록 및 수정 API (PatientForm 대응)
# ========================================
@api_view(['POST'])
def patient_create(request):
    """
    환자 기본 정보 생성 API
    POST /api/patients/create/
    """
    try:
        data = request.data
        
        # 필수 필드 확인 (name, sex, birth_date)
        if not data.get('name') or not data.get('sex') or not data.get('birth_date'):
             return Response({
                'success': False,
                'message': '이름, 성별, 생년월일은 필수입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        patient = Patient.objects.create(
            name=data.get('name'),
            birth_date=data.get('birth_date'),
            sex=data.get('sex'),
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            resident_number=data.get('resident_number', ''),
            emergency_contact=data.get('emergency_contact', ''),
            blood_type=data.get('blood_type', ''),
            # diagnosis_date 등 필요한 필드 추가
        )
        return Response({
            'success': True,
            'message': '환자가 등록되었습니다.',
            'data': {'patient_id': patient.patient_id}
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'환자 등록 중 오류 발생: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
def patient_update(request, patient_id):
    """
    환자 기본 정보 수정 API
    PUT /api/patients/{id}/update/
    """
    try:
        patient = Patient.objects.get(patient_id=patient_id)
        data = request.data
        
        patient.name = data.get('name', patient.name)
        patient.birth_date = data.get('birth_date', patient.birth_date)
        patient.sex = data.get('sex', patient.sex)
        patient.phone = data.get('phone', patient.phone)
        patient.address = data.get('address', patient.address)
        patient.resident_number = data.get('resident_number', patient.resident_number)
        patient.emergency_contact = data.get('emergency_contact', patient.emergency_contact)
        patient.blood_type = data.get('blood_type', patient.blood_type)
        
        patient.save()
        
        return Response({
            'success': True,
            'message': '환자 정보가 수정되었습니다.',
            'data': {'patient_id': patient.patient_id}
        }, status=status.HTTP_200_OK)

    except Patient.DoesNotExist:
        return Response({
            'success': False,
            'message': '존재하지 않는 환자입니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'환자 수정 중 오류 발생: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@csrf_exempt
def manage_clinical_data(request, patient_id):
    """
    임상 데이터 저장 API
    POST /api/patients/{id}/clinical/
    """
    try:
        # 1. 로그인 여부 확인
        if not request.user.is_authenticated:
             return Response({
                'success': False, 
                'message': '로그인이 필요합니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 2. 로그인한 사용자의 의사 프로필 가져오기
        try:
            current_doctor = DoctorProfile.objects.get(user=request.user)
        except DoctorProfile.DoesNotExist:
            return Response({
                'success': False, 
                'message': '로그인된 계정의 의사 프로필을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        patient = Patient.objects.get(patient_id=patient_id)
        data = request.data

        # 3. 해당 환자의 가장 최근 진료 기록 조회
        medical_record = MedicalRecord.objects.filter(patient=patient).order_by('-visit_date').first()

        # 4. 진료 기록이 없으면, "로그인한 의사" 명의로 자동 생성
        if not medical_record:
            medical_record = MedicalRecord.objects.create(
                patient=patient,
                doctor=current_doctor,  
                chief_complaint="초기 등록 (CDSS 임상 데이터 입력)" 
            )

        # 5. 임상 데이터 저장 (ClinicalRecord 생성)
        clinical_record = ClinicalRecord.objects.create(
            record=medical_record,
            tumor_stage=data.get('tumor_stage'), # 예: TNM 병기 등 매핑 확인
            child_pugh=data.get('child_pugh_class'), # 프론트엔드에서 보내는 키값
            afp=data.get('AFP'),
            bilirubin=data.get('bilirubin_total'),
            albumin=data.get('albumin'),
            platelet=data.get('platelet'),
            creatinine=data.get('creatinine'),
            # 필요한 경우 models.py의 필드에 맞춰 추가 매핑
            # 예: tumor_size=data.get('tumor_size'),
        )

        return Response({
            'success': True,
            'message': '임상 데이터가 저장되었습니다.'
        }, status=status.HTTP_201_CREATED)

    except Patient.DoesNotExist:
        return Response({'success': False, 'message': '환자를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        print(f"Error in manage_clinical_data: {e}")
        return Response({'success': False, 'message': str(e)}, status=500)

@api_view(['POST'])
def manage_genomic_data(request, patient_id):
    """
    유전체 데이터 저장 API
    POST /api/patients/{id}/genomic/
    """
    try:
        from .models import GenomicData # 모델 import 확인
        
        patient = Patient.objects.get(patient_id=patient_id)
        data = request.data

        GenomicData.objects.create(
            patient=patient,
            sample_date=data.get('sample_date'),
            sample_type=data.get('sample_type'),
            gpr182=data.get('GPR182'),
            klrb1=data.get('KLRB1'),
            # ... 나머지 필드 매핑 (mutation 정보 등)
            # tp53_mutation=data.get('TP53_mutation'),
            # notes=data.get('notes'),
        )

        return Response({
            'success': True,
            'message': '유전체 데이터가 저장되었습니다.'
        }, status=status.HTTP_201_CREATED)

    except Patient.DoesNotExist:
        return Response({'success': False, 'message': '환자를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)


@api_view(['POST'])
def add_imaging_study(request, patient_id):
    """
    영상 검사 메타데이터 저장 API (파일 업로드는 별도 API 사용)
    POST /api/patients/{id}/imaging/
    """
    try:
        from .models import ImagingStudy # 모델 import 확인
        
        patient = Patient.objects.get(patient_id=patient_id)
        data = request.data

        ImagingStudy.objects.create(
            patient=patient,
            study_date=data.get('study_date'),
            modality=data.get('modality'),
            body_part=data.get('body_part'),
            contrast=data.get('contrast', False),
            institution=data.get('institution'),
            accession_number=data.get('accession_number'),
            # findings=data.get('findings'),
            # impression=data.get('impression'),
        )

        return Response({
            'success': True,
            'message': '영상 검사 정보가 등록되었습니다.'
        }, status=status.HTTP_201_CREATED)

    except Patient.DoesNotExist:
        return Response({'success': False, 'message': '환자를 찾을 수 없습니다.'}, status=404)
    except Exception as e:
        return Response({'success': False, 'message': str(e)}, status=500)

# ========================================
# 환자 삭제 API
# ========================================
@api_view(['DELETE'])
def patient_delete(request, patient_id):
    """
    환자 삭제 API
    DELETE /api/patients/{patient_id}/delete/
    """
    try:
        patient = Patient.objects.get(patient_id=patient_id)
        patient.delete()

        return Response({
            'success': True,
            'message': '환자가 삭제되었습니다.'
        }, status=status.HTTP_200_OK)

    except Patient.DoesNotExist:
        return Response({
            'success': False,
            'message': '존재하지 않는 환자입니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'환자 삭제 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# 임상 기록 조회 API
# ========================================
@api_view(['GET'])
def clinical_records(request):
    """
    임상 기록 조회 API
    GET /api/clinical-records/?patient_id={id}
    """
    try:
        patient_id = request.GET.get('patient_id')

        if not patient_id:
            return Response({
                'success': False,
                'message': 'patient_id가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        records = ClinicalRecord.objects.filter(
            record__patient_id=patient_id
        ).select_related('record').order_by('-test_date')

        records_data = []
        for record in records:
            records_data.append({
                'clinical_id': record.clinical_id,
                'tumor_stage': record.tumor_stage,
                'child_pugh': record.child_pugh,
                'afp': record.afp,
                'albumin': record.albumin,
                'bilirubin': record.bilirubin,
                'platelet': record.platelet,
                'creatinine': record.creatinine,
                'test_date': record.test_date.strftime('%Y-%m-%d'),
            })

        return Response({
            'success': True,
            'data': records_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'임상 기록 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# 유전체 기록 조회 API
# ========================================
@api_view(['GET'])
def genomic_records(request):
    """
    유전체 기록 조회 API
    GET /api/genomic-records/?patient_id={id}
    """
    try:
        from .models import GenomicRecord

        patient_id = request.GET.get('patient_id')

        if not patient_id:
            return Response({
                'success': False,
                'message': 'patient_id가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        records = GenomicRecord.objects.filter(
            patient_id=patient_id
        ).order_by('-sample_date')

        records_data = []
        for record in records:
            records_data.append({
                'sample_id': record.sample_id,
                'sample_date': record.sample_date.strftime('%Y-%m-%d'),
                'gene_data': record.gene_data,
            })

        return Response({
            'success': True,
            'data': records_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'유전체 기록 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# AI 예측 결과 조회 API
# ========================================
@api_view(['GET'])
def ai_predictions(request):
    """
    AI 예측 결과 조회 API
    GET /api/ai-predictions/?patient_id={id}
    """
    try:
        from .models import AiPrediction

        patient_id = request.GET.get('patient_id')

        if not patient_id:
            return Response({
                'success': False,
                'message': 'patient_id가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        predictions = AiPrediction.objects.filter(
            patient_id=patient_id
        ).order_by('-analyzed_at')

        predictions_data = []
        for pred in predictions:
            predictions_data.append({
                'prediction_id': pred.prediction_id,
                'risk_score': pred.risk_score,
                'survival_prob_1yr': pred.survival_prob_1yr,
                'survival_prob_3yr': pred.survival_prob_3yr,
                'gradcam_path': pred.gradcam_path,
                'analyzed_at': pred.analyzed_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return Response({
            'success': True,
            'data': predictions_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'AI 예측 결과 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# DICOM Study 목록 조회 API
# ========================================
@api_view(['GET'])
def dicom_studies(request):
    """
    DICOM Study 목록 조회 API
    GET /api/dicom-studies/?patient_id={id}
    """
    try:
        from .models import DicomStudy

        patient_id = request.GET.get('patient_id')

        if not patient_id:
            return Response({
                'success': False,
                'message': 'patient_id가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        studies = DicomStudy.objects.filter(
            patient_id=patient_id
        ).order_by('-study_date')

        studies_data = []
        for study in studies:
            studies_data.append({
                'study_uid': study.study_uid,
                'study_date': study.study_date.strftime('%Y-%m-%d'),
                'study_desc': study.study_desc,
                'modality': study.modality,
                'patient_id': study.patient_id,
            })

        return Response({
            'success': True,
            'data': studies_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'DICOM Study 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ========================================
# DICOM Series 목록 조회 API
# ========================================
@api_view(['GET'])
def dicom_series(request):
    """
    DICOM Series 목록 조회 API
    GET /api/dicom-series/?study_uid={uid}
    """
    try:
        from .models import DicomSeries

        study_uid = request.GET.get('study_uid')

        if not study_uid:
            return Response({
                'success': False,
                'message': 'study_uid가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        series_list = DicomSeries.objects.filter(
            study__study_uid=study_uid
        ).order_by('series_number')

        series_data = []
        for series in series_list:
            series_data.append({
                'series_uid': series.series_uid,
                'series_number': series.series_number,
                'series_desc': series.series_desc,
                'phase_label': series.phase_label,
                'slice_count': series.slice_count,
                'thumbnail_path': series.thumbnail_path,
                'is_selected': series.is_selected,
            })

        return Response({
            'success': True,
            'data': series_data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'success': False,
            'message': f'DICOM Series 조회 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================
# BentoML 설정
# ============================================================
BENTOML_CONFIG = {
    'URL': 'http://localhost:3001',  # BentoML 서버 주소
    'TIMEOUT': 3600,  # 1시간 (대용량 CT 처리용)
}

# CT 스캔 파일 저장 경로 (settings.py에서 MEDIA_ROOT 설정 필요)
CT_UPLOAD_PATH = os.path.join(settings.MEDIA_ROOT, 'ct_scans')
os.makedirs(CT_UPLOAD_PATH, exist_ok=True)


# ============================================================
# API 1: CT 파일 업로드 + 세그멘테이션 요청
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def segment_ct(request):
    """
    CT 파일을 받아서 BentoML 서버로 세그멘테이션 요청
    
    Request:
        - file: CT NIfTI 파일 (.nii 또는 .nii.gz)
        - patient_id: 환자 ID (optional)
    
    Response:
        {
            "success": true,
            "data": {
                "original_path": "/media/ct_scans/volume-20.nii",
                "segmentation_path": "/media/ct_scans/volume-20_seg.nii.gz",
                "labels_found": [0, 1, 8, 9],
                "tumor_detected": true,
                "message": "세그멘테이션 완료"
            }
        }
    """
    try:
        # 1. 파일 받기
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'CT 파일이 필요합니다.'
            }, status=400)
        
        ct_file = request.FILES['file']
        patient_id = request.POST.get('patient_id', 'unknown')
        
        # 파일 확장자 확인
        if not (ct_file.name.endswith('.nii') or ct_file.name.endswith('.nii.gz')):
            return JsonResponse({
                'success': False,
                'error': 'NIfTI 파일만 업로드 가능합니다. (.nii, .nii.gz)'
            }, status=400)
        
        # 2. 파일 저장
        save_filename = f"patient_{patient_id}_{ct_file.name}"
        save_path = os.path.join(CT_UPLOAD_PATH, save_filename)
        
        with open(save_path, 'wb+') as destination:
            for chunk in ct_file.chunks():
                destination.write(chunk)
        
        print(f"📂 CT 파일 저장됨: {save_path}")
        
        # 3. BentoML 서버로 세그멘테이션 요청
        # WSL 환경이면 경로 변환 필요
        bentoml_file_path = convert_to_wsl_path(save_path)
        
        response = requests.post(
            f"{BENTOML_CONFIG['URL']}/segment",
            json={"file_path": bentoml_file_path},
            timeout=BENTOML_CONFIG['TIMEOUT']
        )
        
        result = response.json()
        
        if result.get('status') == 'success':
            seg_path = result.get('result_path', '')
            
            # Windows 경로로 다시 변환 (React에서 접근용)
            seg_path_windows = convert_from_wsl_path(seg_path)
            
            # 라벨 분석 (optional - nibabel 필요)
            labels_found, tumor_detected = analyze_segmentation(seg_path_windows)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'original_path': f"/media/ct_scans/{save_filename}",
                    'segmentation_path': seg_path_windows.replace(settings.MEDIA_ROOT, '/media'),
                    'labels_found': labels_found,
                    'tumor_detected': tumor_detected,
                    'message': '세그멘테이션 완료'
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('message', 'BentoML 서버 오류')
            }, status=500)
            
    except requests.exceptions.Timeout:
        return JsonResponse({
            'success': False,
            'error': '세그멘테이션 시간 초과 (파일이 너무 큽니다)'
        }, status=504)
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'error': 'BentoML 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.'
        }, status=503)
    except Exception as e:
        print(f"❌ 세그멘테이션 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================
# API 2: 기존 파일로 세그멘테이션 요청 (파일 경로만 전달)
# ============================================================
@csrf_exempt
@require_http_methods(["POST"])
def segment_existing_file(request):
    """
    이미 서버에 있는 CT 파일로 세그멘테이션 요청
    
    Request:
        {
            "file_path": "/media/ct_scans/volume-20.nii",
            "patient_id": 1
        }
    """
    try:
        data = json.loads(request.body)
        file_path = data.get('file_path')
        patient_id = data.get('patient_id')
        
        if not file_path:
            return JsonResponse({
                'success': False,
                'error': 'file_path가 필요합니다.'
            }, status=400)
        
        # /media/ 경로를 실제 경로로 변환
        if file_path.startswith('/media/'):
            file_path = file_path.replace('/media/', settings.MEDIA_ROOT + '/')
        
        if not os.path.exists(file_path):
            return JsonResponse({
                'success': False,
                'error': f'파일을 찾을 수 없습니다: {file_path}'
            }, status=404)
        
        # WSL 경로로 변환
        bentoml_file_path = convert_to_wsl_path(file_path)
        
        # BentoML 요청
        response = requests.post(
            f"{BENTOML_CONFIG['URL']}/segment",
            json={"file_path": bentoml_file_path},
            timeout=BENTOML_CONFIG['TIMEOUT']
        )
        
        result = response.json()
        
        if result.get('status') == 'success':
            seg_path = result.get('result_path', '')
            seg_path_windows = convert_from_wsl_path(seg_path)
            labels_found, tumor_detected = analyze_segmentation(seg_path_windows)
            
            return JsonResponse({
                'success': True,
                'data': {
                    'segmentation_path': seg_path_windows.replace(settings.MEDIA_ROOT, '/media'),
                    'labels_found': labels_found,
                    'tumor_detected': tumor_detected,
                    'patient_id': patient_id
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('message', 'BentoML 오류')
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================
# API 3: BentoML 서버 상태 확인
# ============================================================
@require_http_methods(["GET"])
def check_bentoml_status(request):
    """BentoML 서버가 실행 중인지 확인"""
    try:
        response = requests.get(
            f"{BENTOML_CONFIG['URL']}/healthz",
            timeout=5
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'status': 'online',
                'url': BENTOML_CONFIG['URL'],
                'message': 'BentoML 서버 정상 작동 중'
            }
        })
    except requests.exceptions.ConnectionError:
        return JsonResponse({
            'success': False,
            'data': {
                'status': 'offline',
                'url': BENTOML_CONFIG['URL'],
                'message': 'BentoML 서버에 연결할 수 없습니다'
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ============================================================
# 유틸리티 함수들
# ============================================================
def convert_to_wsl_path(windows_path: str) -> str:
    """
    Windows 경로를 WSL 경로로 변환
    C:\\Users\\... -> /mnt/c/Users/...
    """
    if windows_path.startswith('/mnt/'):
        return windows_path  # 이미 WSL 경로
    
    # C:\path -> /mnt/c/path
    path = windows_path.replace('\\', '/')
    if len(path) > 1 and path[1] == ':':
        drive_letter = path[0].lower()
        path = f'/mnt/{drive_letter}{path[2:]}'
    
    return path


def convert_from_wsl_path(wsl_path: str) -> str:
    """
    WSL 경로를 Windows 경로로 변환
    /mnt/c/Users/... -> C:\\Users\\...
    """
    if not wsl_path.startswith('/mnt/'):
        return wsl_path  # 이미 Windows 경로이거나 다른 형식
    
    # /mnt/c/path -> C:/path
    parts = wsl_path.split('/')
    if len(parts) >= 3:
        drive_letter = parts[2].upper()
        remaining_path = '/'.join(parts[3:])
        return f'{drive_letter}:/{remaining_path}'
    
    return wsl_path


def analyze_segmentation(seg_path: str) -> tuple:
    """
    세그멘테이션 결과 분석 (라벨 확인, 종양 검출 여부)
    Returns: (labels_found: list, tumor_detected: bool)
    """
    try:
        import nibabel as nib
        import numpy as np
        
        if not os.path.exists(seg_path):
            return [], False
        
        seg_img = nib.load(seg_path)
        seg_data = seg_img.get_fdata().astype(np.uint8)
        
        labels_found = list(map(int, np.unique(seg_data)))
        tumor_detected = 9 in labels_found  # 라벨 9 = 종양
        
        return labels_found, tumor_detected
        
    except Exception as e:
        print(f"세그멘테이션 분석 오류: {e}")
        return [], False


# ============================================================
# API 4: 전체 진료 기록 조회
# ============================================================
@require_http_methods(["GET"])
def all_medical_records(request):
    try:
        records = MedicalRecord.objects.select_related('patient', 'doctor').all().order_by('-visit_date')
        
        data = []
        for record in records:
            data.append({
                'record_id': record.record_id,
                'visit_date': record.visit_date,
                'patient_name': record.patient.name,
                'doctor_name': record.doctor.name,
                'chief_complaint': record.chief_complaint,
                'assessment': record.assessment,
            })
            
        return JsonResponse({'success': True, 'data': {'records': data}})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

# ========================================
# Orthanc Webhook & Upload Views (수정됨)
# ========================================

class OrthancWebhookView(APIView):
    def post(self, request):
        instance_id = request.data.get('instance_id')
        print(f"[Django] Webhook received for ID: {instance_id}")

        # 1. 저장할 경로 설정
        save_dir = os.path.join(settings.MEDIA_ROOT, 'dicom_input')
        os.makedirs(save_dir, exist_ok=True)
        file_path = os.path.join(save_dir, f"{instance_id}.dcm")

        # [수정] settings.py의 설정을 사용하여 URL 생성
        base_url = getattr(settings, 'ORTHANC_URL', 'http://localhost:8042')
        orthanc_url = f"{base_url}/instances/{instance_id}/file"
        
        # [수정] settings.py의 설정을 사용하여 인증 정보 생성
        auth = (
            getattr(settings, 'ORTHANC_USER', 'orthanc'),
            getattr(settings, 'ORTHANC_PASSWORD', 'orthanc')
        )
        
        try:
            # 2. Orthanc에서 파일 다운로드
            with requests.get(orthanc_url, stream=True, auth=auth) as r:
                r.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            print(f"[Django] File saved at: {file_path}")

            # 3. AI Server 분석 요청
            # (Docker 환경에 따라 주소 확인 필요: bentoml_server 또는 host.docker.internal)
            ai_api_url = "http://bentoml_server:3000/segment"
            
            response = requests.post(ai_api_url, json={"file_path": file_path})
            
            if response.status_code == 200:
                ai_result = response.json()
                print(f"[Django] AI Analysis Complete: {ai_result}")
                return Response({"status": "success", "result": ai_result})
            else:
                print(f"[Django] AI Server Error: {response.text}")
                return Response({"status": "error", "message": "AI server error"}, status=500)

        except Exception as e:
            print(f"[Error] Processing failed: {e}")
            return Response({"status": "error", "message": str(e)}, status=500)

@csrf_exempt
def dicom_upload(request):
    """
    프론트엔드에서 파일을 받아 Orthanc로 업로드하는 뷰
    (utils.py의 upload_dicom_to_orthanc 함수 사용)
    """
    if request.method == 'POST':
        try:
            # 1. 파일 확인
            if 'file' not in request.FILES:
                return JsonResponse({'status': 'error', 'message': '파일이 없습니다.'}, status=400)
            
            uploaded_file = request.FILES['file']
            
            # 2. 유틸리티 함수를 통해 Orthanc로 업로드 (코드가 훨씬 간결해짐)
            result = upload_dicom_to_orthanc(uploaded_file)

            if result and 'ID' in result:
                # 성공
                return JsonResponse({
                    'status': 'success', 
                    'message': 'Upload successful',
                    'data': result
                })
            else:
                # 실패
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Failed to upload to Orthanc'
                }, status=500)

        except Exception as e:
            print(f"서버 내부 오류: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'POST 요청만 허용됩니다.'}, status=405)



@csrf_exempt
def dicom_folder_upload(request):
    """
    React에서 폴더 단위로 파일을 받아 저장하고, 
    Orthanc 백업 및 BentoML 분석을 순차적으로 실행합니다.
    """
    if request.method == 'POST':
        try:
            # 1. 파일 목록 받기
            files = request.FILES.getlist('files')
            patient_id = request.POST.get('patient_id', 'unknown')
            
            if not files:
                return JsonResponse({'status': 'error', 'message': '파일이 없습니다.'}, status=400)

            print(f"📂 [Upload] 환자 {patient_id}의 파일 {len(files)}개 수신 시작...")

            # 2. 저장 경로 설정
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', str(patient_id), timestamp)
            os.makedirs(upload_dir, exist_ok=True)

            # 3. 파일 로컬 저장 & Orthanc 전송
            saved_count = 0
            uploaded_instance_ids = []

            # Orthanc 설정
            orthanc_base_url = getattr(settings, 'ORTHANC_URL', 'http://orthanc_pacs:8042')
            orthanc_auth = (
                getattr(settings, 'ORTHANC_USER', 'orthanc'),
                getattr(settings, 'ORTHANC_PASSWORD', 'orthanc')
            )

            for f in files:
                # 3-1. 로컬 저장
                file_path = os.path.join(upload_dir, f.name)
                with open(file_path, 'wb+') as destination:
                    for chunk in f.chunks():
                        destination.write(chunk)
                saved_count += 1

                # 3-2. Orthanc 전송 (실패해도 분석은 계속 진행)
                try:
                    f.seek(0)
                    orthanc_response = requests.post(
                        f"{orthanc_base_url}/instances",
                        data=f.read(),
                        auth=orthanc_auth,
                        headers={'Content-Type': 'application/dicom'},
                        timeout=5
                    )
                    if orthanc_response.status_code in [200, 201]:
                        instance_data = orthanc_response.json()
                        uploaded_instance_ids.append(instance_data.get('ID'))
                except Exception as e:
                    print(f"⚠️ Orthanc 업로드 실패 ({f.name}): {e}")

            print(f"✅ {saved_count}개 파일 저장 완료. 경로: {upload_dir}")

            # 3-3. Django 테이블에 Study/Series 정보 저장
            if uploaded_instance_ids:
                try:
                    from .models import DicomStudy, DicomSeries
                    import pydicom

                    # 첫 번째 인스턴스에서 Study/Series 정보 가져오기
                    first_instance_id = uploaded_instance_ids[0]
                    instance_info_response = requests.get(
                        f"{orthanc_base_url}/instances/{first_instance_id}/tags?simplify",
                        auth=orthanc_auth,
                        timeout=5
                    )

                    if instance_info_response.status_code == 200:
                        tags = instance_info_response.json()
                        study_uid = tags.get('StudyInstanceUID', '')
                        series_uid = tags.get('SeriesInstanceUID', '')

                        # Study 저장 (중복 체크)
                        study, created = DicomStudy.objects.get_or_create(
                            study_uid=study_uid,
                            defaults={
                                'patient_id': patient_id,
                                'study_date': tags.get('StudyDate', datetime.now().strftime('%Y%m%d')),
                                'study_desc': tags.get('StudyDescription', 'Uploaded Study'),
                                'modality': tags.get('Modality', 'CT')
                            }
                        )

                        # Series 저장 (중복 체크)
                        series, created = DicomSeries.objects.get_or_create(
                            series_uid=series_uid,
                            defaults={
                                'study': study,
                                'series_number': int(tags.get('SeriesNumber', 1)),
                                'series_desc': tags.get('SeriesDescription', 'Uploaded Series'),
                                'phase_label': tags.get('SeriesDescription', 'Unknown'),
                                'slice_count': len(uploaded_instance_ids),
                                'is_selected': True
                            }
                        )
                        print(f"✅ Django 테이블 저장 완료: Study={study_uid}, Series={series_uid}")
                except Exception as e:
                    print(f"⚠️ Django 테이블 저장 실패: {e}")
                    import traceback
                    traceback.print_exc()

            # =========================================================
            # 4. BentoML 분석 요청 
            # =========================================================
            bentoml_url = "http://bentoml_server:3000/segment"
            
           
            bentoml_path = upload_dir.replace('/app/config/media', '/app/media')
            
            # 만약 경로가 바뀌지 않았다면 강제로 맞춰줍니다 (안전장치)
            if '/app/config/media' not in upload_dir:
                 # 로컬 테스트 환경 등을 대비해 절대 경로가 아니라면 상대 경로 등을 고려해야 함
                 # 하지만 Docker 환경에서는 위 replace가 핵심입니다.
                 pass

            print(f"🚀 BentoML 분석 요청 전송: {bentoml_url}")
            print(f"   👉 전달하는 경로: {bentoml_path}")
            
            response = requests.post(
                bentoml_url,
                json={"file_path": bentoml_path}, 
                timeout=3600 # 대용량 처리를 위해 타임아웃 길게
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"🎉 분석 완료: {result}")
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Analysis complete',
                    'data': result,
                    'patient_id': patient_id
                })
            else:
                print(f"❌ BentoML 응답 에러: {response.text}")
                return JsonResponse({
                    'status': 'error', 
                    'message': f'BentoML Error: {response.text}'
                }, status=500)

        except Exception as e:
            print(f"❌ 서버 내부 오류: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'POST only'}, status=405)


@api_view(['GET'])
def get_patient_ai_results(request, patient_id):
    """
    특정 환자의 최신 AI 분석 결과 조회 API

    Response:
    {
        "success": true,
        "data": {
            "patient_id": 1,
            "latest_result": {
                "created_at": "2024-12-08 10:30:00",
                "thumbnail_url": "/media/ai_results/123/overlay_slice_1.png",
                "slices": [
                    {"url": "/media/ai_results/123/overlay_slice_0.png"},
                    {"url": "/media/ai_results/123/overlay_slice_1.png"},
                    {"url": "/media/ai_results/123/overlay_slice_2.png"}
                ],
                "metrics": {
                    "liver_volume": 1234.5,
                    "tumor_volume": 45.2
                }
            }
        }
    }
    """
    try:
        from django.db.models import Max
        import glob

        # 1. 해당 환자의 업로드 폴더 확인
        patient_upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', str(patient_id))

        if not os.path.exists(patient_upload_dir):
            return Response({
                'success': False,
                'message': '아직 업로드된 DICOM 파일이 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 2. 가장 최근 타임스탬프 폴더 찾기
        timestamp_folders = sorted(
            [f for f in os.listdir(patient_upload_dir) if os.path.isdir(os.path.join(patient_upload_dir, f))],
            reverse=True
        )

        if not timestamp_folders:
            return Response({
                'success': False,
                'message': '분석 결과가 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        latest_folder = timestamp_folders[0]
        result_dir = os.path.join(patient_upload_dir, latest_folder)

        # 3. PNG 파일 찾기
        png_files = sorted(glob.glob(os.path.join(result_dir, 'overlay_slice_*.png')))

        if not png_files:
            return Response({
                'success': False,
                'message': 'AI 분석이 아직 완료되지 않았습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 4. URL 변환 (media 경로를 웹 URL로)
        slices = []
        for png_file in png_files:
            # /app/config/media/uploads/1/20241208_103000/overlay_slice_0.png
            # → /media/uploads/1/20241208_103000/overlay_slice_0.png
            rel_path = png_file.replace(settings.MEDIA_ROOT, '').replace('\\', '/')
            if not rel_path.startswith('/'):
                rel_path = '/' + rel_path
            slices.append({
                'url': f"/media{rel_path}" if not rel_path.startswith('/media') else rel_path,
                'filename': os.path.basename(png_file)
            })

        # 5. 생성 시간 (폴더명에서 추출)
        try:
            created_at = datetime.strptime(latest_folder, '%Y%m%d_%H%M%S').strftime('%Y-%m-%d %H:%M:%S')
        except:
            created_at = latest_folder

        return Response({
            'success': True,
            'data': {
                'patient_id': patient_id,
                'latest_result': {
                    'created_at': created_at,
                    'thumbnail_url': slices[1]['url'] if len(slices) > 1 else slices[0]['url'],  # 중간 슬라이스를 썸네일로
                    'slices': slices,
                    'total_slices': len(slices)
                }
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'success': False,
            'message': f'결과 조회 중 오류 발생: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)