# 빠른 시작 가이드

## 시스템 개요

이 시스템은 **버전 2: Hybrid (Rule-based + ML)** 방식으로 구현되었습니다.

### 입력
```
약물 리스트: [A, B, C, D]
```

### 출력
```
전체 위험도: 중간 (45%)
⚠️ A + B: 출혈 위험 85%
✓ C + D: 안전
```

## 1. 즉시 테스트 (설치 불필요)

```bash
cd C:\CDSS\ml_ddi_system
python quick_test.py
```

이 명령은:
- Rule-based 방식으로 즉시 작동
- 222,000개 알려진 상호작용 조회
- ML 모델 없이도 사용 가능

**출력 예시:**
```
[DDI] 약물 상호작용 시스템 - 빠른 테스트

테스트 1: 단일 약물 쌍
Drug 1: Nifedipine (칼슘채널차단제)
Drug 2: Bopindolol (베타차단제)
위험도: 90% (HIGH)
상호작용: 심부전 및 저혈압 위험 증가

테스트 2: 여러 약물 조합
입력: [Nifedipine, Amiloride, Fosinopril]
전체 위험도: MODERATE (60%)
```

## 2. 대화형 모드

```bash
python ddi_analyzer.py
```

그 다음 약물 이름을 입력:
```
약물 입력: aspirin, metformin, statin
```

**지원하는 입력 형식:**
- 약물 이름: `aspirin`, `metformin`
- DrugBank ID: `DB00945`, `DB00331`
- 혼합: `aspirin, DB00331`

## 3. 직접 명령줄 입력

```bash
# 약물 이름으로
python ddi_analyzer.py --drugs "aspirin,metformin,statin"

# DrugBank ID로
python ddi_analyzer.py --drugs "DB00945,DB00331,DB00175"
```

## 4. ML 모델 학습 (선택사항)

더 나은 예측을 위해 ML 모델을 학습시킬 수 있습니다:

```bash
python ml_model.py
```

학습 후:
```bash
python ddi_analyzer.py --model models/ddi_random_forest.pkl --drugs "aspirin,metformin"
```

**학습 시간:**
- 10,000 샘플: ~2-3분
- 50,000 샘플: ~10-15분
- 222,000 샘플 (전체): ~30-60분

## 5. 실제 사용 예제

### 예제 1: 고혈압 환자

```bash
python ddi_analyzer.py --drugs "amlodipine,atenolol,enalapril"
```

**출력:**
```
[DDI] 약물 상호작용 위험도 분석

[LOW] 전체 위험도: LOW (35%)
총 상호작용: 2개
고위험 조합: 0개

[SUMMARY] 모든 약물 조합 분석

[LOW] Amlodipine + Atenolol
  위험도: 40% (LOW)
  - 저혈압 위험 경미하게 증가

[SAFE] Amlodipine + Enalapril
  알려진 상호작용 없음

[LOW] Atenolol + Enalapril
  위험도: 35% (LOW)
  - 혈압 강하 효과 증가
```

### 예제 2: 당뇨병 환자

```bash
python ddi_analyzer.py --drugs "metformin,glipizide,aspirin"
```

**출력:**
```
[DDI] 약물 상호작용 위험도 분석

[MODERATE] 전체 위험도: MODERATE (60%)
총 상호작용: 2개
고위험 조합: 0개

[WARNING] 중간 위험 조합

[MODERATE] Metformin + Aspirin
  위험도: 75% (MODERATE)
  - 저혈당 위험 증가
```

## 6. 배치 처리

여러 약물 조합을 파일로 처리:

1. `drugs.txt` 파일 생성:
```
aspirin, metformin
amlodipine, atenolol, enalapril
nifedipine, metoprolol
```

2. 실행:
```bash
python ddi_analyzer.py --input drugs.txt --output results.txt
```

## 위험도 등급

- **[HIGH] 80-100%**: 🔴 생명 위협 (횡문근융해증, 심정지 등)
- **[MODERATE] 50-79%**: 🟠 심각한 부작용 (출혈, 저혈당 등)
- **[LOW] 20-49%**: 🟡 경미한 부작용
- **[SAFE] 0-19%**: 🟢 안전 또는 유익

## 주의사항

⚠️ **이 시스템은 의학적 자문을 대체하지 않습니다**
- 실제 처방 전에 반드시 의사/약사와 상담
- 참고 용도로만 사용

## 문제 해결

### 약물을 찾을 수 없다고 나옵니다
→ 약물 이름을 영문으로 입력하거나 DrugBank ID 사용

### 메모리 부족 오류
→ 약물 유사도 매트릭스가 큽니다. 시스템 메모리 확인

### ML 모델 학습이 너무 느립니다
→ `ml_model.py`에서 `sample_size`를 줄이세요 (예: 10000)

## 다음 단계

1. ✅ 기본 사용법 익히기 (이 가이드)
2. 📖 [README.md](README.md) 상세 문서 읽기
3. 🤖 ML 모델 학습으로 예측력 향상
4. 🔧 실제 환자 데이터에 적용

## 지원

- 이슈: GitHub Issues
- 문서: [README.md](README.md)
- 테스트: [quick_test.py](quick_test.py)
