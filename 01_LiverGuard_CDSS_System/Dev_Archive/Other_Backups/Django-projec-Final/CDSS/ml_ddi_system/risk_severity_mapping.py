"""
위험도 점수 매핑 시스템
각 DDI 타입을 위험도 등급으로 분류

위험도 등급:
- HIGH (80-100): 생명을 위협하는 부작용
- MODERATE (50-79): 심각한 부작용, 관리 필요
- LOW (20-49): 경미한 부작용 또는 약동학적 변화
- BENEFICIAL (0-19): 치료 효과 증가, 독성 감소
"""

RISK_SEVERITY = {
    # 🔴 HIGH RISK (80-100) - 생명 위협적
    1: {"severity": "HIGH", "score": 90, "category": "cardiac"},  # 심부전, 저혈압
    7: {"severity": "HIGH", "score": 95, "category": "muscle"},  # 횡문근융해증, 근육병증
    8: {"severity": "HIGH", "score": 95, "category": "muscle"},  # 횡문근융해증, 근육글로불린뇨
    9: {"severity": "HIGH", "score": 100, "category": "cardiac"},  # QTc 연장, torsade de pointes, 심정지
    24: {"severity": "HIGH", "score": 95, "category": "muscle"},  # 근육병증, 횡문근융해증
    27: {"severity": "HIGH", "score": 90, "category": "respiratory"},  # 호흡억제
    28: {"severity": "HIGH", "score": 95, "category": "muscle"},  # 횡문근융해증
    30: {"severity": "HIGH", "score": 85, "category": "bleeding"},  # 출혈 위험
    42: {"severity": "HIGH", "score": 90, "category": "cardiac"},  # QTc 연장
    53: {"severity": "HIGH", "score": 90, "category": "cardiac"},  # QTc 연장 활동
    54: {"severity": "HIGH", "score": 85, "category": "cardiac"},  # 서맥
    83: {"severity": "HIGH", "score": 85, "category": "renal"},  # 이독성, 신독성
    84: {"severity": "HIGH", "score": 90, "category": "muscle"},  # 근육병증 횡문근융해증
    90: {"severity": "HIGH", "score": 85, "category": "cardiac"},  # 심실 부정맥
    101: {"severity": "HIGH", "score": 85, "category": "muscle"},  # 근육병증
    102: {"severity": "HIGH", "score": 90, "category": "renal"},  # 신부전, 고칼륨혈증
    110: {"severity": "HIGH", "score": 90, "category": "cardiac"},  # 심부전
    112: {"severity": "HIGH", "score": 85, "category": "neurological"},  # 세로토닌 증후군

    # 🟠 MODERATE RISK (50-79) - 심각한 부작용, 관리 필요
    4: {"severity": "MODERATE", "score": 75, "category": "hematologic"},  # 빈혈, 백혈구감소증
    12: {"severity": "MODERATE", "score": 65, "category": "metabolic"},  # 고칼륨혈증
    16: {"severity": "MODERATE", "score": 70, "category": "allergic"},  # 혈관부종
    18: {"severity": "MODERATE", "score": 60, "category": "allergic"},  # 과민반응
    22: {"severity": "MODERATE", "score": 70, "category": "renal"},  # 신독성
    31: {"severity": "MODERATE", "score": 65, "category": "metabolic"},  # 저나트륨혈증
    32: {"severity": "MODERATE", "score": 70, "category": "cardiac"},  # 저혈압, nitritoid 반응
    35: {"severity": "MODERATE", "score": 75, "category": "cardiac"},  # 심장독성
    36: {"severity": "MODERATE", "score": 75, "category": "neurological"},  # 경련
    51: {"severity": "MODERATE", "score": 70, "category": "hematologic"},  # 골수억제
    55: {"severity": "MODERATE", "score": 70, "category": "neuromuscular"},  # 저혈압, 신경근차단
    58: {"severity": "MODERATE", "score": 75, "category": "metabolic"},  # 저혈당
    64: {"severity": "MODERATE", "score": 65, "category": "cardiac"},  # 고혈압
    65: {"severity": "MODERATE", "score": 70, "category": "multi"},  # 저혈압, 신독성, 고칼륨혈증
    69: {"severity": "MODERATE", "score": 65, "category": "neurological"},  # 중추신경독성
    79: {"severity": "MODERATE", "score": 65, "category": "metabolic"},  # 저칼륨혈증
    80: {"severity": "MODERATE", "score": 70, "category": "bleeding"},  # 항응고 증가
    82: {"severity": "MODERATE", "score": 70, "category": "hematologic"},  # 심각한 백혈구감소증
    88: {"severity": "MODERATE", "score": 65, "category": "hematologic"},  # 골수억제
    96: {"severity": "MODERATE", "score": 65, "category": "cardiac"},  # 부정맥
    97: {"severity": "MODERATE", "score": 70, "category": "thrombotic"},  # 혈전 생성
    98: {"severity": "MODERATE", "score": 75, "category": "hepatic"},  # 간독성
    99: {"severity": "MODERATE", "score": 70, "category": "metabolic"},  # 고칼륨혈증
    100: {"severity": "MODERATE", "score": 65, "category": "neurological"},  # 신경독성
    106: {"severity": "MODERATE", "score": 60, "category": "metabolic"},  # 고혈당
    107: {"severity": "MODERATE", "score": 60, "category": "metabolic"},  # 고칼슘혈증
    108: {"severity": "MODERATE", "score": 70, "category": "cardiac"},  # 저혈압
    111: {"severity": "MODERATE", "score": 65, "category": "metabolic"},  # 저나트륨혈증

    # 🟡 LOW RISK (20-49) - 경미한 부작용 또는 약동학적 변화
    2: {"severity": "LOW", "score": 40, "category": "pharmacokinetic"},  # 배설 감소 → 혈청농도 증가
    3: {"severity": "LOW", "score": 40, "category": "pharmacokinetic"},  # 혈청농도 증가
    6: {"severity": "LOW", "score": 35, "category": "pharmacokinetic"},  # 활성대사물 농도 증가
    14: {"severity": "LOW", "score": 30, "category": "mild"},  # 부종
    17: {"severity": "LOW", "score": 35, "category": "pharmacokinetic"},  # 배설 감소
    19: {"severity": "LOW", "score": 30, "category": "mild"},  # 체액 저류
    20: {"severity": "LOW", "score": 35, "category": "pharmacokinetic"},  # 혈청농도 감소
    21: {"severity": "LOW", "score": 45, "category": "cardiovascular"},  # 고혈압
    23: {"severity": "LOW", "score": 30, "category": "pharmacokinetic"},  # 단백결합 감소
    25: {"severity": "LOW", "score": 45, "category": "cns"},  # 저혈압, CNS 억제
    26: {"severity": "LOW", "score": 45, "category": "cns"},  # CNS 억제, 고혈압
    34: {"severity": "LOW", "score": 45, "category": "cns"},  # CNS 억제
    37: {"severity": "LOW", "score": 30, "category": "cns"},  # 자극 활동 증가
    38: {"severity": "LOW", "score": 40, "category": "sedation"},  # 진정, 졸림
    39: {"severity": "LOW", "score": 35, "category": "cardiovascular"},  # 혈관수축
    41: {"severity": "LOW", "score": 40, "category": "neuromuscular"},  # 신경근 부작용
    43: {"severity": "LOW", "score": 35, "category": "immunologic"},  # 면역억제
    45: {"severity": "LOW", "score": 30, "category": "psychiatric"},  # 항정신병 활동
    46: {"severity": "LOW", "score": 30, "category": "mild"},  # 체액 저류
    47: {"severity": "LOW", "score": 35, "category": "cardiovascular"},  # 항고혈압
    48: {"severity": "LOW", "score": 25, "category": "pharmacokinetic"},  # 흡수 감소
    52: {"severity": "LOW", "score": 40, "category": "cardiovascular"},  # 고혈압, 혈관수축
    56: {"severity": "LOW", "score": 30, "category": "pharmacokinetic"},  # 흡수 증가
    57: {"severity": "LOW", "score": 40, "category": "cardiovascular"},  # 기립성 저혈압
    59: {"severity": "LOW", "score": 30, "category": "dermatologic"},  # 광과민성
    61: {"severity": "LOW", "score": 30, "category": "gastrointestinal"},  # 변비
    62: {"severity": "LOW", "score": 35, "category": "respiratory"},  # 기관지수축
    63: {"severity": "LOW", "score": 30, "category": "cardiovascular"},  # 혈관확장
    67: {"severity": "LOW", "score": 35, "category": "metabolic"},  # 저칼슘혈증
    70: {"severity": "LOW", "score": 35, "category": "bleeding"},  # 항혈소판
    71: {"severity": "LOW", "score": 35, "category": "dermatologic"},  # 피부 부작용
    72: {"severity": "LOW", "score": 40, "category": "neuromuscular"},  # 신경근차단
    73: {"severity": "LOW", "score": 30, "category": "gastrointestinal"},  # 궤양 생성
    75: {"severity": "LOW", "score": 40, "category": "cardiovascular"},  # 저혈압
    77: {"severity": "LOW", "score": 25, "category": "pharmacokinetic"},  # 생체이용률 증가
    85: {"severity": "LOW", "score": 35, "category": "anticholinergic"},  # 항콜린성
    86: {"severity": "LOW", "score": 40, "category": "serotonergic"},  # 세로토닌성
    87: {"severity": "LOW", "score": 30, "category": "pharmacokinetic"},  # 배설 증가 → 농도 감소
    89: {"severity": "LOW", "score": 35, "category": "pharmacokinetic"},  # 대사 감소
    91: {"severity": "LOW", "score": 30, "category": "neurological"},  # 신경흥분
    92: {"severity": "LOW", "score": 35, "category": "sedation"},  # 진정
    93: {"severity": "LOW", "score": 35, "category": "ototoxicity"},  # 이독성
    94: {"severity": "LOW", "score": 35, "category": "cardiovascular"},  # 혈관수축
    95: {"severity": "LOW", "score": 35, "category": "metabolic"},  # 저칼륨혈증
    103: {"severity": "LOW", "score": 35, "category": "cardiac"},  # 빈맥
    104: {"severity": "LOW", "score": 30, "category": "pharmacokinetic"},  # 대사 증가
    105: {"severity": "LOW", "score": 25, "category": "pharmacokinetic"},  # 생체이용률 감소
    109: {"severity": "LOW", "score": 35, "category": "cardiac"},  # 서맥
    113: {"severity": "LOW", "score": 40, "category": "general"},  # 일반 부작용

    # 🟢 BENEFICIAL (0-19) - 치료 효과 증가, 독성 감소
    10: {"severity": "BENEFICIAL", "score": 10, "category": "therapeutic"},  # 치료 효과 증가
    11: {"severity": "BENEFICIAL", "score": 10, "category": "therapeutic"},  # 심장독성 감소
    15: {"severity": "BENEFICIAL", "score": 15, "category": "therapeutic"},  # 진정 감소
    29: {"severity": "BENEFICIAL", "score": 10, "category": "therapeutic"},  # 진통 효과 증가
    33: {"severity": "LOW", "score": 30, "category": "pharmacokinetic"},  # 활성대사물 감소 → 효과 감소
    40: {"severity": "LOW", "score": 35, "category": "antiplatelet"},  # 항혈소판 감소
    44: {"severity": "LOW", "score": 25, "category": "neuromuscular"},  # 신경근차단 감소
    49: {"severity": "LOW", "score": 30, "category": "respiratory"},  # 기관지확장 감소
    50: {"severity": "LOW", "score": 35, "category": "anticoagulant"},  # 항응고 감소
    60: {"severity": "LOW", "score": 30, "category": "antihypertensive"},  # 항고혈압 감소
    66: {"severity": "LOW", "score": 30, "category": "diuretic"},  # 이뇨 감소
    68: {"severity": "LOW", "score": 20, "category": "diagnostic"},  # 진단제 효과 감소
    74: {"severity": "LOW", "score": 35, "category": "therapeutic"},  # 치료 효과 감소
    76: {"severity": "LOW", "score": 25, "category": "stimulant"},  # 자극 감소
    78: {"severity": "LOW", "score": 25, "category": "analgesic"},  # 진통 감소
    81: {"severity": "LOW", "score": 30, "category": "vasoconstrictor"},  # 혈관수축 감소
    5: {"severity": "LOW", "score": 45, "category": "cardiac"},  # AV 차단
}


def get_risk_score(interaction_type):
    """
    상호작용 타입 번호로부터 위험도 점수 반환

    Args:
        interaction_type: int, 상호작용 타입 번호 (1-113)

    Returns:
        dict: {severity, score, category}
    """
    return RISK_SEVERITY.get(interaction_type, {
        "severity": "UNKNOWN",
        "score": 50,
        "category": "unknown"
    })


def get_severity_emoji(severity):
    """위험도 등급에 따른 이모지 반환"""
    emoji_map = {
        "HIGH": "🔴",
        "MODERATE": "🟠",
        "LOW": "🟡",
        "BENEFICIAL": "🟢",
        "UNKNOWN": "⚪"
    }
    return emoji_map.get(severity, "⚪")


def calculate_overall_risk(risk_scores):
    """
    여러 상호작용의 전체 위험도 계산

    Args:
        risk_scores: list of int, 위험도 점수 리스트

    Returns:
        tuple: (overall_score, severity_level)
    """
    if not risk_scores:
        return 0, "SAFE"

    # 가장 높은 위험도와 평균을 조합
    max_risk = max(risk_scores)
    avg_risk = sum(risk_scores) / len(risk_scores)

    # 가중 점수 (최대값 70%, 평균 30%)
    overall_score = int(max_risk * 0.7 + avg_risk * 0.3)

    # 등급 결정
    if overall_score >= 80:
        severity = "HIGH"
    elif overall_score >= 50:
        severity = "MODERATE"
    elif overall_score >= 20:
        severity = "LOW"
    else:
        severity = "SAFE"

    return overall_score, severity


def get_korean_description(interaction_type, interaction_sentence):
    """
    상호작용 타입에 대한 한국어 설명 반환
    """
    # 주요 키워드 기반 간단한 한국어 매핑
    keywords_map = {
        "bleeding": "출혈",
        "heart failure": "심부전",
        "hypotension": "저혈압",
        "hypertension": "고혈압",
        "rhabdomyolysis": "횡문근융해증",
        "QTc prolongation": "QTc 연장",
        "cardiac arrest": "심정지",
        "serum concentration": "혈중 농도",
        "excretion": "배설",
        "therapeutic efficacy": "치료 효과",
        "sedation": "진정",
        "hyperkalemia": "고칼륨혈증",
        "hypokalemia": "저칼륨혈증",
        "nephrotoxic": "신독성",
        "hepatotoxic": "간독성",
        "hypoglycemic": "저혈당",
    }

    # 간단한 키워드 매칭
    sentence_lower = interaction_sentence.lower()
    for eng, kor in keywords_map.items():
        if eng in sentence_lower:
            return kor

    return "상호작용"
