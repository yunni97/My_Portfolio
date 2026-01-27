import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import axios from 'axios';
import { API_BASE_URL, BENTOML_URL, ORTHANC_URL } from '../services/apiConfig';

// ============================================================
// 타입 정의
// ============================================================
interface Patient {
  patient_id: number;
  name: string;
  birth_date: string;
  sex: string;
  phone?: string;
}

interface DicomStudy {
  study_uid: string;
  study_date: string;
  study_desc?: string;
  modality?: string;
  institution?: string;
  accession_number?: string;
  patient_id?: number;
}

interface DicomSeries {
  series_uid: string;
  series_number?: number;
  series_desc?: string;
  phase_label?: string;
  modality?: string;
  num_instances?: number;
}

interface ImageInfo {
  slice_thickness?: string;
  pixel_spacing?: string;
  rows?: number;
  columns?: number;
  window_center?: number;
  window_width?: number;
  total_instances?: number;
}

interface SegmentationResult {
  tumor_detected: boolean;
  tumor_volume?: number;
  tumor_location?: string;
  confidence?: number;
}

// ============================================================
// API 설정
// ============================================================
const API_CONFIG = {
  DJANGO_API: API_BASE_URL,
  ORTHANC_URL: ORTHANC_URL,
  BENTOML_URL: BENTOML_URL,
};

// ============================================================
// API 호출 함수들
// ============================================================
const fetchPatientFromDB = async (patientId: string): Promise<Patient | null> => {
  try {
    const response = await fetch(`${API_CONFIG.DJANGO_API}/patients/${patientId}/`);
    const data = await response.json();
    return data.success ? data.data.patient : null;
  } catch (error) {
    console.error('환자 정보 로드 실패:', error);
    return null;
  }
};

const fetchStudiesFromOrthanc = async (patientId: string): Promise<DicomStudy[]> => {
  try {
    const response = await fetch(`${API_CONFIG.DJANGO_API}/dicom-studies/?patient_id=${patientId}`);
    const data = await response.json();
    return data.success ? data.data : [];
  } catch (error) {
    console.error('Study 로드 실패:', error);
    return [];
  }
};

const fetchSeriesFromOrthanc = async (studyUid: string): Promise<DicomSeries[]> => {
  try {
    const response = await fetch(`${API_CONFIG.DJANGO_API}/dicom-series/?study_uid=${studyUid}`);
    const data = await response.json();
    return data.success ? data.data : [];
  } catch (error) {
    console.error('Series 로드 실패:', error);
    return [];
  }
};

const requestAIAnalysis = async (patientId: number, seriesUid: string): Promise<SegmentationResult | null> => {
  try {
    const response = await fetch(`${API_CONFIG.BENTOML_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patient_id: patientId, series_uid: seriesUid }),
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
  } catch (error) {
    console.error('AI 분석 실패:', error);
    return null;
  }
};

// ============================================================
// 메인 컴포넌트
// ============================================================
const DicomAnalysis: React.FC = () => {
  const { patientId } = useParams<{ patientId?: string }>();
  const navigate = useNavigate();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [studies, setStudies] = useState<DicomStudy[]>([]);
  const [selectedStudy, setSelectedStudy] = useState<DicomStudy | null>(null);
  const [seriesList, setSeriesList] = useState<DicomSeries[]>([]);
  const [leftSeries, setLeftSeries] = useState<DicomSeries | null>(null);
  const [rightSeries, setRightSeries] = useState<DicomSeries | null>(null);
  const [leftSlice, setLeftSlice] = useState(1);
  const [rightSlice, setRightSlice] = useState(1);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showSeriesSelector, setShowSeriesSelector] = useState<'left' | 'right' | null>(null);
  const [segmentationResult, setSegmentationResult] = useState<SegmentationResult | null>(null);

  const [leftImageInfo, setLeftImageInfo] = useState<ImageInfo>({
    slice_thickness: '-', pixel_spacing: '-', rows: 512, columns: 512,
    window_center: 40, window_width: 400, total_instances: 0
  });
  const [rightImageInfo, setRightImageInfo] = useState<ImageInfo>({
    slice_thickness: '-', pixel_spacing: '-', rows: 512, columns: 512,
    window_center: 40, window_width: 400, total_instances: 0
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { loadData(); }, [patientId]);

  const loadData = async () => {
    setLoading(true);

    // 환자 ID가 없으면 로딩만 끝내고 환자 선택 화면 표시
    if (!patientId) {
      setLoading(false);
      return;
    }

    let p = await fetchPatientFromDB(patientId);
    if (!p) p = { patient_id: parseInt(patientId), name: '(DB 연동 필요)', birth_date: '-', sex: 'male' };
    setPatient(p);

    let st = await fetchStudiesFromOrthanc(patientId);
    setStudies(st);

    let currentSelectedStudy = st.length > 0 ? st[0] : null;
    setSelectedStudy(currentSelectedStudy);

    if (currentSelectedStudy) {
      let sr = await fetchSeriesFromOrthanc(currentSelectedStudy.study_uid);
      setSeriesList(sr);
      if (sr.length > 0) {
        setLeftSeries(sr[0]);
        setLeftImageInfo(info => ({ ...info, total_instances: sr[0].num_instances || 100 }));
      }
    }
    setLoading(false);
  };

  const handleStudySelect = async (study: DicomStudy) => {
    setSelectedStudy(study);
    setLeftSeries(null);
    setRightSeries(null);
    setSegmentationResult(null);

    const sr = await fetchSeriesFromOrthanc(study.study_uid);
    setSeriesList(sr);

    if (sr.length > 0) {
      setLeftSeries(sr[0]);
      setLeftImageInfo(info => ({ ...info, total_instances: sr[0].num_instances || 100 }));
    } else {
      setLeftImageInfo(info => ({ ...info, total_instances: 0 }));
    }
  };

  const handleSeriesSelect = (series: DicomSeries, target: 'left' | 'right') => {
    if (target === 'left') {
      setLeftSeries(series); setLeftSlice(1);
      setLeftImageInfo(p => ({ ...p, total_instances: series.num_instances || 100 }));
    } else {
      setRightSeries(series); setRightSlice(1);
      setRightImageInfo(p => ({ ...p, total_instances: series.num_instances || 100 }));
    }
    setShowSeriesSelector(null);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) handleUpload(file);
  };

  // [기존] 단일 파일 업로드
  const handleUpload = async (fileToUpload: File) => {
    if (!fileToUpload) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', fileToUpload);
    if (patientId) formData.append('patient_id', patientId);

    try {
      const response = await axios.post(`${API_CONFIG.DJANGO_API}/dicom-upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (response.data.status === 'success') {
        alert('DICOM 파일이 성공적으로 Orthanc에 전송되었습니다.');
        if (patientId) loadData();
      } else {
        alert(`업로드 실패: ${response.data.message}`);
      }
    } catch (error: any) {
      console.error('Upload Error:', error);
      alert(`서버 연결 오류: ${error.message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  // [NEW] 폴더 업로드 핸들러
  const handleFolderUpload = async (files: FileList) => {
    if (!files || files.length === 0) return;
    setUploading(true);
    const formData = new FormData();

    Array.from(files).forEach((file) => {
      if (file.name.toLowerCase().endsWith('.dcm') || !file.name.includes('.')) {
        formData.append('files', file);
      }
    });

    if (patientId) formData.append('patient_id', patientId);

    try {
      const uploadUrl = `${API_CONFIG.DJANGO_API}/dicom-upload-folder/`;
      const response = await axios.post(uploadUrl, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 600000,
      });

      if (response.data.status === 'success') {
        alert(`✅ 업로드 및 분석 완료!\n결과: ${JSON.stringify(response.data.data)}`);
        if (patientId) loadData();
      } else {
        alert(`❌ 실패: ${response.data.message}`);
      }
    } catch (error: any) {
      console.error('Folder Upload Error:', error);
      alert(`서버 통신 오류: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  // [NEW] 폴더 선택 이벤트 핸들러
  const onFolderSelected = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files) {
      handleFolderUpload(event.target.files);
    }
  };

  const handleAnalyze = async () => {
    if (!leftSeries || !patient) {
      alert('분석할 시리즈를 선택하세요.');
      return;
    }
    setAnalyzing(true);
    setSegmentationResult(null);
    const result = await requestAIAnalysis(patient.patient_id, leftSeries.series_uid);
    if (result) {
      setSegmentationResult(result);
      setRightSeries({
        series_uid: 'AI_' + Date.now(),
        series_number: 99,
        series_desc: result.tumor_detected ? 'AI Segmentation (Tumor Detected)' : 'AI Segmentation (No Tumor)',
        phase_label: 'SEG',
        modality: 'SEG',
        num_instances: leftImageInfo.total_instances
      });
      setRightImageInfo(p => ({ ...p, total_instances: leftImageInfo.total_instances || 100 }));
      alert('AI 분석 완료!');
    } else {
      alert('AI 분석 중 오류가 발생했습니다.');
    }
    setAnalyzing(false);
  };

  const calcAge = (bd: string) => {
    if (!bd || bd === '-') return '-';
    const b = new Date(bd), t = new Date();
    let a = t.getFullYear() - b.getFullYear();
    if (t.getMonth() < b.getMonth() || (t.getMonth() === b.getMonth() && t.getDate() < b.getDate())) a--;
    return a;
  };

  if (loading) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 78px)', background: '#1a1a2e', color: '#e0e0e0', borderRadius: '6px' }}>
      <div style={{ textAlign: 'center' }}><div style={{ fontSize: '48px' }}>⏳</div><div>로딩 중...</div></div>
    </div>
  );

  // 환자 ID가 없는 경우 환자 선택 화면
  if (!patientId || !patient) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 78px)', background: '#1a1a2e', color: '#e0e0e0', borderRadius: '6px' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '64px', marginBottom: '24px' }}>🔬</div>
          <h2 style={{ fontSize: '24px', fontWeight: 600, marginBottom: '16px', color: '#4a9eff' }}>DICOM 영상 분석</h2>
          <p style={{ fontSize: '14px', color: '#a0a0a0', marginBottom: '24px' }}>
            환자를 선택하고 DICOM 영상을 분석하세요
          </p>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/patients')}
            style={{ padding: '12px 24px' }}
          >
            환자 목록으로 이동
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 78px)', background: '#1a1a2e', color: '#e0e0e0', borderRadius: '6px', overflow: 'hidden' }}>

      {/* 상단 환자 정보 */}
      <div style={{ background: '#16213e', padding: '8px 16px', borderBottom: '1px solid #0f3460', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: '#4a9eff', fontSize: '18px' }}>👤</span>
            <span style={{ fontWeight: 600 }}>{patient?.name || '-'}</span>
            <span style={{ padding: '2px 6px', background: patient?.sex === 'male' ? '#1976d2' : '#c2185b', borderRadius: '3px', fontSize: '10px' }}>{patient?.sex === 'male' ? 'M' : 'F'}</span>
          </div>
          <div style={{ fontSize: '12px', color: '#a0a0a0' }}>ID: <span style={{ color: '#4a9eff' }}>{patient?.patient_id || '-'}</span></div>
          <div style={{ fontSize: '12px', color: '#a0a0a0' }}>생년월일: {patient?.birth_date || '-'} <span style={{ color: '#ffa726' }}>({calcAge(patient?.birth_date || '')}세)</span></div>
          <div style={{ fontSize: '12px', color: '#a0a0a0' }}>검사일: <span style={{ color: '#4caf50' }}>{selectedStudy?.study_date || '-'}</span></div>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => navigate(patientId ? `/patients/${patientId}` : '/patients')} style={{ padding: '6px 12px', background: 'transparent', border: '1px solid #4a9eff', color: '#4a9eff', borderRadius: '4px', fontSize: '12px', cursor: 'pointer' }}>← 환자 정보</button>
          <a href={`${API_CONFIG.ORTHANC_URL}/ui/app/#/`} target="_blank" rel="noopener noreferrer" style={{ padding: '6px 12px', background: '#8B5CF6', border: 'none', color: 'white', borderRadius: '4px', fontSize: '12px', textDecoration: 'none' }}>Orthanc</a>
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, minHeight: 0 }}>
        {/* 왼쪽 패널 */}
        <div style={{ width: '200px', background: '#16213e', borderRight: '1px solid #0f3460', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '10px', borderBottom: '1px solid #0f3460', fontSize: '11px' }}>
            <div style={{ color: '#4a9eff', fontWeight: 600, marginBottom: '6px' }}>📋 STUDY</div>
            <div style={{ maxHeight: '100px', overflowY: 'auto', marginBottom: '8px' }}>
              {studies.map(study => (
                <div
                  key={study.study_uid}
                  onClick={() => handleStudySelect(study)}
                  style={{
                    padding: '4px', marginBottom: '2px',
                    background: selectedStudy?.study_uid === study.study_uid ? '#0f3460' : 'transparent',
                    border: `1px solid ${selectedStudy?.study_uid === study.study_uid ? '#4a9eff' : '#1a1a2e'}`,
                    borderRadius: '3px', cursor: 'pointer', fontSize: '10px'
                  }}
                >
                  {study.study_date} ({study.modality})
                </div>
              ))}
            </div>
            <div><span style={{ color: '#808080' }}>Desc:</span> {selectedStudy?.study_desc || '-'}</div>
            <div><span style={{ color: '#808080' }}>Date:</span> {selectedStudy?.study_date || '-'}</div>
            <div><span style={{ color: '#808080' }}>Mod:</span> <span style={{ color: '#4caf50' }}>{selectedStudy?.modality || '-'}</span></div>
          </div>

          <div style={{ padding: '10px', borderBottom: '1px solid #0f3460', fontSize: '11px' }}>
            <div style={{ color: '#4a9eff', fontWeight: 600, marginBottom: '6px' }}>🖼️ LEFT IMAGE</div>
            <div><span style={{ color: '#808080' }}>Series:</span> {leftSeries?.series_desc || '-'}</div>
            <div><span style={{ color: '#808080' }}>Slice:</span> {leftSlice}/{leftImageInfo.total_instances || '-'}</div>
            <div><span style={{ color: '#808080' }}>WL/WW:</span> {leftImageInfo.window_center}/{leftImageInfo.window_width}</div>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div style={{ padding: '10px 10px 6px', fontSize: '11px', color: '#4a9eff', fontWeight: 600 }}>📁 SERIES LIST ({seriesList.length})</div>
            <div style={{ flex: 1, overflow: 'auto', padding: '0 6px 6px' }}>
              {seriesList.map(s => (
                <div key={s.series_uid} onClick={() => handleSeriesSelect(s, 'left')} style={{ padding: '6px', marginBottom: '4px', background: leftSeries?.series_uid === s.series_uid ? '#0f3460' : '#1a1a2e', border: `1px solid ${leftSeries?.series_uid === s.series_uid ? '#4a9eff' : '#2a2a4e'}`, borderRadius: '4px', cursor: 'pointer', fontSize: '10px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>#{s.series_number}</span>
                    <span style={{ padding: '1px 4px', background: s.modality === 'SEG' ? '#e91e63' : '#2196f3', borderRadius: '2px', fontSize: '9px' }}>{s.phase_label}</span>
                  </div>
                  <div style={{ color: '#a0a0a0' }}>{s.series_desc}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Upload and Analyze Section */}
          <div style={{ padding: '10px', borderTop: '1px solid #0f3460' }}>
            <div style={{ marginBottom: '10px' }}>
              {/* 1. 파일 1개 업로드용 Hidden Input */}
              <input
                type="file"
                id="dicom-upload-input"
                onChange={handleFileChange}
                accept=".dcm, application/dicom"
                ref={fileInputRef}
                style={{ display: 'none' }}
              />

              {/* 2. [NEW] 폴더 업로드용 Hidden Input */}
              <input
                type="file"
                id="dicom-folder-input"
                onChange={onFolderSelected}
                style={{ display: 'none' }}
                // TypeScript에서 webkitdirectory 속성을 인식시키기 위한 우회 방법
                {...({ webkitdirectory: "", directory: "" } as any)}
                multiple
              />

              {/* 버튼들 (가로 배치) */}
              <div style={{ display: 'flex', gap: '5px' }}>
                <label
                  htmlFor="dicom-upload-input"
                  style={{
                    flex: 1, padding: '10px',
                    background: uploading ? '#555' : '#1976d2',
                    borderRadius: '4px', color: 'white', fontSize: '11px', fontWeight: 600,
                    cursor: uploading ? 'not-allowed' : 'pointer',
                    textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}
                >
                  {uploading ? <Loader2 size={12} className="animate-spin" /> : '📄 파일 1개'}
                </label>

                <label
                  htmlFor="dicom-folder-input"
                  style={{
                    flex: 1, padding: '10px',
                    background: uploading ? '#555' : '#ff9800',
                    borderRadius: '4px', color: 'white', fontSize: '11px', fontWeight: 600,
                    cursor: uploading ? 'not-allowed' : 'pointer',
                    textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center'
                  }}
                >
                  {uploading ? '업로드 중...' : '📂 폴더 전체'}
                </label>
              </div>
            </div>

            {/* AI 분석 버튼 */}
            <button
              onClick={handleAnalyze}
              disabled={analyzing || !leftSeries}
              style={{
                width: '100%', padding: '10px', marginBottom: '8px',
                background: analyzing || !leftSeries ? '#555' : 'linear-gradient(135deg, #4caf50, #2e7d32)',
                border: 'none', borderRadius: '4px', color: 'white', fontWeight: 600, fontSize: '12px',
                cursor: analyzing || !leftSeries ? 'not-allowed' : 'pointer'
              }}
            >
              {analyzing ? '⏳ AI 분석 중...' : '🧠 AI 분석 실행'}
            </button>

            {/* 생존율 예측 버튼 */}
            <button
              onClick={() => navigate(`/survival/${patientId || ''}`)}
              style={{
                width: '100%', padding: '10px',
                background: 'linear-gradient(135deg, #2196f3, #1565c0)',
                border: 'none', borderRadius: '4px', color: 'white', fontWeight: 600, fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              📊 생존율 예측
            </button>

            {/* 하단 URL 표시 */}
            <div style={{ marginTop: '6px', fontSize: '8px', color: '#606060', textAlign: 'center' }}>
              {API_CONFIG.BENTOML_URL}
            </div>
          </div>
        </div>

        {/* 뷰어 영역 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div style={{ flex: 1, display: 'flex', gap: '2px', padding: '6px', minHeight: 0 }}>
            {/* 왼쪽 뷰어 */}
            <div style={{ flex: 1, background: '#000', borderRadius: '4px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '6px 10px', background: 'linear-gradient(180deg, rgba(0,0,0,0.8) 0%, transparent 100%)', zIndex: 10, display: 'flex', justifyContent: 'space-between' }}>
                <div><div style={{ fontSize: '11px', fontWeight: 600, color: '#4a9eff' }}>원본</div><div style={{ fontSize: '9px', color: '#a0a0a0' }}>{leftSeries?.series_desc || '-'}</div></div>
                <button onClick={() => setShowSeriesSelector('left')} style={{ padding: '3px 6px', background: '#4a9eff', border: 'none', borderRadius: '3px', color: 'white', fontSize: '9px', cursor: 'pointer' }}>변경</button>
              </div>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {leftSeries ? (
                  <div style={{ width: '90%', height: '90%', background: '#111', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                    <div style={{ width: '75%', height: '75%', background: 'radial-gradient(ellipse, #333, #111, #000)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <div style={{ color: '#4a9eff', textAlign: 'center' }}>
                        <div>🔬 CT</div>
                        <div style={{ fontSize: '10px', color: '#808080' }}>Slice {leftSlice}/{leftImageInfo.total_instances}</div>
                        <div style={{ fontSize: '8px', color: '#606060' }}>(Orthanc 연동 필요)</div>
                      </div>
                    </div>
                    <div style={{ position: 'absolute', top: 6, left: 6, fontSize: '9px', color: '#4caf50' }}>{patient?.name}<br />{selectedStudy?.study_date}</div>
                    <div style={{ position: 'absolute', top: 6, right: 6, fontSize: '9px', color: '#ffa726', textAlign: 'right' }}>WL:{leftImageInfo.window_center}<br />WW:{leftImageInfo.window_width}</div>
                  </div>
                ) : <div style={{ color: '#606060' }}>🖼️ 시리즈 선택</div>}
              </div>
              {leftSeries && leftImageInfo.total_instances! > 0 && (
                <div style={{ padding: '6px 10px', background: 'rgba(0,0,0,0.5)' }}>
                  <input type="range" min={1} max={leftImageInfo.total_instances} value={leftSlice} onChange={e => setLeftSlice(+e.target.value)} style={{ width: '100%' }} />
                </div>
              )}
            </div>

            {/* 오른쪽 뷰어 */}
            <div style={{ flex: 1, background: '#000', borderRadius: '4px', display: 'flex', flexDirection: 'column', position: 'relative' }}>
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, padding: '6px 10px', background: 'linear-gradient(180deg, rgba(0,0,0,0.8) 0%, transparent 100%)', zIndex: 10, display: 'flex', justifyContent: 'space-between' }}>
                <div><div style={{ fontSize: '11px', fontWeight: 600, color: '#e91e63' }}>비교/세그먼트</div><div style={{ fontSize: '9px', color: '#a0a0a0' }}>{rightSeries?.series_desc || '-'}</div></div>
                <button onClick={() => setShowSeriesSelector('right')} style={{ padding: '3px 6px', background: '#e91e63', border: 'none', borderRadius: '3px', color: 'white', fontSize: '9px', cursor: 'pointer' }}>선택</button>
              </div>
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {rightSeries ? (
                  <div style={{ width: '90%', height: '90%', background: '#111', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                    <div style={{ width: '75%', height: '75%', background: 'radial-gradient(ellipse, #333, #111, #000)', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
                      {rightSeries.modality === 'SEG' && segmentationResult?.tumor_detected && (
                        <div style={{ position: 'absolute', top: '28%', left: '33%', width: '34%', height: '28%', background: 'rgba(233,30,99,0.4)', border: '2px solid #e91e63', borderRadius: '30%' }} />
                      )}
                      <div style={{ color: '#e91e63', textAlign: 'center' }}>
                        <div>{rightSeries.modality === 'SEG' ? '🎯 SEG' : '🔬 CT'}</div>
                        <div style={{ fontSize: '10px', color: '#808080' }}>Slice {rightSlice}/{rightImageInfo.total_instances}</div>
                      </div>
                    </div>
                    {rightSeries.modality === 'SEG' && segmentationResult && (
                      <div style={{ position: 'absolute', bottom: 6, left: 6, fontSize: '9px', color: '#e91e63' }}>
                        {segmentationResult.tumor_detected ? '🎯 Tumor Detected' : 'No Tumor Detected'}<br />
                        {segmentationResult.tumor_volume && `Vol: ${segmentationResult.tumor_volume}cm³`}<br />
                        {segmentationResult.confidence && `Conf: ${(segmentationResult.confidence * 100).toFixed(0)}%`}
                      </div>
                    )}
                  </div>
                ) : <div style={{ color: '#606060', textAlign: 'center' }}>➕<br />시리즈 선택 또는<br />AI 분석 실행</div>}
              </div>
              {rightSeries && rightImageInfo.total_instances! > 0 && (
                <div style={{ padding: '6px 10px', background: 'rgba(0,0,0,0.5)' }}>
                  <input type="range" min={1} max={rightImageInfo.total_instances} value={rightSlice} onChange={e => setRightSlice(+e.target.value)} style={{ width: '100%' }} />
                </div>
              )}
            </div>
          </div>

          {/* 하단 썸네일 */}
          <div style={{ height: '80px', background: '#16213e', borderTop: '1px solid #0f3460', display: 'flex', alignItems: 'center', padding: '6px', gap: '6px', overflowX: 'auto' }}>
            {seriesList.map(s => (
              <div
                key={s.series_uid}
                onClick={() => handleSeriesSelect(s, rightSeries ? 'left' : 'right')}
                style={{
                  width: '65px', height: '65px', background: '#1a1a2e',
                  border: `2px solid ${leftSeries?.series_uid === s.series_uid ? '#4a9eff' : rightSeries?.series_uid === s.series_uid ? '#e91e63' : '#2a2a4e'}`,
                  borderRadius: '4px', cursor: 'pointer', display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center', position: 'relative', fontSize: '9px'
                }}
              >
                <div style={{ fontSize: '18px' }}>{s.modality === 'SEG' ? '🎯' : '🖼️'}</div>
                <div style={{ color: '#a0a0a0' }}>{s.phase_label}</div>
                {leftSeries?.series_uid === s.series_uid && <div style={{ position: 'absolute', top: 2, left: 2, width: '12px', height: '12px', background: '#4a9eff', borderRadius: '50%', fontSize: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>L</div>}
                {rightSeries?.series_uid === s.series_uid && <div style={{ position: 'absolute', top: 2, right: 2, width: '12px', height: '12px', background: '#e91e63', borderRadius: '50%', fontSize: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>R</div>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {showSeriesSelector && (
        <div onClick={() => setShowSeriesSelector(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
          <div onClick={e => e.stopPropagation()} style={{ background: '#16213e', borderRadius: '8px', padding: '16px', width: '400px', maxHeight: '70%', overflow: 'auto' }}>
            <h3 style={{ marginBottom: '12px', color: showSeriesSelector === 'left' ? '#4a9eff' : '#e91e63' }}>{showSeriesSelector === 'left' ? '왼쪽' : '오른쪽'} 뷰어 시리즈</h3>
            {seriesList.map(s => (
              <div key={s.series_uid} onClick={() => handleSeriesSelect(s, showSeriesSelector)} style={{ padding: '10px', background: '#1a1a2e', border: '1px solid #2a2a4e', borderRadius: '4px', cursor: 'pointer', marginBottom: '6px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div><div style={{ fontWeight: 500 }}>#{s.series_number} - {s.series_desc}</div><div style={{ fontSize: '11px', color: '#808080' }}>{s.num_instances} images</div></div>
                <span style={{ padding: '4px 8px', background: s.modality === 'SEG' ? '#e91e63' : '#2196f3', borderRadius: '4px', fontSize: '10px' }}>{s.phase_label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        input[type="range"] { -webkit-appearance: none; height: 4px; background: #2a2a4e; border-radius: 2px; }
        input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 12px; height: 12px; background: #4a9eff; border-radius: 50%; cursor: pointer; }
      `}</style>
    </div>
  );
};

export default DicomAnalysis;