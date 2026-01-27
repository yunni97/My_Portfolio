Flask AI 모델 서버 (flask-ai-apiserver)
본 프로젝트는 통합 CDSS(의사결정지원시스템)의 핵심 AI 모델을 서빙하는 전용 Flask 백엔드 서버입니다.

React/Django 메인 어플리케이션으로부터 API 요청을 받아, 복잡한 AI 연산을 수행하고 결과를 반환합니다.

1. 🎯 주요 기능 (제공 API)
약물 상호작용 (DDI) 예측: 3중 방어 체계(DrugBank, KFDA, AI)를 통해 약물 간 상호작용 위험도를 분석합니다.

생존율 예측 (Cox Model): 환자의 간수치 데이터를 기반으로 Cox 생존 분석 모델을 실행하고 생존 곡선을 반환합니다.

대체 약물 추천: DDI 위험이 감지된 약물에 대해 안전한 대체 약물을 검증하고 추천합니다.

2. 📂 프로젝트 구조
/flask-ai-apiserver/
│
├── data/             # AI 모델용 맵핑 데이터 (.pkl, .csv 등)
├── models/           # AI 모델 파일 (.joblib, .json)
├── services/         # Cox 모델 로직 (get_cox_model_service.py)
│
├── api_v2.py         # [실행] Flask 메인 서버 (모든 API 엔드포인트 포함)
├── ddi_map.py        # DDI 정보 Ground Truth
└── requirements.txt  # (필수) 파이썬 패키지 목록
3. 💾 설치 방법 (Set-up)
저장소 클론 및 이동

Bash

git clone [repository_url]
cd flask-ai-apiserver
가상 환경 생성 및 활성화

Bash

# Windows
python -m venv venv
.\venv\Scripts\activate
필수 패키지 설치

Bash

(venv) pip install -r requirements.txt
[중요] requirements.txt 파일에 한글 주석이 포함된 경우, UTF-8 with BOM 인코딩으로 저장해야 pip 설치 오류가 발생하지 않습니다.

4. 🚀 서버 실행
가상 환경(venv)이 활성화된 터미널에서 아래 명령어를 실행합니다.
git
Bash

(venv) python api_v2.py
서버가 http://127.0.0.1:5000 에서 정상적으로 실행되는지 확인합니다.

--- 1. AI 서버 (Flask, DB연동 v2) 시작 중 ---
...
--- 5. 모든 자산 로드 완료. 서버가 준비되었습니다. ---
--- Windows OS 감지: 'waitress'로 서버를 시작합니다 (http://127.0.0.1:5000) ---