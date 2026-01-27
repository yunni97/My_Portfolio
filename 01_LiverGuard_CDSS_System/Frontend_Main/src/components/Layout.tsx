import React, { useState, useEffect } from 'react';
import PatientSidebar from './PatientSidebar';
import Header from './Header';
import MenuBar from './MenuBar';
import { API_BASE_URL } from '../services/apiConfig';
// 필요에 따라 페이지 컴포넌트 import (현재는 children으로 렌더링되므로 주석 처리 가능)
// import LassoCoxTest from '../pages/LassoCoxTest';
// import OrthancViewer from '../pages/OrthancViewer';
// import NewDashboard from '../pages/NewDashboard';

// 의사 데이터 인터페이스 (로그인 정보)
interface DoctorData {
  doctor_id: number;
  name: string;
  email: string;
  phone: string;
  department: string | null;
  position: string | null;
  sex: string;
}

// 환자 데이터 인터페이스 (API 응답 구조에 맞춤)
interface Patient {
  patient_id: number; // DB의 primary key (id 대신 patient_id 사용 권장)
  name: string;
  birth_date: string | null; // "YYYY-MM-DD" 형식 문자열
  sex: string; // 'male' | 'female'
  resident_number: string;
  // 필요하다면 age 계산 로직 추가 또는 API에서 age 필드 제공 필요
}

interface LayoutProps {
  children: React.ReactNode;
  doctor: DoctorData;
  onLogout: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, doctor, onLogout }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [activeTab, setActiveTab] = useState('대시보드'); // 초기 탭 설정 (예: 대시보드)
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 환자 목록 API 호출 함수
  const fetchPatients = async () => {
    setLoading(true);
    try {
      // 실제 백엔드 API 주소
      const response = await fetch(`${API_BASE_URL}/patients/`); 
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // API 응답 구조에 따라 데이터 설정 (예: data.results 또는 data.data.patients)
      // 여기서는 data.data.patients가 배열이라고 가정
      if (data.success && Array.isArray(data.data.patients)) {
         // 만약 'age' 필드가 필요하다면 여기서 birth_date를 기반으로 계산하여 추가
         const patientsWithAge = data.data.patients.map((p: any) => ({
            ...p,
            // 간단한 만 나이 계산 예시 (필요 시 더 정교한 로직 사용)
            age: p.birth_date ? new Date().getFullYear() - new Date(p.birth_date).getFullYear() : 0 
         }));
         setPatients(patientsWithAge);
      } else {
        // 응답 구조가 다른 경우에 대한 처리 (예: 바로 배열인 경우 setPatients(data))
        console.warn("API 응답 형식이 예상과 다릅니다:", data);
        // 임시로 빈 배열 설정 또는 에러 처리
        setPatients([]); 
      }

    } catch (err: any) {
      console.error("환자 목록 로딩 실패:", err);
      setError(err.message || "환자 데이터를 불러오는 중 오류가 발생했습니다.");
      // 에러 발생 시에도 UI가 깨지지 않도록 빈 배열 설정
      setPatients([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  const doctorProfile = {
    name: doctor.name,
    status: 'online', // 상태 표시 (필요에 따라 동적 변경 가능)
    department: doctor.department || '미지정',
  };

  const handlePatientSelect = (patient: Patient) => {
    console.log('선택된 환자:', patient);
    // TODO: 환자 선택 시 전역 상태 관리(Context API, Redux 등)를 통해 선택된 환자 정보 저장
    // 또는 URL 파라미터 변경 등을 통해 상세 페이지로 이동 로직 추가
  };

  const handleTabChange = (tab: string) => {
    console.log('선택된 탭:', tab);
    setActiveTab(tab);
    // TODO: 탭 변경에 따른 라우팅 처리 (useNavigate 등 활용)
  };

  return (
    <div className="app-layout">
      {/* 상단 헤더: 의사 정보 및 로그아웃 버튼 */}
      <Header doctor={doctor} onLogout={onLogout} />
      
      <div className="main-wrapper">
        {/* 좌측 사이드바: 환자 목록 */}
        {/* PatientSidebar 컴포넌트의 props 인터페이스도 Patient 타입에 맞춰 수정 필요할 수 있음 */}
        <PatientSidebar
          doctorProfile={doctorProfile}
          patients={patients}
          onPatientSelect={handlePatientSelect}
          loading={loading} // 로딩 상태 전달 (선택 사항)
        />
        
        <div className="content-wrapper">
          {/* 상단 메뉴바 (탭) */}
          <MenuBar activeTab={activeTab} onTabChange={handleTabChange} />
          
          <div className="container">
            {/* 에러 메시지 표시 (선택 사항) */}
            {error && <div className="error-message" style={{color: 'red', padding: '10px'}}>{error}</div>}
            
            {/* 실제 컨텐츠 렌더링 (Dashboard 등) */}
            {children}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Layout;