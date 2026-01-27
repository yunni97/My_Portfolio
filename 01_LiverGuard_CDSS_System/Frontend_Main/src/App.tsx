import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './App.css';
import { API_BASE_URL, ADMIN_URL } from './services/apiConfig';

// 페이지 및 컴포넌트 import
import Dashboard from './pages/Dashboard';
import PatientList from './pages/PatientList';
import PatientDetail from './pages/PatientDetail';
import PatientForm from './pages/PatientForm'; // 새로 추가한 탭 기반 폼
import DicomAnalysis from './pages/DicomAnalysis';
import SurvivalAnalysis from './pages/SurvivalAnalysis';
import LassoCoxTest from './pages/LassoCoxTest';
import OrthancViewer from './pages/OrthancViewer';
import DoctorProfile from './pages/DoctorProfile';
import Layout from './components/Layout';

// 간호사 관련 import
import NurseDashboard from './pages/NurseDashboard';
import NurseProfile from './pages/NurseProfile';
import NurseLayout from './components/NurseLayout';

// Hero 이미지
const HERO_IMAGES = [
  "https://images.unsplash.com/photo-1579684385127-1ef15d508118?q=80&w=2080&auto=format&fit=crop",
  "https://images.unsplash.com/photo-1530026405186-ed1f139313f8?q=80&w=2000&auto=format&fit=crop"
];

// Doctor 타입 정의
interface DoctorData {
  doctor_id: number;
  name: string;
  email: string;
  phone: string;
  department: string | null;
  department_code: string | null;
  position: string | null;
  status: string;
  sex: string;
}

// Nurse 타입 정의
interface NurseData {
  nurse_id: number;
  name: string;
  email: string;
  phone: string;
  department: string | null;
  department_code: string | null;
  position: string | null;
  status: string;
  sex: string;
}

// Hero 컴포넌트 (로그인 페이지 좌측)
const Hero: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % HERO_IMAGES.length);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  return (
    <section className="relative w-full lg:w-1/2 h-screen overflow-hidden flex items-center justify-center">
      <div className="absolute inset-0 z-0">
        {HERO_IMAGES.map((src, index) => (
          <div
            key={src}
            className={`absolute inset-0 transition-opacity duration-[1500ms] ease-in-out ${
              index === currentIndex ? "opacity-100" : "opacity-0"
            }`}
          >
            <img
              src={src}
              alt="Medical background"
              className="absolute inset-0 w-full h-full object-cover"
            />
          </div>
        ))}

        <div className="absolute inset-0 bg-black/50 z-10" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30 z-10" />
      </div>

      <div className="relative z-20 px-12 text-left max-w-xl">
        <div className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-blue-500/10 border border-blue-500/20 mb-6 backdrop-blur-sm animate-fade-up">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
          </span>
          <span className="text-blue-500 text-xs font-semibold tracking-wide uppercase">
            Deep Learning Project
          </span>
        </div>

        <h1 className="text-4xl lg:text-6xl font-bold text-white tracking-tight leading-[1.1] animate-fade-up">
          AI-Powered Liver Cancer
          <span className="block text-transparent bg-clip-text bg-gradient-to-r from-blue-200 to-white">
            Survival Prediction
          </span>
        </h1>
      </div>
    </section>
  );
};


// 로그인 섹션 컴포넌트
const LoginSection: React.FC = () => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [userType, setUserType] = useState<'doctor' | 'nurse'>('doctor'); // 의사/간호사 선택

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // 의사/간호사에 따라 다른 엔드포인트 호출
      const endpoint = userType === 'doctor'
        ? `${API_BASE_URL}/auth/login/`
        : `${API_BASE_URL}/auth/nurse-login/`;

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId, password }),
      });

      const data = await response.json();

      if (data.success) {
        if (userType === 'doctor') {
          // localStorage에 의사 정보 저장
          localStorage.setItem('userType', 'doctor');
          localStorage.setItem('doctorId', data.data.doctor_id.toString());
          localStorage.setItem('doctorEmail', data.data.email);
          localStorage.setItem('doctorName', data.data.name);
          localStorage.setItem('doctorData', JSON.stringify(data.data));
          // Dashboard로 이동
          window.location.href = '/dashboard';
        } else {
          // localStorage에 간호사 정보 저장
          localStorage.setItem('userType', 'nurse');
          localStorage.setItem('nurseId', data.data.nurse_id.toString());
          localStorage.setItem('nurseEmail', data.data.email);
          localStorage.setItem('nurseName', data.data.name);
          localStorage.setItem('nurseData', JSON.stringify(data.data));
          // 간호사 대시보드로 이동
          window.location.href = '/nurse-dashboard';
        }
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다. Django 서버가 실행 중인지 확인해주세요.');
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="
    relative z-[999]
    w-full lg:w-1/2
    min-h-screen
    bg-slate-900
    flex flex-col
    justify-center
    p-6 lg:p-12
    overflow-y-auto
  "
>
      <div className="w-full max-w-md">
        <div className="text-center mb-10">
          <h2 className="text-2xl lg:text-3xl font-bold text-white mb-2">
            {userType === 'doctor' ? '의사 로그인' : '간호사 로그인'}
          </h2>
          <p className="text-gray-400">간암 생존 예측 시스템에 접속하세요</p>
        </div>

        {/* 의사/간호사 선택 탭 */}
        <div className="flex gap-2 mb-6 p-1 bg-slate-800 rounded-lg">
          <button
            type="button"
            onClick={() => setUserType('doctor')}
            className={`flex-1 py-2.5 px-4 rounded-md text-sm font-medium transition-all ${
              userType === 'doctor'
                ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/50'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            👨‍⚕️ 의사
          </button>
          <button
            type="button"
            onClick={() => setUserType('nurse')}
            className={`flex-1 py-2.5 px-4 rounded-md text-sm font-medium transition-all ${
              userType === 'nurse'
                ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/50'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            👩‍⚕️ 간호사
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="userId" className="block text-sm font-medium text-gray-300 mb-2">
              아이디 (Username)
            </label>
            <input
              id="userId"
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
              placeholder="관리자 아이디를 입력하세요"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
              비밀번호
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 transition-all"
              placeholder="••••••••"
              required
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <a href="#" className="text-blue-400 hover:text-blue-300 transition-colors">
              아이디 찾기
            </a>
            <a href="#" className="text-blue-400 hover:text-blue-300 transition-colors">
              비밀번호 찾기
            </a>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-all duration-300 hover:scale-[1.02] shadow-lg hover:shadow-blue-500/50 disabled:hover:scale-100"
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <div className="mt-8 text-center">
          <p className="text-gray-400 text-sm">
            계정이 없으신가요?{' '}
            <a
              href={ADMIN_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 font-medium transition-colors"
            >
              관리자 로그인 진행
            </a>
          </p>
        </div>
      </div>
    </section>
  );
};

// 로그인 페이지 래퍼
const LoginPage: React.FC = () => {
  return (
    <div className="font-sans antialiased bg-slate-900 selection:bg-blue-500/30 h-screen overflow-hidden flex flex-row">
      <Hero />
      <LoginSection />
    </div>
  );
};

// 메인 앱 컴포넌트
export default function App() {
  const [doctorData, setDoctorData] = useState<DoctorData | null>(null);
  const [nurseData, setNurseData] = useState<NurseData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // localStorage에서 사용자 정보 확인
    const userType = localStorage.getItem('userType');

    if (userType === 'doctor') {
      const storedData = localStorage.getItem('doctorData');
      if (storedData) {
        setDoctorData(JSON.parse(storedData));
      }
    } else if (userType === 'nurse') {
      const storedData = localStorage.getItem('nurseData');
      if (storedData) {
        setNurseData(JSON.parse(storedData));
      }
    }

    setIsLoading(false);
  }, []);

  const handleLogout = () => {
    // 의사와 간호사 정보 모두 제거
    localStorage.removeItem('userType');
    localStorage.removeItem('doctorId');
    localStorage.removeItem('doctorEmail');
    localStorage.removeItem('doctorName');
    localStorage.removeItem('doctorData');
    localStorage.removeItem('nurseId');
    localStorage.removeItem('nurseEmail');
    localStorage.removeItem('nurseName');
    localStorage.removeItem('nurseData');
    setDoctorData(null);
    setNurseData(null);
    window.location.href = '/';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* 로그인 없이 접근 가능한 테스트 페이지 */}
        <Route path="/test/lasso-cox" element={<LassoCoxTest />} />
        <Route path="/test/orthanc-viewer" element={<OrthancViewer />} />

        {/* 로그인하지 않은 경우 */}
        {!doctorData && !nurseData ? (
          <>
            <Route path="/" element={<LoginPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </>
        ) : null}

        {/* 간호사 라우팅 */}
        {nurseData ? (
          <>
            <Route
              path="/nurse-dashboard"
              element={
                <NurseLayout nurse={nurseData} onLogout={handleLogout}>
                  <NurseDashboard nurse={nurseData} />
                </NurseLayout>
              }
            />
            <Route
              path="/nurse-profile"
              element={
                <NurseLayout nurse={nurseData} onLogout={handleLogout}>
                  <NurseProfile nurse={nurseData} />
                </NurseLayout>
              }
            />
            {/* 간호사도 환자 등록 가능 */}
            <Route
              path="/patients/add"
              element={
                <NurseLayout nurse={nurseData} onLogout={handleLogout}>
                  <PatientForm />
                </NurseLayout>
              }
            />
            {/* 간호사 환자 정보 수정 라우트 */}
            <Route
              path="/patients/:id/edit"
              element={
                <NurseLayout nurse={nurseData} onLogout={handleLogout}>
                  <PatientForm />
                </NurseLayout>
              }
            />
            {/* 간호사도 DICOM 분석 접근 가능 */}
            <Route
              path="/dicom/:patientId?"
              element={
                <NurseLayout nurse={nurseData} onLogout={handleLogout}>
                  <DicomAnalysis />
                </NurseLayout>
              }
            />
            <Route path="/" element={<Navigate to="/nurse-dashboard" replace />} />
            <Route path="*" element={<Navigate to="/nurse-dashboard" replace />} />
          </>
        ) : null}

        {/* 의사 라우팅 */}
        {doctorData ? (
          <>
            {/* 대시보드 */}
            <Route
              path="/dashboard"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <Dashboard doctor={doctorData} />
                </Layout>
              }
            />
            
            {/* 의사 프로필 */}
            <Route
              path="/profile"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <DoctorProfile doctor={doctorData} />
                </Layout>
              }
            />

            {/* 환자 목록 */}
            <Route
              path="/patients"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <PatientList />
                </Layout>
              }
            />

            {/* 환자 등록 (PatientForm 사용) */}
            <Route
              path="/patients/add"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <PatientForm />
                </Layout>
              }
            />

            {/* 환자 정보 수정 (PatientForm 사용) */}
            <Route
              path="/patients/:id/edit"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <PatientForm />
                </Layout>
              }
            />

            {/* 환자 상세 보기 */}
            <Route
              path="/patients/:id"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <PatientDetail />
                </Layout>
              }
            />

            {/* 진료 기록 (임시 페이지) */}
            <Route
              path="/records"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <div className="card">
                    <div className="card-header">📋 진료 기록</div>
                    <div className="card-body">
                      <p style={{ color: '#586069' }}>진료 기록 목록이 여기에 표시됩니다.</p>
                    </div>
                  </div>
                </Layout>
              }
            />

            {/* DICOM 분석 */}
            <Route
              path="/dicom/:patientId?"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <DicomAnalysis />
                </Layout>
              }
            />
            <Route
              path="/dicom"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <DicomAnalysis />
                </Layout>
              }
            />

            {/* 생존 분석 */}
            <Route
              path="/survival/:patientId?"
              element={
                <Layout doctor={doctorData} onLogout={handleLogout}>
                  <SurvivalAnalysis />
                </Layout>
              }
            />

            {/* 기본 리다이렉트 */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </>
        ) : null}
      </Routes>
    </BrowserRouter>
  );
}