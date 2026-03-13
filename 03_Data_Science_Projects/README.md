# Data Science Projects

다양한 데이터 분석, 머신러닝, 딥러닝 연구 프로젝트 모음입니다.


## 프로젝트 목록

### 1. R Regression Analysis

R 언어를 활용한 회귀 분석 프로젝트입니다.

**분석 내용:**
- 선형 회귀 (Linear Regression)
- 다중 회귀 분석
- 잔차 분석 및 진단

---

### 2. Time Series Modeling

시계열 데이터 분석 및 예측 모델링 프로젝트입니다.

**주요 모델:**
- ARIMA / SARIMA
- 시계열 예측 모델

---

### 3. Deep Learning Projects

**DeepDDI** - 딥러닝을 활용한 약물 상호작용 예측 연구입니다.

**연구 내용:**
- 약물 분자 구조 임베딩 (SMILES → 벡터)
- 약물 쌍 상호작용 유형 예측 (113가지 DDI 타입)
- Monte Carlo Dropout 기반 불확실성 추정

**사용 기술:**
- Keras (모델 로드 및 예측)
- RDKit (분자 처리, Fingerprint 생성)
- scikit-learn (MultiLabelBinarizer)
- pandas, numpy

**실행 방법:**
```bash
cd Drug_Drug_Interaction/deepddi2
python run_DeepDDI.py --input_file [약물쌍파일]
```

---

## 폴더 구조

```
03_Data_Science_Projects/
└── DeepLearning_Projects/        # 딥러닝 프로젝트
│   └── deepddi2/
│       ├── deepddi/              # 핵심 모듈
│       │   ├── DeepDDI.py        # DDI 예측 (Keras)
│       │   ├── Severity.py       # 심각도 분석
│       │   └── preprocessing.py
│       ├── data/                 # 약물 데이터
│       └── run_DeepDDI.py        # 실행 스크립트

```

---

## 공통 기술 스택

| 분야           | 기술                              |
|-------------- |--------------------------------- |
| **언어**       | Python, R                        |
| **데이터 처리** | pandas, numpy                    |
| **시각화**     | matplotlib, seaborn              |
| **머신러닝**   | scikit-learn                     |
| **딥러닝**     | Keras                            |
| **분자 처리**  | RDKit                            |

---

## 참고 자료

- [DeepDDI Paper](https://www.pnas.org/doi/10.1073/pnas.1803294115)
- [RDKit Documentation](https://www.rdkit.org/docs/)
