"""
약물 상호작용 위험도 점수 시스템
각 상호작용 타입(1-113)에 대해 위험도 점수를 부여 (0-100)
"""

# 위험도 레벨 정의
RISK_LEVELS = {
    'CRITICAL': (85, 100),   # 치명적 (빨강)
    'HIGH': (65, 84),        # 높음 (주황)
    'MEDIUM': (40, 64),      # 중간 (노랑)
    'LOW': (20, 39),         # 낮음 (초록)
    'MINIMAL': (0, 19)       # 최소 (파랑)
}

# 상호작용 타입별 위험도 점수
INTERACTION_RISK_SCORES = {
    # CRITICAL - 생명을 위협하는 상호작용
    9: 95,   # QTc prolongation, torsade de pointes, cardiac arrest
    42: 90,  # QTc prolongation
    90: 88,  # Ventricular arrhythmias

    # HIGH - 심각한 부작용
    1: 80,   # Congestive heart failure, hypotension
    7: 85,   # Myopathy, rhabdomyolysis
    8: 85,   # Rhabdomyolysis, myoglobinuria, elevated CPK
    24: 85,  # Myopathy, rhabdomyolysis, myoglobinuria
    28: 82,  # Rhabdomyolysis
    30: 78,  # Bleeding
    4: 75,   # Anemia, severe leukopenia
    82: 75,  # Severe leukopenia
    88: 72,  # Myelosuppression
    83: 80,  # Ototoxicity, nephrotoxicity
    102: 70, # Renal failure, hyperkalemia
    110: 70, # Heart failure
    112: 75, # Serotonin syndrome

    # MEDIUM-HIGH - 중등도 위험
    16: 65,  # Angioedema
    22: 65,  # Nephrotoxicity
    31: 60,  # Hyponatremia
    32: 68,  # Hypotension, nitritoid reactions
    36: 65,  # Convulsion
    54: 60,  # Bradycardia
    64: 60,  # Hypertension
    79: 55,  # Hypokalemia
    99: 60,  # Hyperkalemia
    108: 62, # Hypotension

    # MEDIUM - 중등도 관리 필요
    2: 50,   # Decreased excretion
    3: 50,   # Increased serum concentration
    6: 52,   # Increased active metabolites
    17: 48,  # Decreased excretion
    20: 55,  # Decreased serum concentration
    25: 58,  # Hypotensive, CNS depressant
    26: 58,  # CNS depressant, hypertensive
    27: 60,  # Respiratory depressant
    34: 56,  # CNS depressant
    35: 65,  # Cardiotoxic
    38: 45,  # Sedation, somnolence
    46: 48,  # Fluid retention
    51: 55,  # Myelosuppressive
    58: 62,  # Hypoglycemic
    69: 50,  # Central neurotoxic
    86: 52,  # Serotonergic
    89: 54,  # Decreased metabolism
    98: 58,  # Hepatotoxic
    104: 50, # Increased metabolism

    # LOW - 경미한 상호작용
    10: 35,  # Increased therapeutic efficacy
    11: 30,  # Decreased cardiotoxicity (유익한 효과)
    13: 40,  # Decreased absorption
    14: 42,  # Edema formation
    15: 25,  # Decreased sedation (유익한 효과)
    18: 38,  # Hypersensitivity reaction
    19: 45,  # Fluid retention
    21: 45,  # Hypertensive
    23: 35,  # Decreased protein binding
    29: 30,  # Increased analgesic (유익한 효과)
    33: 48,  # Reduced active metabolites
    37: 40,  # Stimulatory
    40: 38,  # Decreased antiplatelet
    43: 45,  # Immunosuppressive
    47: 35,  # Antihypertensive
    48: 40,  # Decreased absorption
    56: 42,  # Increased absorption
    60: 35,  # Decreased antihypertensive
    68: 25,  # Decreased diagnostic effectiveness
    70: 35,  # Increased antiplatelet (유익할 수 있음)
    74: 40,  # Decreased therapeutic efficacy
    77: 38,  # Increased bioavailability
    78: 30,  # Decreased analgesic
    87: 42,  # Increased excretion
    105: 40, # Decreased bioavailability

    # MINIMAL - 최소한의 임상적 의미
    5: 18,   # Atrioventricular block
    12: 15,  # Hyperkalemia (경미)
    39: 15,  # Vasoconstricting
    41: 20,  # Adverse neuromuscular
    44: 18,  # Decreased neuromuscular blocking
    45: 22,  # Antipsychotic
    49: 18,  # Decreased bronchodilatory
    50: 20,  # Decreased anticoagulant
    52: 22,  # Hypertensive, vasoconstricting
    53: 20,  # QTc-prolonging
    55: 18,  # Hypotension, neuromuscular blockade
    57: 18,  # Orthostatic hypotensive
    59: 15,  # Photosensitizing
    61: 18,  # Constipating
    62: 20,  # Bronchoconstrictory
    63: 15,  # Vasodilatory
    65: 20,  # Hypotensive, nephrotoxic, hyperkalemic
    66: 18,  # Decreased diuretic
    67: 15,  # Hypocalcemic
    71: 12,  # Dermatologic adverse
    72: 18,  # Neuromuscular blocking
    73: 20,  # Ulcerogenic
    75: 15,  # Hypotensive
    76: 12,  # Decreased stimulatory
    80: 18,  # Anticoagulant
    81: 15,  # Decreased vasoconstricting
    84: 20,  # Myopathic rhabdomyolysis
    85: 18,  # Anticholinergic
    91: 15,  # Neuroexcitatory
    92: 18,  # Sedative
    93: 18,  # Ototoxic
    94: 15,  # Vasopressor
    95: 18,  # Hypokalemic
    96: 20,  # Arrhythmogenic
    97: 18,  # Thrombogenic
    100: 15, # Neurotoxic
    101: 20, # Myopathy
    103: 15, # Tachycardic
    106: 18, # Hyperglycemic
    107: 12, # Hypercalcemic
    109: 18, # Bradycardic
    111: 15, # Hyponatremic
    113: 40, # General adverse effects
}

def get_risk_score(interaction_type: int) -> int:
    """
    상호작용 타입에 대한 위험도 점수 반환

    Args:
        interaction_type: 상호작용 타입 (1-113)

    Returns:
        위험도 점수 (0-100)
    """
    return INTERACTION_RISK_SCORES.get(interaction_type, 50)  # 기본값 50 (중간)


def get_risk_level(score: int) -> str:
    """
    점수에 따른 위험도 레벨 반환

    Args:
        score: 위험도 점수 (0-100)

    Returns:
        위험도 레벨 (CRITICAL, HIGH, MEDIUM, LOW, MINIMAL)
    """
    for level, (min_score, max_score) in RISK_LEVELS.items():
        if min_score <= score <= max_score:
            return level
    return 'MEDIUM'


def get_risk_color(level: str) -> str:
    """
    위험도 레벨에 따른 색상 이모지 반환

    Args:
        level: 위험도 레벨

    Returns:
        색상 이모지
    """
    colors = {
        'CRITICAL': '🔴',
        'HIGH': '🟠',
        'MEDIUM': '🟡',
        'LOW': '🟢',
        'MINIMAL': '🔵'
    }
    return colors.get(level, '⚪')


def get_risk_percentage(score: int) -> int:
    """
    위험도 점수를 퍼센트로 변환

    Args:
        score: 위험도 점수 (0-100)

    Returns:
        위험도 퍼센트 (0-100)
    """
    return score


if __name__ == '__main__':
    # 테스트
    print("상호작용 위험도 점수 시스템 테스트\n")

    test_types = [9, 30, 89, 10, 113]
    for itype in test_types:
        score = get_risk_score(itype)
        level = get_risk_level(score)
        color = get_risk_color(level)
        print(f"Type {itype}: {score}점 - {level} {color}")
