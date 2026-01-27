import React, { useState } from 'react';
import './PatientSidebar.css';

// 의사 프로필 인터페이스
interface DoctorProfile {
    name: string;
    status: string;
    department: string;
}

// 환자 데이터 인터페이스 (상위 컴포넌트와 일치시킴)
interface Patient {
    patient_id: number;
    name: string;
    birth_date: string | null;
    sex: string; // 'male' | 'female'
    resident_number: string;
    age?: number; // 선택적 속성으로 추가
}

interface PatientSidebarProps {
    doctorProfile: DoctorProfile;
    patients: Patient[];
    onPatientSelect?: (patient: Patient) => void;
    loading?: boolean; // 로딩 상태 prop 추가
}

const PatientSidebar: React.FC<PatientSidebarProps> = ({
    doctorProfile,
    patients,
    onPatientSelect,
    loading = false // 기본값 설정
}) => {
    const [searchTerm, setSearchTerm] = useState('');

    // 검색 필터링 로직
    const filteredPatients = patients.filter(patient =>
        patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (patient.resident_number && patient.resident_number.includes(searchTerm))
    );

    const handlePatientClick = (patient: Patient) => {
        if (onPatientSelect) {
            onPatientSelect(patient);
        }
    };

    return (
        <div className="patient-sidebar">
            {/* 의사 프로필 섹션 */}
            <div className="doctor-profile">
                <div className="doctor-avatar">
                    {doctorProfile.name.charAt(0)}
                </div>
                <div className="doctor-info">
                    <h3 className="doctor-name">{doctorProfile.name}</h3>
                    <p className="doctor-department">{doctorProfile.department}</p>
                    <span className={`doctor-status ${doctorProfile.status.toLowerCase()}`}>
                        {doctorProfile.status}
                    </span>
                </div>
            </div>

            {/* 환자 검색 섹션 */}
            <div className="patient-search">
                <input
                    type="text"
                    placeholder="환자 이름 또는 주민번호"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="search-input"
                />
                {searchTerm && (
                    <button
                        className="clear-search"
                        onClick={() => setSearchTerm('')}
                        aria-label="검색어 지우기"
                    >
                        ✕
                    </button>
                )}
            </div>

            {/* 환자 목록 섹션 */}
            <div className="patient-list">
                <div className="patient-list-header">
                    <h4>환자 목록</h4>
                    <span className="patient-count">
                        {loading ? '-' : `${filteredPatients.length}명`}
                    </span>
                </div>
                
                <div className="patient-list-items">
                    {loading ? (
                        <div className="loading-state">로딩 중...</div>
                    ) : filteredPatients.length > 0 ? (
                        filteredPatients.map(patient => (
                            <div
                                key={patient.patient_id}
                                className="patient-item"
                                onClick={() => handlePatientClick(patient)}
                            >
                                <div className="patient-item-header">
                                    <span className="patient-name">{patient.name}</span>
                                    <span className={`patient-sex ${patient.sex}`}>
                                        {patient.sex === 'male' ? '남' : '여'}
                                    </span>
                                </div>
                                <div className="patient-item-details">
                                    {/* 나이가 계산되어 있다면 표시 */}
                                    {patient.age !== undefined && (
                                        <span className="patient-age">{patient.age}세</span>
                                    )}
                                    <span className="patient-resident">
                                        {patient.resident_number}
                                    </span>
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="no-patients">
                            {searchTerm ? '검색 결과가 없습니다.' : '등록된 환자가 없습니다.'}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PatientSidebar;