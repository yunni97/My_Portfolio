# React Project - Backend API Server

Django REST API server for React Project

## Team Members
- 송영운
- 신종혁
- 정예진
- 장보윤
- 장재호

## Tech Stack
- Django 5.2.7
- Django REST Framework
- MySQL (Database: Dashboard)
- Docker & Docker Compose

## Repository
- Backend: https://github.com/LiverGuardAI/React-project
- Frontend: C:\django_rest\react-frontend

## Database Configuration
- Database: Dashboard
- User: acorn
- Host: 34.67.62.238
- Port: 3306

## Getting Started

### Using Docker
```bash
docker-compose up --build
```

### Manual Setup
```bash
cd reactproject
python manage.py migrate
python manage.py runserver
```

## API Endpoints
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/

## LIBRARY
- requirements.txt
- 터미널에 pip install -r requirements.txt 입력 
