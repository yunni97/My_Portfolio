from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import (
    Patients, MedicalRecords, Prescriptions, Drugs,
    BloodResults, MedicalVitals, MedicalStudy, DoctorProfiles
)


# 의사 로그인
def doctor_login_view(request):
    """의사 로그인 뷰"""
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor_id')
        password = request.POST.get('password')

        # 커스텀 백엔드를 통한 인증
        doctor = authenticate(request, doctor_id=doctor_id, password=password)

        if doctor is not None:
            # 세션에 의사 정보 저장
            request.session['doctor_id'] = doctor.doctor_id
            request.session['doctor_name'] = doctor.name

            # 마지막 로그인 시간 업데이트
            doctor.last_login = timezone.now()
            doctor.save(update_fields=['last_login'])

            messages.success(request, f'{doctor.name} 님, 환영합니다!')
            return redirect('liverguard:home')
        else:
            messages.error(request, '의사 ID 또는 비밀번호가 올바르지 않습니다.')

    return render(request, 'liverguard/doctor_login.html')


# 의사 로그아웃
def doctor_logout_view(request):
    """의사 로그아웃 뷰"""
    doctor_name = request.session.get('doctor_name', '의사')
    request.session.flush()
    messages.success(request, f'{doctor_name} 님, 로그아웃되었습니다.')
    return redirect('liverguard:doctor_login')


# 홈 페이지
def home(request):
    # 의사 로그인 체크
    if 'doctor_id' not in request.session:
        messages.warning(request, '로그인이 필요합니다.')
        return redirect('liverguard:doctor_login')

    search_query = request.GET.get('search', '')

    if search_query:
        patients = Patients.objects.filter(name__icontains=search_query).order_by('-created_at')[:50]
    else:
        patients = Patients.objects.all().order_by('-created_at')[:50]

    context = {
        'patients': patients,
        'search_query': search_query,
        'total_patients': Patients.objects.count(),
        'total_records': MedicalRecords.objects.count(),
        'total_prescriptions': Prescriptions.objects.count(),
        'doctor_name': request.session.get('doctor_name', ''),
    }
    return render(request, 'liverguard/home.html', context)


# 환자 목록
def patient_list(request):
    patients = Patients.objects.all().order_by('-created_at')
    return render(request, 'liverguard/patient_list.html', {'patients': patients})


# 환자 상세
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patients, patient_id=patient_id)
    records = MedicalRecords.objects.filter(patient=patient).order_by('-visit_date')

    context = {
        'patient': patient,
        'records': records,
    }
    return render(request, 'liverguard/patient_detail.html', context)


# 환자 추가
def patient_add(request):
    if request.method == 'POST':
        # TODO: 폼 처리 로직 추가
        pass
    return render(request, 'liverguard/patient_form.html')


# 진료기록 목록
def record_list(request):
    records = MedicalRecords.objects.all().order_by('-visit_date')[:50]
    return render(request, 'liverguard/record_list.html', {'records': records})


# 진료기록 상세
def record_detail(request, record_id):
    record = get_object_or_404(MedicalRecords, record_id=record_id)

    # 관련 데이터 조회
    try:
        vitals = MedicalVitals.objects.get(record=record)
    except MedicalVitals.DoesNotExist:
        vitals = None

    try:
        blood = BloodResults.objects.filter(record=record).latest('taken_at')
    except BloodResults.DoesNotExist:
        blood = None

    prescriptions = Prescriptions.objects.filter(record=record)
    studies = MedicalStudy.objects.filter(record=record)

    context = {
        'record': record,
        'vitals': vitals,
        'blood': blood,
        'prescriptions': prescriptions,
        'studies': studies,
    }
    return render(request, 'liverguard/record_detail.html', context)


# 진료기록 추가
def record_add(request):
    if request.method == 'POST':
        # TODO: 폼 처리 로직 추가
        pass

    patients = Patients.objects.all()
    return render(request, 'liverguard/record_form.html', {'patients': patients})


# 처방 목록
def prescription_list(request):
    prescriptions = Prescriptions.objects.all().order_by('-created_at')[:50]
    return render(request, 'liverguard/prescription_list.html', {'prescriptions': prescriptions})


# 처방 상세
def prescription_detail(request, prescription_id):
    prescription = get_object_or_404(Prescriptions, prescription_id=prescription_id)
    return render(request, 'liverguard/prescription_detail.html', {'prescription': prescription})


# 약물 목록
def drug_list(request):
    query = request.GET.get('q', '')
    if query:
        drugs = Drugs.objects.filter(name_kr__icontains=query) | Drugs.objects.filter(name_eng__icontains=query)
    else:
        drugs = Drugs.objects.all()[:50]

    return render(request, 'liverguard/drug_list.html', {'drugs': drugs, 'query': query})


# 약물 상세
def drug_detail(request, drug_id):
    drug = get_object_or_404(Drugs, drug_id=drug_id)
    return render(request, 'liverguard/drug_detail.html', {'drug': drug})
