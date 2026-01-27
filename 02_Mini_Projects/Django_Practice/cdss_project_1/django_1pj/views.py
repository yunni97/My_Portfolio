from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Patient, DoctorProfile

def login_view(request):
    """의사 로그인 뷰"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # 의사 프로필이 있는지 확인
            try:
                doctor_profile = user.doctorprofile
                login(request, user)
                messages.success(request, f'{doctor_profile.doctor_name} 선생님, 환영합니다!')
                return redirect('home')
            except DoctorProfile.DoesNotExist:
                messages.error(request, '의사 계정이 아닙니다. 관리자에게 문의하세요.')
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    
    return render(request, 'django_1pj/login.html')


def logout_view(request):
    """로그아웃 뷰"""
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('login')


@login_required(login_url='login')
def home_view(request):
    """CDSS 홈화면 - 환자 리스트"""
    try:
        doctor_profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        messages.error(request, '의사 프로필이 없습니다. 관리자에게 문의하세요.')
        return redirect('login')
    
    # 담당 환자 목록 조회
    patients = Patient.objects.filter(doctor=doctor_profile).order_by('-updated_at')
    
    # 검색 기능
    search_query = request.GET.get('search', '')
    if search_query:
        patients = patients.filter(
            Q(patient_id__icontains=search_query) |
            Q(name__icontains=search_query)
        )
    
    context = {
        'doctor': doctor_profile,
        'patients': patients,
        'search_query': search_query,
    }

    return render(request, 'django_1pj/home.html', context)


@login_required(login_url='login')
def patient_detail_view(request, patient_id):
    """환자 상세 정보 및 예후 관리 화면"""
    try:
        doctor_profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        messages.error(request, '의사 프로필이 없습니다.')
        return redirect('login')
    
    try:
        patient = Patient.objects.get(patient_id=patient_id, doctor=doctor_profile)
    except Patient.DoesNotExist:
        messages.error(request, '해당 환자 정보를 찾을 수 없습니다.')
        return redirect('home')
    
    if request.method == 'POST':
        # 환자 정보 업데이트
        patient.name = request.POST.get('name')
        patient.birth_date = request.POST.get('birth_date')
        patient.gender = request.POST.get('gender')
        patient.phone = request.POST.get('phone', '')
        
        # 진단 정보
        diagnosis_date = request.POST.get('diagnosis_date')
        if diagnosis_date:
            patient.diagnosis_date = diagnosis_date
        
        patient.bclc_stage = request.POST.get('bclc_stage', '')
        
        tumor_size = request.POST.get('tumor_size')
        if tumor_size:
            patient.tumor_size = float(tumor_size)
        
        tumor_count = request.POST.get('tumor_count')
        if tumor_count:
            patient.tumor_count = int(tumor_count)
        
        patient.child_pugh = request.POST.get('child_pugh', '')
        patient.vascular_invasion = request.POST.get('vascular_invasion') == 'on'
        
        afp_initial = request.POST.get('afp_initial')
        if afp_initial:
            patient.afp_initial = float(afp_initial)
        
        afp_current = request.POST.get('afp_current')
        if afp_current:
            patient.afp_current = float(afp_current)
        
        # 치료 정보
        patient.treatment_type = request.POST.get('treatment_type', '')
        
        treatment_start_date = request.POST.get('treatment_start_date')
        if treatment_start_date:
            patient.treatment_start_date = treatment_start_date
        
        patient.recurrence_risk = request.POST.get('recurrence_risk', '')
        
        next_ct_date = request.POST.get('next_ct_date')
        if next_ct_date:
            patient.next_ct_date = next_ct_date
        
        next_blood_test_date = request.POST.get('next_blood_test_date')
        if next_blood_test_date:
            patient.next_blood_test_date = next_blood_test_date
        
        patient.save()
        messages.success(request, '환자 정보가 수정되었습니다.')
        return redirect('patient_detail', patient_id=patient.patient_id)
    
    context = {
        'doctor': doctor_profile,
        'patient': patient,
    }
    
    return render(request, 'django_1pj/patient_detail.html', context)


@login_required(login_url='login')
def patient_add_view(request):
    """새 환자 추가"""
    try:
        doctor_profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        messages.error(request, '의사 프로필이 없습니다.')
        return redirect('login')
    
    if request.method == 'POST':
        # 환자 생성
        patient = Patient()
        patient.patient_id = request.POST.get('patient_id')
        patient.name = request.POST.get('name')
        patient.birth_date = request.POST.get('birth_date')
        patient.gender = request.POST.get('gender')
        patient.phone = request.POST.get('phone', '')
        patient.doctor = doctor_profile
        
        # 진단 정보
        diagnosis_date = request.POST.get('diagnosis_date')
        if diagnosis_date:
            patient.diagnosis_date = diagnosis_date
        
        patient.bclc_stage = request.POST.get('bclc_stage', '')
        
        tumor_size = request.POST.get('tumor_size')
        if tumor_size:
            patient.tumor_size = float(tumor_size)
        
        tumor_count = request.POST.get('tumor_count')
        if tumor_count:
            patient.tumor_count = int(tumor_count)
        
        patient.child_pugh = request.POST.get('child_pugh', '')
        patient.vascular_invasion = request.POST.get('vascular_invasion') == 'on'
        
        afp_initial = request.POST.get('afp_initial')
        if afp_initial:
            patient.afp_initial = float(afp_initial)
        
        afp_current = request.POST.get('afp_current')
        if afp_current:
            patient.afp_current = float(afp_current)
        
        # 치료 정보
        patient.treatment_type = request.POST.get('treatment_type', '')
        
        treatment_start_date = request.POST.get('treatment_start_date')
        if treatment_start_date:
            patient.treatment_start_date = treatment_start_date
        
        patient.recurrence_risk = request.POST.get('recurrence_risk', '')
        
        next_ct_date = request.POST.get('next_ct_date')
        if next_ct_date:
            patient.next_ct_date = next_ct_date
        
        next_blood_test_date = request.POST.get('next_blood_test_date')
        if next_blood_test_date:
            patient.next_blood_test_date = next_blood_test_date
        
        try:
            patient.save()
            messages.success(request, '새 환자가 추가되었습니다.')
            return redirect('patient_detail', patient_id=patient.patient_id)
        except Exception as e:
            messages.error(request, f'환자 추가 중 오류가 발생했습니다: {str(e)}')
    
    context = {
        'doctor': doctor_profile,
        'patient': None,  # 새 환자이므로 None
    }
    
    return render(request, 'django_1pj/patient_detail.html', context)


@login_required(login_url='login')
def patient_delete_view(request, patient_id):
    """환자 삭제"""
    try:
        doctor_profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        messages.error(request, '의사 프로필이 없습니다.')
        return redirect('login')
    
    if request.method == 'POST':
        try:
            patient = Patient.objects.get(patient_id=patient_id, doctor=doctor_profile)
            patient.delete()
            messages.success(request, '환자가 삭제되었습니다.')
        except Patient.DoesNotExist:
            messages.error(request, '해당 환자를 찾을 수 없습니다.')
    
    return redirect('home')