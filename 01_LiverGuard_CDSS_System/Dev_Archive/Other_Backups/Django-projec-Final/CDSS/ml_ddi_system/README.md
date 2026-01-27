# 💊 ML 기반 약물 상호작용 위험도 분석 시스템

## 개요

여러 약물을 동시에 복용할 때의 상호작용 위험도를 자동으로 분석하는 시스템입니다.

### 주요 기능

✅ **입력**: 약물 리스트 [A, B, C, D]
✅ **출력**:
- 전체 위험도 점수 (0-100%)
- 개별 조합별 위험도
- 가장 위험한 조합 강조

### 예시

```
입력: ["메트포르민", "아스피린", "스타틴", "베타차단제"]

출력:
전체 위험도: 중간 (45%)
⚠️ 아스피린 + 메트포르민: 저혈당 위험 30%
✅ 스타틴 + 베타차단제: 안전
```

## 시스템 구조

### 1. Hybrid 예측 시스템

- **Rule-based** (알려진 DDI 데이터 조회)
  - 222,128개의 알려진 약물 상호작용 데이터 활용
  - 즉시 조회, 100% 정확도

- **ML-based** (새로운 조합 예측)
  - Random Forest 모델
  - 약물 구조 유사도 기반 예측
  - 알려지지 않은 조합에 대해서도 예측 가능

### 2. 위험도 점수 시스템

- 🔴 **HIGH (80-100%)**: 생명을 위협하는 부작용
  - 횡문근융해증, 심정지, QTc 연장 등

- 🟠 **MODERATE (50-79%)**: 심각한 부작용, 관리 필요
  - 출혈, 저혈당, 고칼륨혈증 등

- 🟡 **LOW (20-49%)**: 경미한 부작용 또는 약동학적 변화
  - 혈청농도 증가, 진정 효과 등

- 🟢 **BENEFICIAL (0-19%)**: 치료 효과 증가, 독성 감소

## 설치 및 사용

### 1. 필수 패키지 설치

```bash
pip install pandas numpy scikit-learn
```

### 2. 디렉토리 구조

```
ml_ddi_system/
├── risk_severity_mapping.py      # 위험도 점수 매핑
├── data_preprocessing.py          # 데이터 로딩 및 전처리
├── ml_model.py                    # Random Forest 모델
├── hybrid_predictor.py            # Hybrid 예측 시스템
├── ddi_analyzer.py                # 메인 애플리케이션
├── quick_test.py                  # 빠른 테스트
└── models/                        # 학습된 모델 저장
```

### 3. 빠른 테스트 (Rule-based만 사용)

```bash
cd C:\CDSS\ml_ddi_system
python quick_test.py
```

### 4. ML 모델 학습 (선택)

```bash
python ml_model.py
```

학습 시간: 약 10-30분 (샘플 크기에 따라)

### 5. 메인 애플리케이션 사용

#### 대화형 모드

```bash
python ddi_analyzer.py
```

#### 직접 약물 입력

```bash
python ddi_analyzer.py --drugs "aspirin,metformin,statin,atenolol"
```

#### ML 모델 사용

```bash
python ddi_analyzer.py --model models/ddi_random_forest.pkl --drugs "DB00945,DB00188"
```

## 사용 예제

### 예제 1: 고혈압 환자

```python
from ddi_analyzer import DDIAnalyzer

analyzer = DDIAnalyzer()
result = analyzer.analyze_drugs([
    "amlodipine",      # 암로디핀 (칼슘채널차단제)
    "atenolol",        # 아테놀롤 (베타차단제)
    "enalapril"        # 에날라프릴 (ACE 억제제)
])
```

### 예제 2: 당뇨병 환자

```python
result = analyzer.analyze_drugs([
    "metformin",       # 메트포르민
    "glipizide",       # 글리피지드
    "aspirin"          # 아스피린
])
```

## 데이터 소스

- **DrugBank 5.0**: 약물 정보 및 상호작용 데이터
- **113개 상호작용 타입**: 의학적으로 검증된 상호작용 분류
- **약물 구조 유사도**: Tanimoto 계수 기반

## 제한사항

⚠️ **주의사항**:
- 이 시스템은 의학적 자문을 대체하지 않습니다
- 실제 처방 전에 반드시 의사/약사와 상담하세요
- 모든 약물 상호작용을 완벽히 예측할 수는 없습니다

## 성능

- **Rule-based 정확도**: ~100% (알려진 조합)
- **ML 모델 정확도**: ~75-85% (테스트 세트)
- **처리 속도**:
  - Rule-based: 즉시 (< 1초)
  - ML 예측: 약 1-2초

## 향후 개선 사항

- [ ] 더 많은 약물 데이터 추가
- [ ] 딥러닝 모델 (Graph Neural Network) 적용
- [ ] 약물 용량 고려
- [ ] 환자 특성 (나이, 신장/간 기능) 반영
- [ ] Web UI 개발

## 라이센스

이 프로젝트는 교육 및 연구 목적으로 개발되었습니다.

## 문의

버그 리포트 및 기능 제안은 이슈로 등록해주세요.
