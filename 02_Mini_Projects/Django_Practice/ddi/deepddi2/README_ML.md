# Drug Interaction Analyzer

약물 조합의 상호작용을 분석하고 위험도를 평가하는 시스템입니다.

## 기능

- 여러 약물의 조합을 분석
- 상호작용 위험도 계산 (0-100%)
- 위험도 레벨 분류 (CRITICAL, HIGH, MEDIUM, LOW, MINIMAL)
- 상호작용 설명 제공
- 웹 기반 인터페이스 (Streamlit)

## 설치

```bash
# 필요한 패키지 설치
pip install -r requirements_ml.txt
```

## 사용 방법

### 1. 명령줄 인터페이스 (CLI)

```bash
python drug_interaction_analyzer.py
```

### 2. 웹 인터페이스 (Streamlit)

```bash
streamlit run app_streamlit.py
```

웹 브라우저가 자동으로 열리고 `http://localhost:8501`에서 앱이 실행됩니다.

## 사용 예제

### Python 코드로 직접 사용

```python
from drug_interaction_analyzer import DrugInteractionAnalyzer

# 분석기 초기화
analyzer = DrugInteractionAnalyzer()

# 약물 리스트 입력
drugs = ["Nifedipine", "Sotalol", "Carvedilol"]

# 분석 실행
result = analyzer.analyze_drug_combination(drugs)

# 결과 출력
analyzer.print_analysis_result(result)
```

### 출력 예시

```
================================================================================
Drug Interaction Analysis Result
================================================================================

[HIGH] Overall Risk: HIGH (69.1%)
   Total combinations: 3
   Interactions found: 3
   Safe combinations: 0

================================================================================
Interactions Found (3)
================================================================================

1. [HIGH] Nifedipine + Sotalol
   Risk: HIGH (80%)
   Type: 1
   Description: The risk or severity of congestive heart failure and hypotension
   can be increased when Nifedipine is combined with Sotalol.

2. [HIGH] Nifedipine + Carvedilol
   Risk: HIGH (80%)
   Type: 1
   Description: The risk or severity of congestive heart failure and hypotension
   can be increased when Nifedipine is combined with Carvedilol.

3. [MINIMAL] Sotalol + Carvedilol
   Risk: MINIMAL (18%)
   Type: 57
   Description: Carvedilol may increase the orthostatic hypotensive activities
   of Sotalol.
```

## 파일 구조

```
.
├── drug_interaction_analyzer.py    # 메인 분석 엔진
├── interaction_risk_scorer.py      # 위험도 점수 시스템
├── app_streamlit.py                # 웹 인터페이스
├── requirements_ml.txt             # 필요한 패키지
└── data/
    ├── DrugBank_known_ddi.txt      # 약물 상호작용 데이터
    ├── Approved_drug_Information.txt  # 약물 정보
    └── Type_information/
        └── Interaction_information_model1.csv  # 상호작용 설명
```

## 위험도 레벨

- **CRITICAL (85-100%)**: 생명을 위협할 수 있는 상호작용
  - 예: 심장 부정맥, 급성 신부전 등

- **HIGH (65-84%)**: 심각한 부작용 가능
  - 예: 근육 괴사, 출혈, 간독성 등

- **MEDIUM (40-64%)**: 중등도 관리 필요
  - 예: 약물 농도 변화, CNS 억제 등

- **LOW (20-39%)**: 경미한 상호작용
  - 예: 흡수 감소, 효능 증가 등

- **MINIMAL (0-19%)**: 최소한의 임상적 의미
  - 예: 경미한 부작용 증가

## 데이터 소스

- **DrugBank 5.0**: 2,214개 승인 약물
- **222,127개 약물 상호작용**
- **113개 상호작용 타입**

## 주의사항

⚠️ **면책 조항**: 이 도구는 교육 및 연구 목적으로만 사용됩니다.
실제 의료 결정을 내리기 전에 반드시 의료 전문가와 상담하세요.

## 라이센스

이 프로젝트는 DeepDDI 데이터를 기반으로 합니다.

## 향후 개선 사항

### Level 1 (입문) - 이진 분류
- 상호작용 있음/없음만 예측
- Logistic Regression, Random Forest 사용
- 목표: 정확도 80% 이상

### Level 2 (중급) - 다중 분류
- 어떤 상호작용 타입인지 예측
- XGBoost, LightGBM 사용
- 목표: F1-score 70% 이상

### Level 3 (고급) - 개인화 예측
- 환자 특성 반영 (부작용 프로필, 타겟 효소)
- DNN (Deep Neural Network) 사용
- 목표: ROC-AUC 0.85 이상

### Level 4 (최종) - 현재 구현됨!
- 실시간 처방 지원 시스템 프로토타입
- 웹 인터페이스 (Streamlit)
- 위험도 시각화 + 결과 다운로드
