// src/pages/PatientList.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../services/apiConfig';

interface Patient {
  patient_id: number;
  name: string;
  birth_date: string;
  sex: string;
  phone: string;
  resident_number?: string;
  address?: string;
  diagnosis_date?: string;
  created_at: string;
  updated_at?: string;
}

const PatientList: React.FC = () => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchPatients();
  }, []);

  const fetchPatients = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/patients/`);
      const data = await response.json();
      if (data.success) {
        setPatients(data.data.patients);
      }
      setLoading(false);
    } catch (error) {
      console.error('환자 목록 조회 실패:', error);
      setLoading(false);
    }
  };

  const filteredPatients = patients.filter(
    (patient) =>
      patient.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      patient.phone?.includes(searchTerm)
  );

  const handleDelete = async (patientId: number, patientName: string) => {
    if (!window.confirm(`"${patientName}" 환자를 정말 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.`)) return;

    try {
      const response = await fetch(`${API_BASE_URL}/patients/${patientId}/delete/`, {
        method: 'DELETE'
      });
      const data = await response.json();
      if (data.success) {
        setPatients(patients.filter((p) => p.patient_id !== patientId));
        alert('삭제되었습니다.');
      }
    } catch (error) {
      console.error('삭제 실패:', error);
      alert('삭제에 실패했습니다.');
    }
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="doctor-avatar">🏥</div>
        <div style={{ fontSize: '14px', fontWeight: 600, marginTop: '16px' }}>Loading...</div>
      </div>
    );
  }

  return (
    <div style={{ height: 'calc(100vh - 50px - 28px)', display: 'flex', flexDirection: 'column' }}>
      {/* 헤더 영역 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexShrink: 0 }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#24292e', display: 'flex', alignItems: 'center', gap: '8px' }}>
          👥 환자 목록
          <span className="badge-count">{patients.length}명</span>
        </h2>
        <button
          className="btn btn-primary"
          onClick={() => navigate('/patients/add')}
        >
          ➕ 환자 추가
        </button>
      </div>

      {/* 검색 */}
      <div className="card" style={{ marginBottom: '12px', flexShrink: 0 }}>
        <div className="card-body" style={{ padding: '10px 16px' }}>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <input
              type="text"
              className="form-control"
              placeholder="환자명 또는 주민번호로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ maxWidth: '350px' }}
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                style={{ background: 'none', border: 'none', color: '#999', cursor: 'pointer', fontSize: '14px' }}
              >
                ✕ 초기화
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 테이블 - flex:1로 남은 공간 채움 */}
      <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div className="card-body" style={{ padding: 0, flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          {filteredPatients.length > 0 ? (
            <div style={{ overflow: 'auto', flex: 1 }}>
              <table className="table">
                <thead style={{ position: 'sticky', top: 0, background: '#fafbfc', zIndex: 1 }}>
                  <tr>
                    <th style={{ width: '50px' }}>No.</th>
                    <th style={{ width: '100px' }}>이름</th>
                    <th style={{ width: '110px' }}>생년월일</th>
                    <th style={{ width: '70px' }}>성별</th>
                    <th style={{ width: '130px' }}>연락처</th>
                    <th style={{ width: '100px' }}>등록일</th>
                    <th style={{ textAlign: 'center' }}>관리</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPatients.map((patient, index) => (
                    <tr key={patient.patient_id}>
                      <td><span className="patient-id">{index + 1}</span></td>
                      <td style={{ fontWeight: 500 }}>{patient.name}</td>
                      <td>{patient.birth_date}</td>
                      <td>
                        {patient.sex === 'male' ? (
                          <span className="badge badge-male">남성</span>
                        ) : (
                          <span className="badge badge-female">여성</span>
                        )}
                      </td>
                      <td>{patient.phone || '-'}</td>
                      <td>{patient.created_at ? new Date(patient.created_at).toLocaleDateString('ko-KR') : '-'}</td>
                      <td>
                        <div style={{ display: 'flex', gap: '4px', justifyContent: 'center' }}>
                          <button
                            className="btn btn-outline-primary btn-sm"
                            onClick={() => navigate(`/patients/${patient.patient_id}`)}
                            title="상세보기"
                          >
                            👁️ 상세
                          </button>
                          <button
                            className="btn btn-sm"
                            style={{ background: '#ffc107', color: '#212529' }}
                            onClick={() => navigate(`/patients/${patient.patient_id}/edit`)}
                            title="정보 수정"
                          >
                            ✏️ 수정
                          </button>
                          <button
                            className="btn btn-sm"
                            style={{ background: '#dc3545', color: 'white' }}
                            onClick={() => handleDelete(patient.patient_id, patient.name)}
                            title="삭제"
                          >
                            🗑️ 삭제
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <div className="empty-state-icon">📋</div>
              <p className="empty-state-text">
                {searchTerm ? '검색 결과가 없습니다.' : '등록된 환자가 없습니다.'}
              </p>
              {!searchTerm && (
                <p style={{ fontSize: '13px', color: '#666', marginTop: '8px' }}>
                  오른쪽 상단의 "환자 추가" 버튼을 클릭하세요.
                </p>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 통계 */}
      {filteredPatients.length > 0 && (
        <div style={{
          marginTop: '12px',
          padding: '10px 16px',
          background: '#d1ecf1',
          border: '1px solid #bee5eb',
          borderRadius: '4px',
          fontSize: '13px',
          display: 'flex',
          justifyContent: 'space-between',
          flexShrink: 0
        }}>
          <span>
            전체 <strong style={{ color: '#0366d6' }}>{patients.length}명</strong>의 환자
            {' | '}
            남성 <strong style={{ color: '#1976d2' }}>{patients.filter(p => p.sex === 'male').length}명</strong>
            {' · '}
            여성 <strong style={{ color: '#c2185b' }}>{patients.filter(p => p.sex === 'female').length}명</strong>
          </span>
          {searchTerm && (
            <span>검색 결과 <strong style={{ color: '#0366d6' }}>{filteredPatients.length}명</strong></span>
          )}
        </div>
      )}
    </div>
  );
};

export default PatientList;