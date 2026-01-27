from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from .models import Patient, DoctorProfile
from .ddi_utils import analyze_drug_interactions

def login_view(request):
    """의사 로그인 뷰"""
    if request.user.is_authenticated:
        # 이미 로그인된 경우: Superuser는 CDSS 관리자로, 의사는 home으로
        if request.user.is_superuser:
            return redirect('cdss_admin')
        return redirect('home')
    
    if request.method == 'POST':
        username_or_doctor_id = request.POST.get('username')
        password = request.POST.get('password')

        # 먼저 username으로 인증 시도
        user = authenticate(request, username=username_or_doctor_id, password=password)

        # username으로 실패하면 doctor_id로 시도
        if user is None:
            try:
                # doctor_id로 DoctorProfile 찾기
                doctor_profile = DoctorProfile.objects.get(doctor_id=username_or_doctor_id)
                # 해당 User로 인증
                user = authenticate(request, username=doctor_profile.user.username, password=password)
            except DoctorProfile.DoesNotExist:
                pass

        if user is not None:
            # Superuser는 DoctorProfile 없이도 로그인 허용
            if user.is_superuser:
                login(request, user)
                messages.success(request, f'{user.username}님, 환영합니다! (관리자)')
                return redirect('cdss_admin')  # Superuser는 CDSS 관리자로 리다이렉트

            # 일반 사용자는 의사 프로필이 있는지 확인
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
    # Superuser는 CDSS 관리자로 리다이렉트
    if request.user.is_superuser:
        return redirect('cdss_admin')

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


# ============================================
# CDSS 관리자 전용 뷰
# ============================================

@login_required(login_url='login')
def cdss_admin_view(request):
    """CDSS 관리자 대시보드"""
    # Superuser만 접근 가능
    if not request.user.is_superuser:
        messages.error(request, 'CDSS 관리자 권한이 필요합니다.')
        return redirect('home')

    # 모든 의사 목록
    doctors = DoctorProfile.objects.all().select_related('user')

    context = {
        'doctors': doctors,
    }

    return render(request, 'django_1pj/cdss_admin.html', context)


@login_required(login_url='login')
def cdss_admin_doctor_add_view(request):
    """CDSS 관리자 - 의사 추가"""
    if not request.user.is_superuser:
        messages.error(request, 'CDSS 관리자 권한이 필요합니다.')
        return redirect('home')

    if request.method == 'POST':
        # User 생성
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # DoctorProfile 정보
        doctor_id = request.POST.get('doctor_id')
        doctor_name = request.POST.get('doctor_name')
        doctor_sex = request.POST.get('doctor_sex')
        doctor_phone = request.POST.get('doctor_phone', '')
        doctor_email = request.POST.get('doctor_email', '')

        # 유효성 검사
        if password != password_confirm:
            messages.error(request, '비밀번호가 일치하지 않습니다.')
            return render(request, 'django_1pj/cdss_admin_doctor_form.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, f'이미 존재하는 사용자명입니다: {username}')
            return render(request, 'django_1pj/cdss_admin_doctor_form.html')

        if DoctorProfile.objects.filter(doctor_id=doctor_id).exists():
            messages.error(request, f'이미 존재하는 의사 ID입니다: {doctor_id}')
            return render(request, 'django_1pj/cdss_admin_doctor_form.html')

        try:
            # User 생성
            user = User.objects.create_user(
                username=username,
                password=password,
                is_staff=False,
                is_superuser=False
            )

            # DoctorProfile 생성
            DoctorProfile.objects.create(
                user=user,
                doctor_id=doctor_id,
                doctor_name=doctor_name,
                doctor_sex=doctor_sex,
                doctor_phone=doctor_phone,
                doctor_email=doctor_email,
                doctor_status='진료외'
            )

            messages.success(request, f'의사 계정이 생성되었습니다: {doctor_name} ({doctor_id})')
            return redirect('cdss_admin')

        except Exception as e:
            messages.error(request, f'계정 생성 중 오류가 발생했습니다: {str(e)}')
            return render(request, 'django_1pj/cdss_admin_doctor_form.html')

    return render(request, 'django_1pj/cdss_admin_doctor_form.html')


@login_required(login_url='login')
def cdss_admin_doctor_delete_view(request, doctor_id):
    """CDSS 관리자 - 의사 삭제"""
    if not request.user.is_superuser:
        messages.error(request, 'CDSS 관리자 권한이 필요합니다.')
        return redirect('home')

    if request.method == 'POST':
        try:
            doctor = DoctorProfile.objects.get(doctor_id=doctor_id)
            user = doctor.user
            doctor_name = doctor.doctor_name

            # User와 DoctorProfile 모두 삭제
            doctor.delete()
            user.delete()

            messages.success(request, f'{doctor_name} 의사 계정이 삭제되었습니다.')
        except DoctorProfile.DoesNotExist:
            messages.error(request, '해당 의사를 찾을 수 없습니다.')

    return redirect('cdss_admin')


# ============================================
# DDI 분석 뷰
# ============================================

@login_required(login_url='login')
def ddi_analysis_view(request):
    """DDI 분석 페이지"""
    try:
        doctor_profile = request.user.doctorprofile
    except DoctorProfile.DoesNotExist:
        if not request.user.is_superuser:
            messages.error(request, '의사 프로필이 없습니다.')
            return redirect('login')
        doctor_profile = None

    context = {
        'doctor': doctor_profile,
    }

    return render(request, 'django_1pj/ddi_analysis.html', context)


@login_required(login_url='login')
def ddi_analyze_api(request):
    """DDI 분석 API (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST 요청만 허용됩니다.'}, status=405)

    # 약물 리스트 받기 (쉼표로 구분된 문자열 또는 JSON 배열)
    import json
    try:
        data = json.loads(request.body)
        drug_names = data.get('drugs', [])
    except:
        drugs_str = request.POST.get('drugs', '')
        drug_names = [d.strip() for d in drugs_str.split(',') if d.strip()]

    if not drug_names:
        return JsonResponse({'error': '약물 이름을 입력해주세요.'}, status=400)

    if len(drug_names) < 2:
        return JsonResponse({'error': '최소 2개 이상의 약물이 필요합니다.'}, status=400)

    # DDI 분석 수행
    try:
        result = analyze_drug_interactions(drug_names)

        # 에러가 있으면 반환
        if 'error' in result:
            return JsonResponse(result, status=400)

        return JsonResponse(result)

    except Exception as e:
        return JsonResponse({'error': f'분석 중 오류 발생: {str(e)}'}, status=500)


@login_required(login_url='login')
def ddi_drug_list_api(request):
    """약물 목록 API - 자동완성용"""
    import os

    drug_set = set()  # 중복 제거를 위해 set 사용
    drug_info_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        'deepddi2', 'data', 'Approved_drug_Information.txt'
    )

    try:
        with open(drug_info_file, 'r', encoding='utf-8') as f:
            # 헤더가 없으므로 next(f) 제거
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    drug_name = parts[1].strip()  # 두 번째 컬럼이 약물 이름
                    if drug_name:  # 빈 문자열이 아닌 경우만 추가
                        drug_set.add(drug_name)

        # set을 list로 변환하고 알파벳순 정렬
        drug_list = sorted(list(drug_set))

        return JsonResponse({'drugs': drug_list})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)