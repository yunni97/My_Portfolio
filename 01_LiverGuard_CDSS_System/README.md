# LiverGuard CDSS - AI 기반 간암 진단 보조 시스템


## 프로젝트 개요

**LiverGuard CDSS**는 간암 환자의 **병기 예측**, **재발 예측**, **생존 분석**을 수행하는 임상 의사결정 지원 시스템(Clinical Decision Support System)입니다.


### 주요 기능
- **AI 기반 병기 예측**: CT 영상 + 임상 데이터 + mRNA 유전체를 활용한 멀티모달 분석
- **재발 위험 예측**: XGBoost, RandomForest 기반 재발 확률 예측
- **생존 분석**: Cox 회귀 기반 생존 곡선 및 위험 요인 분석
- **PACS 연동**: Orthanc DICOM 서버와 통합


## 폴더 구조

```
01_LiverGuard_CDSS_System/
├── Backend_Main/             # Django REST API 서버
│   ├── config/               # Django 설정
│   ├── main/                 # 메인 앱 (환자, 의사 모델)
│   ├── ai_app/               # AI 예측 API
│   ├── docker-compose.yaml   # Docker 컨테이너 설정
│   └── requirements.txt
│
├── Frontend_Main/            # React (Vite) 웹 대시보드
│   ├── src/
│   │   ├── pages/            # 페이지 컴포넌트
│   │   ├── components/       # 재사용 컴포넌트
│   │   └── api/              # API 클라이언트
│   └── package.json
│
├── AI_Model_Server/          # BentoML 모델 서빙
│   ├── bentofile.yaml
│   └── service.py
│
└── Dev_Archive/              # 개발 아카이브 (연구/실험 코드)
    ├── Legacy_Django/
    ├── Notebooks_and_Data/
    └── Research_Visualization/
```

---

## 실행 방법

### 1. Backend 서버 실행
```bash
cd Backend_Main
docker-compose up -d   # Django + MySQL + Orthanc 실행
```

### 2. Frontend 개발 서버 실행
```bash
cd Frontend_Main
npm install
npm run dev            # http://localhost:5173
```

### 3. AI Model Server 실행
```bash
cd AI_Model_Server
bentoml serve service:svc
```

---

## 데이터셋 안내

> **데이터셋은 별도 다운로드가 필요합니다.**

| 데이터셋          | 용도         | 다운로드 링크 
|----------------- |------------ |--------------
| **LiTS17**       | 간 분할 학습  | [CodaLab - LiTS Challenge](https://competitions.codalab.org/competitions/17094)
| **HCC-TACE-Seg** | 간암 분할    |  [TCIA - HCC-TACE-Seg](https://wiki.cancerimagingarchive.net/pages/viewpage.action?pageId=70230229)
| **TCGA-LIHC**    | mRNA 유전체  | [GDC Data Portal](https://portal.gdc.cancer.gov/)


### 모델 파일 안내
- **학습된 모델 파일**(.pkl, .pth)은 용량 문제로 포함되지 않았습니다.
- 모델을 사용하려면 `AI_Model_Server/models/` 폴더에 모델 파일을 배치하세요.
- 학습 스크립트는 `Dev_Archive/Notebooks_and_Data/`에서 확인할 수 있습니다.

---

## 기술 스택

### Backend
- **Framework**: Django 4.x, Django REST Framework
- **Database**: MySQL 8.0
- **PACS**: Orthanc DICOM Server
- **Containerization**: Docker, Docker Compose

### Frontend
- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Charts**: Chart.js, react-chartjs-2

### AI/ML
- **Serving**: BentoML
- **Models**: XGBoost, RandomForest, Cox Regression


---
