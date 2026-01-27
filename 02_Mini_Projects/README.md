# Mini Projects

다양한 프레임워크와 기술을 학습하기 위해 진행한 미니 프로젝트들입니다.


## 프로젝트 목록

### 1. Restaurant Management

Flask 기반 식당 관리 웹 애플리케이션입니다.

**주요 기능:**
- 업체 등록 및 로그인/로그아웃
- 메뉴 관리 (추가/수정/삭제)
- 매출 조회 및 히트상품 분석
- 메뉴 검색 기능

**사용 기술:**
- Flask, Flask-WTF
- PyMySQL (MySQL 연동)
- Jinja2 템플릿
- Werkzeug (비밀번호 해싱)

**실행 방법:**
```bash
cd Restaurant_Management
pip install flask flask-wtf pymysql
python main.py  # http://localhost:5000
```

---

### 2. Flutter Mobile App

Flutter 기반 간암 환자용 헬스케어 모바일 앱입니다.

**주요 기능:**
- 혈액검사 결과 조회 및 추이 그래프
- 약물 상호작용(DDI) 분석
- 생존 예측 분석
- 병원 지도 및 일정 관리

**사용 기술:**
- Flutter, Dart
- Dio (HTTP 클라이언트)
- Provider (상태 관리)
- Django/Flask API 서버 연동

**실행 방법:**
```bash
cd Flutter_Mobile_App/Flutter-application/dashboard_app
flutter pub get
flutter run
```

---

### 3. Django Practice

Django 기반 CDSS(임상 의사결정 지원 시스템) 연습 프로젝트입니다.

**주요 기능:**
- 의사 로그인/로그아웃
- 환자 관리 (조회/추가/수정/삭제)
- CDSS 관리자 대시보드
- DDI(약물 상호작용) 분석 연동

**사용 기술:**
- Django, Django ORM
- SQLite/MySQL
- Django Template 시스템
- deepddi2 라이브러리 연동

**실행 방법:**
```bash
cd Django_Practice/cdss_project
pip install django
python manage.py runserver
```

---

## 폴더 구조

```
02_Mini_Projects/
├── Restaurant_Management/   # Flask 식당 관리 웹앱
│   ├── main.py              # Flask 메인 앱
│   ├── db_connect/          # DB 연결 모듈
│   ├── sys_module/          # 메뉴 검색 모듈
│   └── templates/           # Jinja2 템플릿
│
├── Flutter_Mobile_App/      # Flutter 모바일 앱
│   ├── Flutter-application/ # 메인 Flutter 앱
│   ├── django-dashboard-apiserver/  # Django API 서버
│   └── flask-ai-apiserver/  # Flask AI API 서버
│
└── Django_Practice/         # Django CDSS 연습
    ├── cdss_project/        # 메인 프로젝트
    ├── cdss_project_1~3/    # 버전별 연습 코드
    └── ddi/                 # DDI 분석 모듈
```

---

## 학습 목표

| 프로젝트               | 학습 포인트                        |
|---------------------- |---------------------------------- |
| Restaurant Management | Flask 웹 개발, MySQL 연동, 세션 관리 |
| Flutter Mobile App    | 크로스플랫폼 앱 개발, API 연동       |
| Django Practice       | Django MTV 패턴, ORM, 인증 시스템   |
