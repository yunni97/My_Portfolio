
# CSV 컬럼 → 여러 테이블로 분리하여 삽입
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, date

# ============================================
# 1. DB 연결 설정 (수정 필요)
# ============================================
# cmd 에서 ipconfig -> 나의 컴퓨터 ip 확인
DB_CONFIG = {
    'host': '192.168.0.18',
    'port': 5432,
    'database': 'postgres',  
    'user': 'postgres',       
    'password': 'acorm1234'   
}

engine = create_engine(
    f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
)

# ============================================
# 2. CSV 읽기 및 전처리
# ============================================
df = pd.read_csv('clinical_matched.csv')
print(f"총 {len(df)}개 행 로드됨")

# [Not Available], [Discrepancy], [Unknown] 등을 None으로 변환
na_values = ['[Not Available]', '[Discrepancy]', '[Unknown]', '', ' ']
df = df.replace(na_values, None)

# 숫자 컬럼 변환 함수
def safe_numeric(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except:
        return None

def safe_int(value):
    if value is None or pd.isna(value):
        return None
    try:
        return int(float(value))
    except:
        return None
print("✅ 전처리 완료")

def calculate_birth_date(age, birth_year, diagnosis_year=2015):
    if birth_year and not pd.isna(birth_year):
        return date(int(birth_year), 1, 1)  # 1월 1일로 가정
    elif age and not pd.isna(age):
        try:
            birth_year_calc = diagnosis_year - int(age)
            return date(birth_year_calc, 1, 1)
        except:
            return None
    return None

# ============================================
# 4. 테이블별 데이터 준비
# ============================================
patient_data = []
for _, row in df.iterrows():
    patient_data.append({
        'patient_id': row['PATIENT_ID'],
        'sample_id': row['SAMPLE_ID'],
        'name': f"Patient_{row['PATIENT_ID'][-4:]}",
        'date_of_birth': calculate_birth_date(row['AGE'], row.get('BIRTH_YEAR')),
        'age': safe_int(row['AGE']),
        'gender': row['SEX'],
        'current_status': None,
        'created_at': datetime.now(),
        'updated_at': datetime.now(),
        'doctor_id': None
    })
df_patient = pd.DataFrame(patient_data)
print(f"✅ patient 데이터 준비 완료: {len(df_patient)}행")
df_patient.head()

anthro_data = []
for _, row in df.iterrows():
    height = safe_numeric(row['HEIGHT'])
    weight = safe_numeric(row['WEIGHT'])
    
    # BMI 계산
    bmi = None
    if height and weight and height > 0:
        bmi = round(weight / ((height / 100) ** 2), 2)
    
    anthro_data.append({
        'measured_at': date.today(),
        'height': height,
        'weight': weight,
        'bmi': bmi,
        'is_pregnant': False,
        'smoking_status': False,
        'patient_id': row['PATIENT_ID'],
        'encounter_id': None 
    })
df_anthro = pd.DataFrame(anthro_data)
print(f"✅ anthropometric_data 준비 완료: {len(df_anthro)}행")
df_anthro.head()

# ============================================
# lab_data
# ============================================
import math

def calculate_meld(bilirubin, inr, creatinine):
    if bilirubin is None or inr is None or creatinine is None:
        return None
    
    # 최소값 1로 설정
    bilirubin = max(1.0, float(bilirubin))
    inr = max(1.0, float(inr))
    creatinine = max(1.0, float(creatinine))
    # 크레아티닌 최대값 4.0 (투석 환자 기준)
    creatinine = min(4.0, creatinine)
    
    meld = (3.78 * math.log(bilirubin) + 
            11.2 * math.log(inr) + 
            9.57 * math.log(creatinine) + 
            6.43)
    
    # 반올림 및 범위 제한 (6-40)
    return max(6, min(40, round(meld)))

def calculate_albi(bilirubin, albumin):
    if bilirubin is None or albumin is None:
        return None, None
    
    try:
        # 단위 변환
        # Bilirubin: mg/dL → μmol/L (×17.1)
        # Albumin: g/dL → g/L (×10)
        bili_umol = float(bilirubin) * 17.1
        alb_gl = float(albumin) * 10
        
        if bili_umol <= 0 or alb_gl <= 0:
            return None, None
        
        albi_score = (math.log10(bili_umol) * 0.66) + (alb_gl * -0.085)
        albi_score = round(albi_score, 3)
        
        # ALBI Grade
        if albi_score <= -2.60:
            albi_grade = '1'
        elif albi_score <= -1.39:
            albi_grade = '2'
        else:
            albi_grade = '3'
        
        return albi_score, albi_grade
    
    except:
        return None, None

lab_data = []
for _, row in df.iterrows():
    # ALBI 먼저 계산 (튜플 반환)
    albi_score, albi_grade = calculate_albi(
        safe_numeric(row['BILIRUBIN_TOTAL']), 
        safe_numeric(row['SERUM_ALBUMIN_PRERESECTION'])
    )
    lab_data.append({
        'test_date': date.today(),
        'afp': safe_numeric(row['AFP_AT_PROCUREMENT']),
        'albumin': safe_numeric(row['SERUM_ALBUMIN_PRERESECTION']),
        'bilirubin_total': safe_numeric(row['BILIRUBIN_TOTAL']),
        'pt_inr': safe_numeric(row['PROTHROMBIN_TIME_INR_AT_PROCUREMENT']),
        'platelet': safe_int(row['PLATELET_COUNT_PRERESECTION']),
        'creatinine': safe_numeric(row['CREATININE_LEVEL_PRERESECTION']),
        'child_pugh_class': row['CHILD_PUGH_CLASSIFICATION'] if row['CHILD_PUGH_CLASSIFICATION'] in ['A', 'B', 'C'] else None,
        'meld_score': calculate_meld(
            safe_numeric(row['BILIRUBIN_TOTAL']),
            safe_numeric(row['PROTHROMBIN_TIME_INR_AT_PROCUREMENT']), 
            safe_numeric(row['CREATININE_LEVEL_PRERESECTION'])     
        ),
        'albi_score': albi_score,
        'albi_grade': albi_grade,
        'created_at': datetime.now(),
        'patient_id': row['PATIENT_ID'],
        'encounter_id': None
    })
df_lab = pd.DataFrame(lab_data)
print(f"✅ lab_results 준비 완료: {len(df_lab)}행")
df_lab.head()


def parse_ishak_score(value):
    if value is None or pd.isna(value):
        return None
    try:
        return int(str(value).split(' ')[0].replace(',', ''))
    except:
        return None

def parse_ecog(value):
    """ECOG score 파싱"""
    if value is None or pd.isna(value):
        return None
    try:
        return int(value)
    except:
        return None

diagnosis_data = []
for _, row in df.iterrows():
    ajcc_stage = row['AJCC_PATHOLOGIC_TUMOR_STAGE']
    if ajcc_stage and 'Stage' in str(ajcc_stage):
        ajcc_stage = ajcc_stage.replace('Stage ', '')
    
    diagnosis_data.append({
        'diagnosis_date': date.today(),  # 실제로는 진단일
        'ajcc_stage': ajcc_stage,
        'ajcc_t': row['AJCC_TUMOR_PATHOLOGIC_PT'],
        'ajcc_n': row['AJCC_NODES_PATHOLOGIC_PN'],
        'ajcc_m': row['AJCC_METASTASIS_PATHOLOGIC_PM'],
        'grade': row['GRADE'],
        'vascular_invasion': row['VASCULAR_INVASION'],
        'ishak_score': parse_ishak_score(row['ISHAK_FIBROSIS_SCORE']),
        'hepatic_inflammation': row['HEPATIC_INFLAMMATION_ADJ_TISSUE'],
        'ecog_score': parse_ecog(row['ECOG_SCORE']),
        'tumor_status': row['TUMOR_STATUS'],
        'measured_at': datetime.now(),
        'created_at': datetime.now(),
        'patient_id': row['PATIENT_ID'],
        'encounter_id': None  
    })
df_diagnosis = pd.DataFrame(diagnosis_data)
print(f"✅ hcc_diagnosis 준비 완료: {len(df_diagnosis)}행")
df_diagnosis.head()


genomic_data = []
for _, row in df.iterrows():
    genomic_data.append({
        'sample_date': None,
        'pathway_scores': None,
        'lasso_coefficients': None,
        'risk_genes': None,
        'created_at': datetime.now(),
        'patient_id': row['PATIENT_ID'],
        'sample_id': row['SAMPLE_ID']
    })
df_genomic = pd.DataFrame(genomic_data)

print(engine.url)

df_patient.to_sql(
    'patient',
    engine,
    if_exists='append',
    index=False
)
print("✅ patient 테이블 INSERT 완료")


# FK 순서 중요! patient 먼저

# 1. patient
df_patient.to_sql('patient', engine, if_exists='append', index=False)
print("✅ patient INSERT 완료")

# 2. anthropometric_data (encounter_id 제외)
df_anthro_clean = df_anthro.drop(columns=['encounter_id'])
df_anthro_clean.to_sql('anthropometric_data', engine, if_exists='append', index=False)
print("✅ anthropometric_data INSERT 완료")

# 3. lab_results (encounter_id 제외)
df_lab_clean = df_lab.drop(columns=['encounter_id'])
df_lab_clean.to_sql('lab_results', engine, if_exists='append', index=False)
print("✅ lab_results INSERT 완료")

# 4. hcc_diagnosis (encounter_id 제외)
df_diagnosis_clean = df_diagnosis.drop(columns=['encounter_id'])
df_diagnosis_clean.to_sql('hcc_diagnosis', engine, if_exists='append', index=False)
print("✅ hcc_diagnosis INSERT 완료")

# 5. genomic_data
df_genomic.to_sql('genomic_data', engine, if_exists='append', index=False)
print("✅ genomic_data INSERT 완료")

print("\n🎉 모든 데이터 INSERT 완료!")