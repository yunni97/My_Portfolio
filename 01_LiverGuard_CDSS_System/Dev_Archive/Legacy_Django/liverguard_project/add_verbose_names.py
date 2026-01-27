"""
Add verbose_name to models
"""
import re

verbose_names = {
    "DoctorProfiles": ("의사 프로필", "의사 프로필"),
    "Drugs": ("약물 정보", "약물 정보"),
    "Patients": ("환자", "환자"),
    "MedicalRecords": ("진료 기록", "진료 기록"),
    "MedicalDiagnosis": ("진단", "진단"),
    "MedicalVitals": ("활력 징후", "활력 징후"),
    "BloodResults": ("혈액 검사", "혈액 검사"),
    "MedicalStudy": ("영상 검사", "영상 검사"),
    "MedicalSeries": ("영상 시리즈", "영상 시리즈"),
    "Prescriptions": ("처방전", "처방전"),
    "PrescriptionDrug": ("처방 약물", "처방 약물"),
    "DrugForm": ("약물 형태", "약물 형태"),
    "DrugRoute": ("투약 경로", "투약 경로"),
    "DrugFrequency": ("투약 빈도", "투약 빈도"),
    "NurseProfiles": ("간호사 프로필", "간호사 프로필"),
    "NursingNotes": ("간호 기록", "간호 기록"),
    "Departments": ("부서", "부서"),
    "DeseaseManage": ("질병 관리", "질병 관리"),
    "Announcements": ("공지사항", "공지사항"),
    "AuthUsers": ("인증 사용자", "인증 사용자"),
}

# Read the models.py file
with open('liverguard/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add verbose_name to each model
for model_name, (verbose_singular, verbose_plural) in verbose_names.items():
    # Find the Meta class for this model
    pattern = rf'(class {model_name}\(models\.Model\):.*?class Meta:.*?db_table = [^\n]+)'

    def add_verbose(match):
        meta_section = match.group(1)
        if 'verbose_name' not in meta_section:
            # Add verbose_name after db_table
            meta_section = meta_section + f"\n        verbose_name = '{verbose_singular}'\n        verbose_name_plural = '{verbose_plural}'"
        return meta_section

    content = re.sub(pattern, add_verbose, content, flags=re.DOTALL)

# Write back
with open('liverguard/models.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Added verbose_name to all models!")
