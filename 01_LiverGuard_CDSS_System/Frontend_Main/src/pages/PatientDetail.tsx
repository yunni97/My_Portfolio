import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../services/apiConfig';

interface Patient {
  patient_id: number;
  name: string;
  birth_date: string;
  sex: string;
  phone: string;
  address?: string;
  resident_number?: string;
  diagnosis_date?: string;
  created_at?: string;
  updated_at?: string;
}

interface ClinicalRecord {
  clinical_id: number;
  tumor_stage?: string;
  child_pugh?: string;
  afp?: number;
  albumin?: number;
  bilirubin?: number;
  test_date: string;
}

interface GenomicRecord {
  sample_id: number;
  sample_date: string;
  gene_data: any;
}

interface AIPrediction {
  prediction_id: number;
  risk_score: number;
  survival_prob_1yr: number;
  survival_prob_3yr: number;
  analyzed_at: string;
}

const PatientDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'clinical' | 'genomic' | 'dicom'>('clinical');
  const [patient, setPatient] = useState<Patient | null>(null);
  const [clinicalRecords, setClinicalRecords] = useState<ClinicalRecord[]>([]);
  const [genomicRecords, setGenomicRecords] = useState<GenomicRecord[]>([]);
  const [predictions, setPredictions] = useState<AIPrediction[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPatientData();
  }, [id]);

  const fetchPatientData = async () => {
    try {
      // 환자 상세 정보
      const patientResponse = await fetch(`${API_BASE_URL}/patients/${id}/`);
      const patientData = await patientResponse.json();
      if (patientData.success) {
        setPatient(patientData.data.patient);
      }

      // 임상 기록
      const clinicalResponse = await fetch(`${API_BASE_URL}/clinical-records/?patient_id=${id}`);
      const clinicalData = await clinicalResponse.json();
      if (clinicalData.success) {
        setClinicalRecords(clinicalData.data);
      }

      // 유전체 기록
      const genomicResponse = await fetch(`${API_BASE_URL}/genomic-records/?patient_id=${id}`);
      const genomicData = await genomicResponse.json();
      if (genomicData.success) {
        setGenomicRecords(genomicData.data);
      }

      // AI 예측
      const predictionsResponse = await fetch(`${API_BASE_URL}/ai-predictions/?patient_id=${id}`);
      const predictionsData = await predictionsResponse.json();
      if (predictionsData.success) {
        setPredictions(predictionsData.data);
      }

      setLoading(false);
    } catch (error) {
      console.error('환자 데이터 로드 실패:', error);
      setLoading(false);
    }
  };

  const getRiskStyle = (score: number) => {
    if (score >= 0.7) return { background: '#f8d7da', borderColor: '#f5c6cb', color: '#721c24' };
    if (score >= 0.4) return { background: '#fff3cd', borderColor: '#ffeeba', color: '#856404' };
    return { background: '#d4edda', borderColor: '#c3e6cb', color: '#155724' };
  };

  if (loading) {
    return (
      <div className="empty-state">
        <div className="doctor-avatar">🏥</div>
        <div style={{ fontSize: '14px', fontWeight: 600, marginTop: '16px' }}>Loading...</div>
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="empty-state">
        <div className="empty-state-icon">❌</div>
        <p className="empty-state-text">환자를 찾을 수 없습니다.</p>
        <button
          onClick={() => navigate('/patients')}
          className="btn btn-primary btn-sm"
          style={{ marginTop: '12px' }}
        >
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* 헤더 영역 */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#24292e' }}>👤 환자 상세 정보</h2>
        <button onClick={() => navigate('/patients')} className="btn btn-secondary">
          ← 환자 목록으로
        </button>
      </div>

      {/* 기본 정보 카드 */}
      <div className="card" style={{ marginBottom: '16px' }}>
        <div className="card-header" style={{ background: '#2b5876', color: 'white' }}>
          기본 정보
        </div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>환자 ID:</strong>
                <span style={{ color: '#0366d6', fontWeight: 500 }}>{patient.patient_id}</span>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>이름:</strong>
                <span>{patient.name}</span>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>생년월일:</strong>
                <span>{patient.birth_date}</span>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>성별:</strong>
                {patient.sex === 'male' ? (
                  <span className="badge badge-male">남성</span>
                ) : (
                  <span className="badge badge-female">여성</span>
                )}
              </div>
            </div>
            <div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>연락처:</strong>
                <span>{patient.phone}</span>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>주소:</strong>
                <span>{patient.address || '미등록'}</span>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>진단일:</strong>
                <span>{patient.diagnosis_date || '미등록'}</span>
              </div>
              <div style={{ marginBottom: '12px' }}>
                <strong style={{ color: '#586069', fontWeight: 500, display: 'inline-block', minWidth: '100px' }}>등록일:</strong>
                <span>{patient.created_at ? new Date(patient.created_at).toLocaleString('ko-KR') : '-'}</span>
              </div>
            </div>
          </div>

          <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #e1e4e8' }}>
            <button
              className="btn btn-primary btn-sm"
              onClick={() => navigate(`/patients/${patient.patient_id}/edit`)}
            >
              정보 수정
            </button>
          </div>
        </div>
      </div>

      {/* 최근 AI 예측 */}
      {predictions.length > 0 && (
        <div
          className="card"
          style={{
            marginBottom: '16px',
            ...getRiskStyle(predictions[0].risk_score),
            border: `1px solid ${getRiskStyle(predictions[0].risk_score).borderColor}`
          }}
        >
          <div className="card-body">
            <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>⚠️ 최근 AI 예측 결과</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', fontSize: '13px' }}>
              <div>
                <strong>위험도:</strong> {(predictions[0].risk_score * 100).toFixed(1)}%
              </div>
              <div>
                <strong>1년 생존확률:</strong> {(predictions[0].survival_prob_1yr * 100).toFixed(1)}%
              </div>
              <div>
                <strong>3년 생존확률:</strong> {(predictions[0].survival_prob_3yr * 100).toFixed(1)}%
              </div>
            </div>
            <p style={{ fontSize: '11px', marginTop: '8px', opacity: 0.75 }}>
              분석 일시: {predictions[0].analyzed_at}
            </p>
          </div>
        </div>
      )}

      {/* 탭 */}
      <div className="card">
        <div style={{ display: 'flex', borderBottom: '1px solid #e1e4e8' }}>
          <button
            onClick={() => setActiveTab('clinical')}
            style={{
              flex: 1,
              padding: '12px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'clinical' ? '2px solid #0366d6' : '2px solid transparent',
              color: activeTab === 'clinical' ? '#0366d6' : '#586069',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            📊 임상 데이터
          </button>
          <button
            onClick={() => setActiveTab('genomic')}
            style={{
              flex: 1,
              padding: '12px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'genomic' ? '2px solid #0366d6' : '2px solid transparent',
              color: activeTab === 'genomic' ? '#0366d6' : '#586069',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            🧬 유전체 데이터
          </button>
          <button
            onClick={() => setActiveTab('dicom')}
            style={{
              flex: 1,
              padding: '12px 16px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'dicom' ? '2px solid #0366d6' : '2px solid transparent',
              color: activeTab === 'dicom' ? '#0366d6' : '#586069',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            🔬 DICOM 영상
          </button>
        </div>

        <div className="card-body">
          {activeTab === 'clinical' && (
            <div>
              {clinicalRecords.length > 0 ? (
                <table className="table">
                  <thead>
                    <tr>
                      <th>검사일</th>
                      <th>TNM 병기</th>
                      <th>Child-Pugh</th>
                      <th>AFP</th>
                      <th>Albumin</th>
                      <th>Bilirubin</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clinicalRecords.map((record) => (
                      <tr key={record.clinical_id}>
                        <td>{record.test_date}</td>
                        <td>{record.tumor_stage || '-'}</td>
                        <td>{record.child_pugh || '-'}</td>
                        <td>{record.afp || '-'}</td>
                        <td>{record.albumin || '-'}</td>
                        <td>{record.bilirubin || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="empty-state">
                  <p className="empty-state-text">임상 데이터가 없습니다.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'genomic' && (
            <div>
              {genomicRecords.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  {genomicRecords.map((record) => (
                    <div key={record.sample_id} style={{ border: '1px solid #e1e4e8', borderRadius: '4px', padding: '12px' }}>
                      <p style={{ fontSize: '13px', fontWeight: 500, marginBottom: '8px' }}>샘플 ID: {record.sample_id}</p>
                      <p style={{ fontSize: '12px', color: '#586069', marginBottom: '8px' }}>채취일: {record.sample_date}</p>
                      <div style={{ background: '#f6f8fa', padding: '12px', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace', overflow: 'auto', maxHeight: '150px' }}>
                        {JSON.stringify(record.gene_data, null, 2)}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p className="empty-state-text">유전체 데이터가 없습니다.</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'dicom' && (
            <div className="empty-state">
              <div className="empty-state-icon">🔬</div>
              <p className="empty-state-text">DICOM 영상 분석</p>
              <button
                onClick={() => navigate(`/dicom/${id}`)}
                className="btn btn-primary"
                style={{ marginTop: '12px' }}
              >
                DICOM 뷰어 열기
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PatientDetail;