"""
DeepDDI2 통합 유틸리티
약물 리스트를 입력받아 DDI 위험도를 분석
"""
import os
import sys
import tempfile
import pandas as pd
from itertools import combinations

# DeepDDI2 경로 추가
DEEPDDI_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'deepddi2')
sys.path.insert(0, DEEPDDI_PATH)

# sklearn 버전 호환성을 위한 모듈 경로 리다이렉트
if 'sklearn.preprocessing.label' not in sys.modules:
    import sklearn.preprocessing
    sys.modules['sklearn.preprocessing.label'] = sklearn.preprocessing

from deepddi import DeepDDI
from deepddi import preprocessing

# DeepDDI2 데이터 및 모델 경로
DATA_DIR = os.path.join(DEEPDDI_PATH, 'data')
MODEL_DIR = os.path.join(DATA_DIR, 'models')
DRUG_INFO_FILE = os.path.join(DATA_DIR, 'Approved_drug_Information.txt')
PCA_PROFILE_FILE = os.path.join(DATA_DIR, 'drug_tanimoto_PCA50.csv')
DDI_MODEL_JSON = os.path.join(MODEL_DIR, 'ddi_model.json')
DDI_MODEL_WEIGHT = os.path.join(MODEL_DIR, 'ddi_model.h5')
BINARIZER_FILE = os.path.join(DATA_DIR, 'multilabelbinarizer.pkl')
INTERACTION_INFO_FILE = os.path.join(DATA_DIR, 'Type_information', 'Interaction_information_model1.csv')


# 약물 정보 로드 (약물명 -> SMILES 매핑)
def load_drug_database():
    """승인된 약물 정보 로드"""
    drug_db = {}

    try:
        # 1단계: all_approved_drug_input.txt에서 DB ID -> SMILES 매핑
        all_drug_input_file = os.path.join(DATA_DIR, 'all_approved_drug_input.txt')
        db_to_smiles = {}

        with open(all_drug_input_file, 'r', encoding='utf-8') as f:
            next(f)  # 헤더 스킵 (Prescription, Drug name, Smiles)
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    db_id = parts[1].strip()
                    smiles = parts[2].strip()
                    if db_id and smiles:
                        db_to_smiles[db_id] = smiles

        # 2단계: Approved_drug_Information.txt에서 약물 이름 -> DB ID 매핑
        with open(DRUG_INFO_FILE, 'r', encoding='utf-8') as f:
            # 헤더가 없으므로 next(f) 제거
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    db_id = parts[0].strip()
                    drug_name = parts[1].strip()

                    # SMILES가 있는 경우만 추가
                    if db_id in db_to_smiles and drug_name:
                        drug_db[drug_name.lower()] = {
                            'name': drug_name,
                            'db_id': db_id,  # DB ID 추가
                            'smiles': db_to_smiles[db_id]
                        }

    except Exception as e:
        print(f"약물 데이터베이스 로드 오류: {e}")

    return drug_db


# 상호작용 타입별 기본 위험도 (의학적 중요도 기반)
INTERACTION_SEVERITY = {
    # 매우 위험 (생명을 위협할 수 있는 상호작용)
    1: 'high',    # congestive heart failure, hypotension
    4: 'high',    # anemia, severe leukopenia
    7: 'high',    # myopathy, rhabdomyolysis
    8: 'high',    # rhabdomyolysis, myoglobinuria, elevated CPK
    9: 'high',    # QTc prolongation, cardiac arrest
    24: 'high',   # myopathy, rhabdomyolysis, myoglobinuria
    28: 'high',   # rhabdomyolysis

    # 중등도 위험 (모니터링 필요)
    2: 'medium',  # decreased excretion
    3: 'medium',  # increased serum concentration
    6: 'medium',  # increased active metabolites
    12: 'medium', # hyperkalemic activities
    14: 'medium', # edema formation
    16: 'medium', # angioedema
    17: 'medium', # decreased excretion
    18: 'medium', # hypersensitivity reaction
    19: 'medium', # fluid retention
    21: 'medium', # hypertensive activities
    22: 'medium', # nephrotoxic activities
    25: 'medium', # CNS depressant, hypotensive
    26: 'medium', # CNS depressant, hypertensive
    27: 'medium', # respiratory depressant
    38: 'medium', # sedation, somnolence

    # 경미 또는 긍정적 (위험도 낮음)
    10: 'low',    # therapeutic efficacy increased (좋은 것!)
    11: 'low',    # decrease cardiotoxic activities (좋은 것!)
    13: 'low',    # decreased absorption (경미)
    15: 'low',    # decreased sedative activities
    20: 'low',    # decreased serum concentration
    23: 'low',    # decreased protein binding
    29: 'low',    # increased analgesic activities (좋은 것!)
}

# DDI 위험도 등급 계산 (상호작용 타입과 점수 기반)
def calculate_risk_level(score, interaction_type=None):
    """
    점수와 상호작용 타입을 기반으로 위험도 등급 반환

    Args:
        score: 예측 점수 (0-1)
        interaction_type: 상호작용 타입 번호 (1-113)

    Returns:
        dict: {'level': str, 'label': str, 'emoji': str}
    """
    # 상호작용 타입이 있으면 타입별 기본 위험도 사용
    if interaction_type is not None:
        base_severity = INTERACTION_SEVERITY.get(interaction_type, 'medium')

        # 점수가 매우 낮으면 (< 0.5) 한 단계 낮춤
        if score < 0.5:
            if base_severity == 'high':
                base_severity = 'medium'
            elif base_severity == 'medium':
                base_severity = 'low'

        # 점수가 매우 높으면 (> 0.8) 한 단계 높임
        elif score > 0.8:
            if base_severity == 'low':
                base_severity = 'medium'
            elif base_severity == 'medium':
                base_severity = 'high'

        if base_severity == 'high':
            return {'level': 'high', 'label': '높음', 'emoji': '🔴'}
        elif base_severity == 'medium':
            return {'level': 'medium', 'label': '중간', 'emoji': '⚠️'}
        else:
            return {'level': 'low', 'label': '안전', 'emoji': '✅'}

    # 타입 정보가 없으면 점수만으로 판단 (더 보수적인 임계값)
    if score >= 0.85:
        return {'level': 'high', 'label': '높음', 'emoji': '🔴'}
    elif score >= 0.6:
        return {'level': 'medium', 'label': '중간', 'emoji': '⚠️'}
    else:
        return {'level': 'low', 'label': '안전', 'emoji': '✅'}


# 상호작용 정보 로드
def load_interaction_info():
    """DDI 상호작용 타입 정보 로드"""
    interaction_db = {}
    try:
        # 탭으로 구분된 CSV 파일
        df = pd.read_csv(INTERACTION_INFO_FILE, sep='\t')
        # 컬럼 이름이 'type'과 'sentence'
        for idx, row in df.iterrows():
            interaction_db[int(row['type'])] = row['sentence']
    except Exception as e:
        print(f"상호작용 정보 로드 오류: {e}")
        import traceback
        traceback.print_exc()

    return interaction_db


def analyze_drug_interactions(drug_names):
    """
    약물 리스트를 받아 DDI 분석 수행

    Args:
        drug_names: 약물 이름 리스트 ['Aspirin', 'Metformin', ...]

    Returns:
        {
            'overall_risk': {'score': 0.45, 'level': 'medium', 'label': '중간'},
            'total_pairs': 6,
            'analyzed_pairs': 4,
            'interactions': [
                {
                    'drug1': 'Aspirin',
                    'drug2': 'Metformin',
                    'risk': {'score': 0.65, 'level': 'medium', 'label': '중간'},
                    'description': '저혈당 위험 증가'
                },
                ...
            ],
            'not_found': ['UnknownDrug']
        }
    """
    drug_db = load_drug_database()
    interaction_db = load_interaction_info()

    # 약물 매칭
    matched_drugs = []
    not_found = []

    for drug_name in drug_names:
        drug_lower = drug_name.lower().strip()
        if drug_lower in drug_db:
            matched_drugs.append(drug_db[drug_lower])
        else:
            not_found.append(drug_name)

    # 매칭된 약물이 2개 미만이면 분석 불가
    if len(matched_drugs) < 2:
        error_msg = f'분석 가능한 약물이 {len(matched_drugs)}개입니다. 최소 2개 이상 필요합니다.'
        if not_found:
            error_msg += f'\n찾을 수 없는 약물: {", ".join(not_found)}'
        if matched_drugs:
            matched_names = [d['name'] for d in matched_drugs]
            error_msg += f'\n매칭된 약물: {", ".join(matched_names)}'

        print(f"[DEBUG] {error_msg}")  # 서버 로그에 출력

        return {
            'error': error_msg,
            'matched': len(matched_drugs),
            'not_found': not_found
        }

    # DB ID -> 약물 이름 매핑 (결과 표시용)
    db_id_to_name = {drug['db_id']: drug['name'] for drug in matched_drugs}

    # DDI 입력 파일 생성 (임시 파일) - DB ID 사용
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_input:
        tmp_input.write('Prescription\tDrug name\tSmiles\n')
        for i, drug in enumerate(matched_drugs):
            # DeepDDI는 Drug name 컬럼에 DB ID를 기대함
            tmp_input.write(f'TMP001\t{drug["db_id"]}\t{drug["smiles"]}\n')
        tmp_input_path = tmp_input.name

    try:
        # 임시 출력 디렉토리
        with tempfile.TemporaryDirectory() as tmp_output_dir:
            # DDI 입력 파일 파싱
            parsed_input_file = os.path.join(tmp_output_dir, 'DDI_input.txt')
            preprocessing.parse_DDI_input_file(tmp_input_path, parsed_input_file)

            # PCA 프로파일 생성
            pca_df = preprocessing.generate_input_profile(parsed_input_file, PCA_PROFILE_FILE)

            # DDI 예측
            output_file = os.path.join(tmp_output_dir, 'DDI_result.txt')
            DeepDDI.predict_DDI(output_file, pca_df, DDI_MODEL_JSON, DDI_MODEL_WEIGHT,
                               0.4, BINARIZER_FILE, 'model1')

            # 결과 파싱
            interactions = []
            scores = []

            with open(output_file, 'r') as f:
                next(f)  # 헤더 스킵
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        drug_pair = parts[0].split('_')
                        drug1_db_id = drug_pair[1] if len(drug_pair) > 1 else ''
                        drug2_db_id = drug_pair[2] if len(drug_pair) > 2 else ''

                        # DB ID를 약물 이름으로 변환
                        drug1_name = db_id_to_name.get(drug1_db_id, drug1_db_id)
                        drug2_name = db_id_to_name.get(drug2_db_id, drug2_db_id)

                        interaction_class = int(parts[1])
                        score = float(parts[2])

                        description = interaction_db.get(interaction_class, f'상호작용 타입 {interaction_class}')

                        # 상호작용 타입을 고려한 위험도 계산
                        risk = calculate_risk_level(score, interaction_type=interaction_class)
                        risk['score'] = score
                        risk['type'] = interaction_class

                        interactions.append({
                            'drug1': drug1_name,
                            'drug2': drug2_name,
                            'risk': risk,
                            'description': description
                        })
                        scores.append(score)

            # 전체 위험도 계산 (평균 점수)
            overall_score = sum(scores) / len(scores) if scores else 0
            overall_risk = calculate_risk_level(overall_score)
            overall_risk['score'] = overall_score

            # 조합 수 계산
            total_pairs = len(list(combinations(matched_drugs, 2)))
            analyzed_pairs = len(set([(i['drug1'], i['drug2']) for i in interactions]))

            return {
                'overall_risk': overall_risk,
                'total_pairs': total_pairs,
                'analyzed_pairs': analyzed_pairs,
                'interactions': interactions,
                'not_found': not_found
            }

    finally:
        # 임시 파일 정리
        if os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)


# 간단한 테스트 함수
def test_ddi_analysis():
    """테스트용 함수"""
    test_drugs = ['Aspirin', 'Metformin', 'Atorvastatin']
    result = analyze_drug_interactions(test_drugs)
    print(result)
    return result


if __name__ == '__main__':
    test_ddi_analysis()
