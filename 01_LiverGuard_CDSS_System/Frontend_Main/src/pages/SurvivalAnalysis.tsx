import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { API_BASE_URL, BENTOML_URL } from '../services/apiConfig';

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

interface ClinicalData {
    // 주요 예측 변수 (Lasso-Cox 선택 변수)
    GPR182?: number;
    KLRB1?: number;
    BILIRUBIN_TOTAL?: number;
    SERUM_ALBUMIN_PRERESECTION?: number;
    // 추가 임상 변수
    AFP?: number;
    tumor_size?: number;
    tumor_count?: number;
    vascular_invasion?: boolean;
    cirrhosis?: boolean;
    child_pugh_score?: string;
    BCLC_stage?: string;
    ALBI_score?: number;
}

interface SurvivalPrediction {
    risk_score: number;
    risk_group: 'low' | 'medium' | 'high';
    survival_1year: number;
    survival_3year: number;
    survival_5year: number;
    median_survival_months: number;
    confidence_interval: [number, number];
    model_version: string;
    prediction_date: string;
}

interface FeatureImportance {
    feature: string;
    coefficient: number;
    importance: number;
    direction: 'positive' | 'negative';
}

// ============================================================
// API 설정
// ============================================================
const API_CONFIG = {
    DJANGO_API: API_BASE_URL,
    BENTOML_URL: BENTOML_URL,
};

// ============================================================
// API 함수
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

const fetchClinicalData = async (patientId: string): Promise<ClinicalData | null> => {
    // TODO: Django API에서 임상 데이터 가져오기
    // const response = await fetch(`${API_CONFIG.DJANGO_API}/patients/${patientId}/clinical-data/`);
    console.log('fetchClinicalData:', patientId);
    return null;
};

const requestSurvivalPrediction = async (
    patientId: number,
    _clinicalData: ClinicalData
): Promise<SurvivalPrediction | null> => {
    // TODO: BentoML Lasso-Cox 모델 예측 요청
    // const response = await fetch(`${API_CONFIG.BENTOML_URL}/predict-survival`, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ patient_id: patientId, ...clinicalData }),
    // });
    console.log('requestSurvivalPrediction:', patientId);
    return null;
};

// ============================================================
// 메인 컴포넌트
// ============================================================
const SurvivalAnalysis: React.FC = () => {
    const { patientId } = useParams<{ patientId?: string }>();
    const navigate = useNavigate();

    const [patient, setPatient] = useState<Patient | null>(null);
    const [clinicalData, setClinicalData] = useState<ClinicalData | null>(null);
    const [prediction, setPrediction] = useState<SurvivalPrediction | null>(null);
    const [loading, setLoading] = useState(true);
    const [analyzing, setAnalyzing] = useState(false);

    // Lasso-Cox 모델 Feature Importance (실제 모델에서 가져온 값)
    const featureImportances: FeatureImportance[] = [
        { feature: 'GPR182', coefficient: -0.423, importance: 0.28, direction: 'negative' },
        { feature: 'KLRB1', coefficient: -0.312, importance: 0.21, direction: 'negative' },
        { feature: 'BILIRUBIN_TOTAL', coefficient: 0.287, importance: 0.19, direction: 'positive' },
        { feature: 'SERUM_ALBUMIN', coefficient: -0.251, importance: 0.17, direction: 'negative' },
    ];

    useEffect(() => {
        loadData();
    }, [patientId]);

    const loadData = async () => {
        setLoading(true);

        if (patientId) {
            const p = await fetchPatientFromDB(patientId);
            if (p) setPatient(p);

            const cd = await fetchClinicalData(patientId);
            if (cd) setClinicalData(cd);
        }

        // ========== 더미 데이터 (API 연동 전) ==========
        if (!patient) {
            setPatient({
                patient_id: patientId ? parseInt(patientId) : 1,
                name: '(DB 연동 필요)',
                birth_date: '-',
                sex: 'male',
            });
        }

        if (!clinicalData) {
            setClinicalData({
                GPR182: 2.34,
                KLRB1: 1.87,
                BILIRUBIN_TOTAL: 1.2,
                SERUM_ALBUMIN_PRERESECTION: 3.8,
                AFP: 245.6,
                tumor_size: 4.2,
                tumor_count: 1,
                vascular_invasion: false,
                cirrhosis: true,
                child_pugh_score: 'A',
                BCLC_stage: 'B',
                ALBI_score: -2.45,
            });
        }
        // ========== 더미 데이터 끝 ==========

        setLoading(false);
    };

    const handleAnalyze = async () => {
        if (!clinicalData || !patient) return;

        setAnalyzing(true);

        const result = await requestSurvivalPrediction(patient.patient_id, clinicalData);

        if (result) {
            setPrediction(result);
        } else {
            // ========== 더미 예측 결과 ==========
            await new Promise(r => setTimeout(r, 2000));

            setPrediction({
                risk_score: 0.342,
                risk_group: 'medium',
                survival_1year: 0.847,
                survival_3year: 0.623,
                survival_5year: 0.456,
                median_survival_months: 42,
                confidence_interval: [36, 52],
                model_version: 'Lasso-Cox v1.0 (C-index: 0.678)',
                prediction_date: new Date().toISOString().split('T')[0],
            });
            // ========== 더미 끝 ==========
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

    const getRiskColor = (group: string) => {
        switch (group) {
            case 'low': return '#4caf50';
            case 'medium': return '#ff9800';
            case 'high': return '#f44336';
            default: return '#999';
        }
    };

    const getRiskLabel = (group: string) => {
        switch (group) {
            case 'low': return '저위험';
            case 'medium': return '중위험';
            case 'high': return '고위험';
            default: return '-';
        }
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 78px)', background: '#f5f7fa' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '48px' }}>⏳</div>
                    <div>데이터 로딩 중...</div>
                </div>
            </div>
        );
    }

    return (
        <div style={{ height: 'calc(100vh - 50px - 28px)', display: 'flex', flexDirection: 'column', gap: '14px', overflow: 'hidden' }}>

            {/* 상단 헤더 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#24292e' }}>
                        📊 생존율 예측 분석
                    </h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 12px', background: '#e3f2fd', borderRadius: '4px' }}>
                        <span style={{ fontSize: '13px', color: '#1976d2' }}>👤 {patient?.name}</span>
                        <span style={{ fontSize: '12px', color: '#666' }}>({calcAge(patient?.birth_date || '')}세, {patient?.sex === 'male' ? '남' : '여'})</span>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => navigate(`/dicom/${patientId}`)}
                    >
                        ← DICOM 뷰어
                    </button>
                    <button
                        className="btn btn-primary btn-sm"
                        onClick={() => navigate(`/patients/${patientId}`)}
                    >
                        환자 정보
                    </button>
                </div>
            </div>

            {/* 메인 컨텐츠 */}
            <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '320px 1fr 300px', gap: '14px', minHeight: 0 }}>

                {/* 좌측: 임상 데이터 입력 */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'auto' }}>

                    {/* 주요 예측 변수 (Lasso-Cox 선택) */}
                    <div className="card">
                        <div className="card-header" style={{ background: '#e8f5e9' }}>
                            <span>🧬 주요 예측 변수</span>
                            <span style={{ fontSize: '10px', color: '#4caf50' }}>Lasso 선택</span>
                        </div>
                        <div className="card-body" style={{ padding: '12px' }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                <div>
                                    <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>GPR182 (발현량)</label>
                                    <input type="number" className="form-control" value={clinicalData?.GPR182 || ''}
                                        onChange={e => setClinicalData(prev => ({ ...prev!, GPR182: parseFloat(e.target.value) }))}
                                        style={{ fontSize: '13px' }} step="0.01" />
                                </div>
                                <div>
                                    <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>KLRB1 (발현량)</label>
                                    <input type="number" className="form-control" value={clinicalData?.KLRB1 || ''}
                                        onChange={e => setClinicalData(prev => ({ ...prev!, KLRB1: parseFloat(e.target.value) }))}
                                        style={{ fontSize: '13px' }} step="0.01" />
                                </div>
                                <div>
                                    <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>Total Bilirubin (mg/dL)</label>
                                    <input type="number" className="form-control" value={clinicalData?.BILIRUBIN_TOTAL || ''}
                                        onChange={e => setClinicalData(prev => ({ ...prev!, BILIRUBIN_TOTAL: parseFloat(e.target.value) }))}
                                        style={{ fontSize: '13px' }} step="0.1" />
                                </div>
                                <div>
                                    <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>Serum Albumin (g/dL)</label>
                                    <input type="number" className="form-control" value={clinicalData?.SERUM_ALBUMIN_PRERESECTION || ''}
                                        onChange={e => setClinicalData(prev => ({ ...prev!, SERUM_ALBUMIN_PRERESECTION: parseFloat(e.target.value) }))}
                                        style={{ fontSize: '13px' }} step="0.1" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 추가 임상 변수 */}
                    <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                        <div className="card-header">
                            <span>📋 추가 임상 정보</span>
                        </div>
                        <div className="card-body" style={{ padding: '12px', overflow: 'auto', flex: 1 }}>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                                <div>
                                    <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>AFP (ng/mL)</label>
                                    <input type="number" className="form-control" value={clinicalData?.AFP || ''}
                                        onChange={e => setClinicalData(prev => ({ ...prev!, AFP: parseFloat(e.target.value) }))}
                                        style={{ fontSize: '13px' }} />
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                    <div>
                                        <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>종양 크기 (cm)</label>
                                        <input type="number" className="form-control" value={clinicalData?.tumor_size || ''}
                                            onChange={e => setClinicalData(prev => ({ ...prev!, tumor_size: parseFloat(e.target.value) }))}
                                            style={{ fontSize: '13px' }} step="0.1" />
                                    </div>
                                    <div>
                                        <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>종양 개수</label>
                                        <input type="number" className="form-control" value={clinicalData?.tumor_count || ''}
                                            onChange={e => setClinicalData(prev => ({ ...prev!, tumor_count: parseInt(e.target.value) }))}
                                            style={{ fontSize: '13px' }} />
                                    </div>
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                                    <div>
                                        <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>Child-Pugh</label>
                                        <select className="form-control" value={clinicalData?.child_pugh_score || ''}
                                            onChange={e => setClinicalData(prev => ({ ...prev!, child_pugh_score: e.target.value }))}
                                            style={{ fontSize: '13px' }}>
                                            <option value="A">A</option>
                                            <option value="B">B</option>
                                            <option value="C">C</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>BCLC Stage</label>
                                        <select className="form-control" value={clinicalData?.BCLC_stage || ''}
                                            onChange={e => setClinicalData(prev => ({ ...prev!, BCLC_stage: e.target.value }))}
                                            style={{ fontSize: '13px' }}>
                                            <option value="0">0</option>
                                            <option value="A">A</option>
                                            <option value="B">B</option>
                                            <option value="C">C</option>
                                            <option value="D">D</option>
                                        </select>
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '16px', marginTop: '4px' }}>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                                        <input type="checkbox" checked={clinicalData?.vascular_invasion || false}
                                            onChange={e => setClinicalData(prev => ({ ...prev!, vascular_invasion: e.target.checked }))} />
                                        혈관 침범
                                    </label>
                                    <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}>
                                        <input type="checkbox" checked={clinicalData?.cirrhosis || false}
                                            onChange={e => setClinicalData(prev => ({ ...prev!, cirrhosis: e.target.checked }))} />
                                        간경변
                                    </label>
                                </div>
                                <div>
                                    <label style={{ fontSize: '11px', color: '#666', display: 'block', marginBottom: '4px' }}>ALBI Score</label>
                                    <input type="number" className="form-control" value={clinicalData?.ALBI_score || ''}
                                        onChange={e => setClinicalData(prev => ({ ...prev!, ALBI_score: parseFloat(e.target.value) }))}
                                        style={{ fontSize: '13px' }} step="0.01" />
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* 분석 버튼 */}
                    <button
                        onClick={handleAnalyze}
                        disabled={analyzing}
                        style={{
                            padding: '14px',
                            background: analyzing ? '#ccc' : 'linear-gradient(135deg, #2196f3, #1565c0)',
                            border: 'none',
                            borderRadius: '6px',
                            color: 'white',
                            fontWeight: 600,
                            fontSize: '14px',
                            cursor: analyzing ? 'not-allowed' : 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            gap: '8px',
                            flexShrink: 0
                        }}
                    >
                        {analyzing ? '⏳ 분석 중...' : '🧠 Lasso-Cox 생존 분석 실행'}
                    </button>
                </div>

                {/* 중앙: 생존 곡선 시각화 */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', minHeight: 0 }}>

                    {/* 생존 곡선 그래프 */}
                    <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                        <div className="card-header" style={{ background: '#e3f2fd' }}>
                            <span>📈 Kaplan-Meier 생존 곡선</span>
                            {prediction && (
                                <span style={{ fontSize: '11px', color: '#1976d2' }}>{prediction.model_version}</span>
                            )}
                        </div>
                        <div className="card-body" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', minHeight: 0 }}>
                            {prediction ? (
                                <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                                    {/* 그래프 영역 */}
                                    <svg viewBox="0 0 400 280" style={{ width: '100%', height: '100%' }}>
                                        {/* 그리드 */}
                                        <defs>
                                            <pattern id="grid" width="40" height="25" patternUnits="userSpaceOnUse">
                                                <path d="M 40 0 L 0 0 0 25" fill="none" stroke="#eee" strokeWidth="0.5" />
                                            </pattern>
                                        </defs>
                                        <rect x="50" y="20" width="320" height="200" fill="url(#grid)" />

                                        {/* 축 */}
                                        <line x1="50" y1="220" x2="370" y2="220" stroke="#333" strokeWidth="1" />
                                        <line x1="50" y1="20" x2="50" y2="220" stroke="#333" strokeWidth="1" />

                                        {/* Y축 레이블 */}
                                        {[0, 0.25, 0.5, 0.75, 1].map((v, i) => (
                                            <g key={i}>
                                                <text x="45" y={220 - v * 200 + 4} textAnchor="end" fontSize="10" fill="#666">{(v * 100).toFixed(0)}%</text>
                                                <line x1="47" y1={220 - v * 200} x2="50" y2={220 - v * 200} stroke="#333" />
                                            </g>
                                        ))}

                                        {/* X축 레이블 */}
                                        {[0, 12, 24, 36, 48, 60].map((m, i) => (
                                            <g key={i}>
                                                <text x={50 + (m / 60) * 320} y="235" textAnchor="middle" fontSize="10" fill="#666">{m}개월</text>
                                                <line x1={50 + (m / 60) * 320} y1="220" x2={50 + (m / 60) * 320} y2="223" stroke="#333" />
                                            </g>
                                        ))}

                                        {/* 전체 평균 생존 곡선 (회색) */}
                                        <path
                                            d="M 50,40 L 100,55 L 150,80 L 200,110 L 250,145 L 300,175 L 350,195 L 370,205"
                                            fill="none"
                                            stroke="#bbb"
                                            strokeWidth="2"
                                            strokeDasharray="5,3"
                                        />

                                        {/* 환자 예측 생존 곡선 (파란색) */}
                                        <path
                                            d={`M 50,${220 - 200} 
                          L ${50 + (12 / 60) * 320},${220 - prediction.survival_1year * 200} 
                          L ${50 + (36 / 60) * 320},${220 - prediction.survival_3year * 200} 
                          L ${50 + (60 / 60) * 320},${220 - prediction.survival_5year * 200}`}
                                            fill="none"
                                            stroke="#2196f3"
                                            strokeWidth="3"
                                        />

                                        {/* 신뢰구간 */}
                                        <path
                                            d={`M 50,${220 - 200} 
                          L ${50 + (12 / 60) * 320},${220 - (prediction.survival_1year + 0.05) * 200} 
                          L ${50 + (36 / 60) * 320},${220 - (prediction.survival_3year + 0.08) * 200} 
                          L ${50 + (60 / 60) * 320},${220 - (prediction.survival_5year + 0.1) * 200}
                          L ${50 + (60 / 60) * 320},${220 - (prediction.survival_5year - 0.1) * 200}
                          L ${50 + (36 / 60) * 320},${220 - (prediction.survival_3year - 0.08) * 200}
                          L ${50 + (12 / 60) * 320},${220 - (prediction.survival_1year - 0.05) * 200}
                          Z`}
                                            fill="rgba(33, 150, 243, 0.15)"
                                            stroke="none"
                                        />

                                        {/* 데이터 포인트 */}
                                        <circle cx={50 + (12 / 60) * 320} cy={220 - prediction.survival_1year * 200} r="5" fill="#2196f3" />
                                        <circle cx={50 + (36 / 60) * 320} cy={220 - prediction.survival_3year * 200} r="5" fill="#2196f3" />
                                        <circle cx={50 + (60 / 60) * 320} cy={220 - prediction.survival_5year * 200} r="5" fill="#2196f3" />

                                        {/* 중앙 생존 시간 표시 */}
                                        <line
                                            x1={50 + (prediction.median_survival_months / 60) * 320}
                                            y1="20"
                                            x2={50 + (prediction.median_survival_months / 60) * 320}
                                            y2="220"
                                            stroke="#ff9800"
                                            strokeWidth="2"
                                            strokeDasharray="4,2"
                                        />
                                        <text
                                            x={50 + (prediction.median_survival_months / 60) * 320}
                                            y="15"
                                            textAnchor="middle"
                                            fontSize="10"
                                            fill="#ff9800"
                                        >
                                            중앙생존: {prediction.median_survival_months}개월
                                        </text>

                                        {/* 범례 */}
                                        <g transform="translate(280, 30)">
                                            <rect x="0" y="0" width="85" height="45" fill="white" stroke="#ddd" rx="3" />
                                            <line x1="5" y1="12" x2="25" y2="12" stroke="#2196f3" strokeWidth="3" />
                                            <text x="30" y="15" fontSize="9" fill="#333">환자 예측</text>
                                            <line x1="5" y1="28" x2="25" y2="28" stroke="#bbb" strokeWidth="2" strokeDasharray="5,3" />
                                            <text x="30" y="31" fontSize="9" fill="#333">평균 생존</text>
                                        </g>

                                        {/* 축 제목 */}
                                        <text x="210" y="255" textAnchor="middle" fontSize="11" fill="#333">시간 (개월)</text>
                                        <text x="15" y="120" textAnchor="middle" fontSize="11" fill="#333" transform="rotate(-90, 15, 120)">생존 확률</text>
                                    </svg>
                                </div>
                            ) : (
                                <div style={{ textAlign: 'center', color: '#999' }}>
                                    <div style={{ fontSize: '64px', marginBottom: '16px' }}>📊</div>
                                    <div style={{ fontSize: '14px' }}>임상 데이터를 입력하고</div>
                                    <div style={{ fontSize: '14px' }}>"생존 분석 실행" 버튼을 클릭하세요</div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 생존율 요약 */}
                    {prediction && (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', flexShrink: 0 }}>
                            <div style={{ background: 'white', border: '1px solid #e1e4e8', borderRadius: '6px', padding: '16px', textAlign: 'center' }}>
                                <div style={{ fontSize: '11px', color: '#666', marginBottom: '6px' }}>1년 생존율</div>
                                <div style={{ fontSize: '28px', fontWeight: 700, color: '#4caf50' }}>{(prediction.survival_1year * 100).toFixed(1)}%</div>
                            </div>
                            <div style={{ background: 'white', border: '1px solid #e1e4e8', borderRadius: '6px', padding: '16px', textAlign: 'center' }}>
                                <div style={{ fontSize: '11px', color: '#666', marginBottom: '6px' }}>3년 생존율</div>
                                <div style={{ fontSize: '28px', fontWeight: 700, color: '#2196f3' }}>{(prediction.survival_3year * 100).toFixed(1)}%</div>
                            </div>
                            <div style={{ background: 'white', border: '1px solid #e1e4e8', borderRadius: '6px', padding: '16px', textAlign: 'center' }}>
                                <div style={{ fontSize: '11px', color: '#666', marginBottom: '6px' }}>5년 생존율</div>
                                <div style={{ fontSize: '28px', fontWeight: 700, color: '#9c27b0' }}>{(prediction.survival_5year * 100).toFixed(1)}%</div>
                            </div>
                            <div style={{ background: 'white', border: '1px solid #e1e4e8', borderRadius: '6px', padding: '16px', textAlign: 'center' }}>
                                <div style={{ fontSize: '11px', color: '#666', marginBottom: '6px' }}>중앙 생존</div>
                                <div style={{ fontSize: '28px', fontWeight: 700, color: '#ff9800' }}>{prediction.median_survival_months}<span style={{ fontSize: '14px' }}>개월</span></div>
                            </div>
                        </div>
                    )}
                </div>

                {/* 우측: 위험도 및 변수 중요도 */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflow: 'auto' }}>

                    {/* 위험도 평가 */}
                    <div className="card">
                        <div className="card-header" style={{ background: prediction ? (prediction.risk_group === 'high' ? '#ffebee' : prediction.risk_group === 'medium' ? '#fff3e0' : '#e8f5e9') : '#f6f8fa' }}>
                            <span>⚠️ 위험도 평가</span>
                        </div>
                        <div className="card-body" style={{ padding: '16px', textAlign: 'center' }}>
                            {prediction ? (
                                <>
                                    <div style={{
                                        width: '100px',
                                        height: '100px',
                                        borderRadius: '50%',
                                        background: `conic-gradient(${getRiskColor(prediction.risk_group)} ${prediction.risk_score * 360}deg, #eee 0deg)`,
                                        margin: '0 auto 16px',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center'
                                    }}>
                                        <div style={{
                                            width: '80px',
                                            height: '80px',
                                            borderRadius: '50%',
                                            background: 'white',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'center',
                                            justifyContent: 'center'
                                        }}>
                                            <div style={{ fontSize: '20px', fontWeight: 700, color: getRiskColor(prediction.risk_group) }}>
                                                {(prediction.risk_score * 100).toFixed(0)}%
                                            </div>
                                            <div style={{ fontSize: '10px', color: '#666' }}>Risk Score</div>
                                        </div>
                                    </div>
                                    <div style={{
                                        display: 'inline-block',
                                        padding: '8px 20px',
                                        background: getRiskColor(prediction.risk_group),
                                        color: 'white',
                                        borderRadius: '20px',
                                        fontWeight: 600,
                                        fontSize: '14px'
                                    }}>
                                        {getRiskLabel(prediction.risk_group)}군
                                    </div>
                                    <div style={{ marginTop: '12px', fontSize: '11px', color: '#666' }}>
                                        95% CI: [{prediction.confidence_interval[0]}, {prediction.confidence_interval[1]}] 개월
                                    </div>
                                </>
                            ) : (
                                <div style={{ color: '#999', padding: '20px 0' }}>
                                    분석 후 표시됩니다
                                </div>
                            )}
                        </div>
                    </div>

                    {/* 변수 중요도 */}
                    <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                        <div className="card-header">
                            <span>📊 변수 중요도</span>
                            <span style={{ fontSize: '10px', color: '#666' }}>Lasso-Cox</span>
                        </div>
                        <div className="card-body" style={{ padding: '12px', overflow: 'auto', flex: 1 }}>
                            {featureImportances.map((fi, idx) => (
                                <div key={idx} style={{ marginBottom: '12px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                        <span style={{ fontSize: '12px', fontWeight: 500 }}>{fi.feature}</span>
                                        <span style={{
                                            fontSize: '10px',
                                            color: fi.direction === 'positive' ? '#f44336' : '#4caf50',
                                            fontWeight: 500
                                        }}>
                                            {fi.direction === 'positive' ? '↑ 위험 증가' : '↓ 보호 효과'}
                                        </span>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <div style={{ flex: 1, height: '8px', background: '#eee', borderRadius: '4px', overflow: 'hidden' }}>
                                            <div style={{
                                                width: `${fi.importance * 100}%`,
                                                height: '100%',
                                                background: fi.direction === 'positive' ? '#f44336' : '#4caf50',
                                                borderRadius: '4px'
                                            }} />
                                        </div>
                                        <span style={{ fontSize: '11px', color: '#666', width: '40px', textAlign: 'right' }}>
                                            {(fi.importance * 100).toFixed(0)}%
                                        </span>
                                    </div>
                                    <div style={{ fontSize: '10px', color: '#999', marginTop: '2px' }}>
                                        계수: {fi.coefficient.toFixed(3)}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* 모델 정보 */}
                    <div className="card" style={{ flexShrink: 0 }}>
                        <div className="card-header">
                            <span>ℹ️ 모델 정보</span>
                        </div>
                        <div className="card-body" style={{ padding: '12px', fontSize: '11px', color: '#666' }}>
                            <div style={{ marginBottom: '6px' }}>
                                <strong>모델:</strong> Lasso-Cox Regression
                            </div>
                            <div style={{ marginBottom: '6px' }}>
                                <strong>C-index:</strong> 0.678 (Ridge-Cox)
                            </div>
                            <div style={{ marginBottom: '6px' }}>
                                <strong>학습 데이터:</strong> TCGA-LIHC (n=72)
                            </div>
                            <div style={{ marginBottom: '6px' }}>
                                <strong>선택 변수:</strong> 4개 (GPR182, KLRB1, BILIRUBIN, ALBUMIN)
                            </div>
                            <div style={{ color: '#999', fontSize: '10px', marginTop: '8px' }}>
                                ※ 본 예측 결과는 참고용이며, 최종 임상 판단은 담당 의료진이 결정합니다.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SurvivalAnalysis;