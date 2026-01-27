// src/pages/NurseDashboard.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../services/apiConfig';

interface NurseData {
  nurse_id: number;
  name: string;
  email: string;
  department: string | null;
}

interface NurseDashboardProps {
  nurse: NurseData;
}

interface Patient {
  patient_id: number;
  name: string;
  birth_date: string;
  sex: string;
  phone?: string;
  resident_number?: string;
  created_at?: string;
}

const NurseDashboard: React.FC<NurseDashboardProps> = ({ nurse }) => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [uploadStatus, setUploadStatus] = useState<string>('');
  const [uploading, setUploading] = useState(false);

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
      console.error('환자 목록 로드 실패:', error);
      setLoading(false);
    }
  };

  const filteredPatients = patients.filter(p =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.resident_number?.includes(searchQuery)
  );

  // DICOM 파일 업로드 핸들러
  const handleDicomUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;
    if (!selectedPatient) {
      alert('먼저 환자를 선택해주세요.');
      return;
    }

    setUploading(true);
    setUploadStatus('업로드 중...');

    try {
      const formData = new FormData();

      // 여러 파일을 FormData에 추가
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }
      formData.append('patient_id', selectedPatient.patient_id.toString());

      const response = await fetch(`${API_BASE_URL}/dicom-upload-folder/`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (data.status === 'success') {
        setUploadStatus(`✅ ${files.length}개 파일 업로드 성공!`);
        setTimeout(() => setUploadStatus(''), 3000);
      } else {
        setUploadStatus(`❌ 업로드 실패: ${data.message}`);
      }
    } catch (error) {
      console.error('DICOM 업로드 오류:', error);
      setUploadStatus('❌ 업로드 중 오류가 발생했습니다.');
    } finally {
      setUploading(false);
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
    <div className="dashboard-grid">
      {/* ========== 좌측 패널: 간호사 정보 ========== */}
      <div className="left-panel">
        <div className="doctor-profile">
          <div className="doctor-avatar">👩‍⚕️</div>
          <div className="profile-name">{nurse.name} 간호사</div>
          <div className="doctor-info">
            <div className="info-item">
              <span>🏥</span>
              <span>{nurse.department || '부서 미정'}</span>
            </div>
            <div className="info-item">
              <span>📧</span>
              <span>{nurse.email}</span>
            </div>
            <div className="info-item">
              <span>🆔</span>
              <span>ID: {nurse.nurse_id}</span>
            </div>
          </div>
        </div>

        {/* 간호사 업무 메뉴 */}
        <div className="announcement-card">
          <div className="announcement-header">
            <span className="announcement-title">📋 간호사 업무</span>
          </div>
          <div style={{ padding: '12px' }}>
            <button
              className="btn btn-primary btn-full"
              style={{ marginBottom: '8px' }}
              onClick={() => navigate('/patients/add')}
            >
              + 환자 등록
            </button>

            <button
              className="btn btn-secondary btn-full"
              style={{ marginBottom: '8px' }}
              disabled={!selectedPatient} // 환자가 선택되지 않으면 비활성화
              onClick={() => {
                if (selectedPatient) {
                  navigate(`/patients/${selectedPatient.patient_id}/edit`);
                } else {
                  alert("수정할 환자를 목록에서 선택해주세요.");
                }
              }}
            >
              ✏️ 환자 기록 수정
            </button>
            
            <button
              className="btn btn-full"
              style={{ background: '#8B5CF6', color: 'white' }}
              disabled={!selectedPatient}
              onClick={() => {
                if (selectedPatient) {
                  console.log('Navigating to DICOM:', `/dicom/${selectedPatient.patient_id}`);
                  navigate(`/dicom/${selectedPatient.patient_id}`);
                } else {
                  alert('먼저 환자를 선택해주세요.');
                }
              }}
            >
              🔬 DICOM 분석
            </button>
          </div>
        </div>

        {/* 업로드 안내 */}
        <div className="calendar-card" style={{ flex: 1 }}>
          <div className="cal-header">
            <span className="cal-title">📤 DICOM 업로드 안내</span>
          </div>
          <div style={{ padding: '16px', fontSize: '13px', color: '#6b7280' }}>
            <p style={{ marginBottom: '8px' }}>• 환자를 먼저 선택하세요</p>
            <p style={{ marginBottom: '8px' }}>• DICOM 파일(.dcm)만 업로드 가능</p>
            <p style={{ marginBottom: '8px' }}>• 여러 파일 동시 업로드 지원</p>
            <p>• 업로드 후 자동으로 Orthanc PACS에 저장됩니다</p>
          </div>
        </div>
      </div>

      {/* ========== 중앙 패널: 환자 목록 ========== */}
      <div className="center-panel">
        <div className="patient-list-card">
          <div className="patient-list-header">
            <span className="patient-list-title">환자 목록</span>
            <span className="badge-count">{patients.length}명</span>
            <input
              type="text"
              className="search-input"
              placeholder="환자 검색"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {filteredPatients.length > 0 ? (
            <div style={{ overflow: 'auto', flex: 1 }}>
              <table className="table">
                <thead>
                  <tr>
                    <th style={{ width: '50px' }}>No.</th>
                    <th>성명</th>
                    <th>주민번호</th>
                    <th>등록일</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPatients.map((patient, idx) => (
                    <tr
                      key={patient.patient_id}
                      onClick={() => {
                        setSelectedPatient({...patient});
                      }}
                      className={selectedPatient?.patient_id === patient.patient_id ? 'selected' : ''}
                      style={{ cursor: 'pointer' }}
                    >
                      <td><span className="patient-id">{idx + 1}</span></td>
                      <td>{patient.name}</td>
                      <td>{patient.resident_number || '-'}</td>
                      <td>{patient.created_at ? new Date(patient.created_at).toLocaleDateString('ko-KR') : '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <p className="empty-state-text">등록된 환자가 없습니다.</p>
            </div>
          )}
        </div>
      </div>

      {/* ========== 우측 패널: 환자 정보 & DICOM 업로드 ========== */}
      <div className="right-panel">
        {/* 선택된 환자 정보 */}
        <div className="detail-card">
          <div className="detail-title">선택된 환자</div>

          {selectedPatient ? (
            <div className="detail-grid" style={{ gap: '12px' }}>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">환자 ID</div>
                <div className="detail-val">{selectedPatient.patient_id}</div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">이름</div>
                <div className="detail-val">{selectedPatient.name}</div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">생년월일</div>
                <div className="detail-val">{selectedPatient.birth_date || '-'}</div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">성별</div>
                <div className="detail-val">
                  {selectedPatient.sex === 'male' ? (
                    <span style={{ color: '#1976d2', fontWeight: 500 }}>남성</span>
                  ) : selectedPatient.sex === 'female' ? (
                    <span style={{ color: '#c2185b', fontWeight: 500 }}>여성</span>
                  ) : (
                    selectedPatient.sex || '-'
                  )}
                </div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">연락처</div>
                <div className="detail-val">{selectedPatient.phone || '-'}</div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
              환자를 선택해주세요
            </div>
          )}
        </div>

        {/* DICOM 파일 업로드 */}
        <div className="image-board">
          <div className="image-head">
            <span className="tag">DICOM Upload</span>
          </div>

          <div style={{ padding: '20px' }}>
            {!selectedPatient ? (
              <div style={{ textAlign: 'center', color: '#6b7280', padding: '40px 0' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📁</div>
                <p>환자를 먼저 선택해주세요</p>
              </div>
            ) : (
              <div>
                <div style={{
                  border: '2px dashed #4b5563',
                  borderRadius: '8px',
                  padding: '40px',
                  textAlign: 'center',
                  background: '#1f2937',
                  marginBottom: '16px'
                }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>📤</div>
                  <p style={{ color: '#9ca3af', marginBottom: '16px' }}>
                    DICOM 파일을 선택하거나 드래그하세요
                  </p>
                  <label
                    htmlFor="dicom-upload"
                    className="btn btn-primary"
                    style={{ cursor: 'pointer', display: 'inline-block' }}
                  >
                    {uploading ? '업로드 중...' : '파일 선택'}
                  </label>
                  <input
                    id="dicom-upload"
                    type="file"
                    multiple
                    accept=".dcm"
                    onChange={handleDicomUpload}
                    style={{ display: 'none' }}
                    disabled={uploading}
                  />
                </div>

                {uploadStatus && (
                  <div style={{
                    padding: '12px',
                    background: uploadStatus.startsWith('✅') ? '#10b981' : '#ef4444',
                    color: 'white',
                    borderRadius: '6px',
                    textAlign: 'center',
                    fontSize: '14px'
                  }}>
                    {uploadStatus}
                  </div>
                )}

                <div style={{ marginTop: '16px', fontSize: '12px', color: '#6b7280' }}>
                  <p>📌 업로드 안내:</p>
                  <ul style={{ paddingLeft: '20px', marginTop: '8px' }}>
                    <li>DICOM 파일(.dcm)만 업로드 가능합니다</li>
                    <li>여러 파일을 한번에 선택할 수 있습니다</li>
                    <li>업로드된 파일은 Orthanc PACS에 자동 저장됩니다</li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NurseDashboard;
