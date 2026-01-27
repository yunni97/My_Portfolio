import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../services/apiConfig';

// ============================================================
// 타입 정의
// ============================================================
interface PatientBasicInfo {
    name: string;
    birth_date: string;
    sex: string;
    phone: string;
    address: string;
    resident_number: string;
    emergency_contact: string;
    blood_type: string;
}

interface ClinicalData {
    diagnosis_date: string;
    chief_complaint: string;
    // 간기능 검사
    AFP: string;
    bilirubin_total: string;
    bilirubin_direct: string;
    albumin: string;
    ALT: string;
    AST: string;
    ALP: string;
    GGT: string;
    PT_INR: string;
    platelet: string;
    creatinine: string;
    // 간암 관련
    tumor_size: string;
    tumor_count: string;
    vascular_invasion: boolean;
    cirrhosis: boolean;
    hepatitis_b: boolean;
    hepatitis_c: boolean;
    child_pugh_score: string;
    child_pugh_class: string;
    MELD_score: string;
    BCLC_stage: string;
    ALBI_score: string;
    ALBI_grade: string;
}

interface GenomicData {
    sample_date: string;
    sample_type: string;
    // 유전자 발현량 (Lasso-Cox 주요 변수)
    GPR182: string;
    KLRB1: string;
    // 추가 유전자
    TP53_mutation: boolean;
    CTNNB1_mutation: boolean;
    TERT_mutation: boolean;
    AXIN1_mutation: boolean;
    // 기타
    TMB: string;
    MSI_status: string;
    notes: string;
}

interface ImagingStudy {
    study_date: string;
    modality: string;
    body_part: string;
    contrast: boolean;
    institution: string;
    accession_number: string;
    file_path: string;
    findings: string;
    impression: string;
}

// ============================================================
// API 설정
// ============================================================
const API_CONFIG = {
    DJANGO_API: API_BASE_URL,
};

// ============================================================
// 메인 컴포넌트
// ============================================================
const PatientForm: React.FC = () => {
    const { id } = useParams<{ id?: string }>();
    const navigate = useNavigate();
    const isEditMode = !!id;

    // 탭 상태
    const [activeTab, setActiveTab] = useState<'basic' | 'clinical' | 'genomic' | 'imaging'>('basic');
    const [loading, setLoading] = useState(false);
    const [saving, setSaving] = useState(false);
    const [patientId, setPatientId] = useState<number | null>(id ? parseInt(id) : null);

    // 폼 데이터
    const [basicInfo, setBasicInfo] = useState<PatientBasicInfo>({
        name: '',
        birth_date: '',
        sex: 'male',
        phone: '',
        address: '',
        resident_number: '',
        emergency_contact: '',
        blood_type: '',
    });

    const [clinicalData, setClinicalData] = useState<ClinicalData>({
        diagnosis_date: '',
        chief_complaint: '',
        AFP: '',
        bilirubin_total: '',
        bilirubin_direct: '',
        albumin: '',
        ALT: '',
        AST: '',
        ALP: '',
        GGT: '',
        PT_INR: '',
        platelet: '',
        creatinine: '',
        tumor_size: '',
        tumor_count: '',
        vascular_invasion: false,
        cirrhosis: false,
        hepatitis_b: false,
        hepatitis_c: false,
        child_pugh_score: '',
        child_pugh_class: 'A',
        MELD_score: '',
        BCLC_stage: '0',
        ALBI_score: '',
        ALBI_grade: '1',
    });

    const [genomicData, setGenomicData] = useState<GenomicData>({
        sample_date: '',
        sample_type: 'tissue',
        GPR182: '',
        KLRB1: '',
        TP53_mutation: false,
        CTNNB1_mutation: false,
        TERT_mutation: false,
        AXIN1_mutation: false,
        TMB: '',
        MSI_status: 'MSS',
        notes: '',
    });

    const [imagingStudies, setImagingStudies] = useState<ImagingStudy[]>([]);
    const [newImaging, setNewImaging] = useState<ImagingStudy>({
        study_date: '',
        modality: 'CT',
        body_part: 'Abdomen',
        contrast: true,
        institution: '',
        accession_number: '',
        file_path: '',
        findings: '',
        impression: '',
    });

    // 유효성 검사 에러
    const [errors, setErrors] = useState<Record<string, string>>({});

    // ============================================================
    // 데이터 로드 (수정 모드)
    // ============================================================
    useEffect(() => {
        if (isEditMode && id) {
            loadPatientData(id);
        }
    }, [id, isEditMode]);

    const loadPatientData = async (patientId: string) => {
        setLoading(true);
        try {
            const response = await fetch(`${API_CONFIG.DJANGO_API}/patients/${patientId}/`);
            const data = await response.json();

            if (data.success) {
                const patient = data.data.patient;
                setBasicInfo({
                    name: patient.name || '',
                    birth_date: patient.birth_date || '',
                    sex: patient.sex || 'male',
                    phone: patient.phone || '',
                    address: patient.address || '',
                    resident_number: patient.resident_number || '',
                    emergency_contact: patient.emergency_contact || '',
                    blood_type: patient.blood_type || '',
                });

                // TODO: 임상데이터, 유전체 데이터도 로드
                // if (data.data.clinical) setClinicalData(data.data.clinical);
                // if (data.data.genomic) setGenomicData(data.data.genomic);
            }
        } catch (error) {
            console.error('환자 데이터 로드 실패:', error);
        }
        setLoading(false);
    };

    // ============================================================
    // 저장
    // ============================================================
    const validateBasicInfo = (): boolean => {
        const newErrors: Record<string, string> = {};

        if (!basicInfo.name.trim()) newErrors.name = '이름을 입력하세요';
        if (!basicInfo.birth_date) newErrors.birth_date = '생년월일을 입력하세요';
        if (!basicInfo.sex) newErrors.sex = '성별을 선택하세요';

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const saveBasicInfo = async (): Promise<number | null> => {
        if (!validateBasicInfo()) return null;

        setSaving(true);
        try {
            const url = isEditMode
                ? `${API_CONFIG.DJANGO_API}/patients/${id}/update/`
                : `${API_CONFIG.DJANGO_API}/patients/create/`;

            const response = await fetch(url, {
                method: isEditMode ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(basicInfo),
            });

            const data = await response.json();

            if (data.success) {
                const newPatientId = data.data?.patient_id || data.data?.patient?.patient_id || parseInt(id || '0');
                setPatientId(newPatientId);
                alert(isEditMode ? '환자 정보가 수정되었습니다.' : '환자가 등록되었습니다.');
                return newPatientId;
            } else {
                alert('저장 실패: ' + (data.error || '알 수 없는 오류'));
                return null;
            }
        } catch (error) {
            console.error('저장 실패:', error);
            alert('저장 중 오류가 발생했습니다.');
            return null;
        } finally {
            setSaving(false);
        }
    };

    const saveClinicalData = async (): Promise<boolean> => {
        if (!patientId) {
            alert('먼저 기본정보를 저장하세요.');
            return false;
        }

        setSaving(true);
        try {
            const response = await fetch(`${API_CONFIG.DJANGO_API}/patients/${patientId}/clinical/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(clinicalData),
            });

            const data = await response.json();
            if (data.success) {
                alert('임상 데이터가 저장되었습니다.');
                return true;
            }
            return false;
        } catch (error) {
            console.error('임상 데이터 저장 실패:', error);
            return false;
        } finally {
            setSaving(false);
        }
    };

    const saveGenomicData = async (): Promise<boolean> => {
        if (!patientId) {
            alert('먼저 기본정보를 저장하세요.');
            return false;
        }

        setSaving(true);
        try {
            const response = await fetch(`${API_CONFIG.DJANGO_API}/patients/${patientId}/genomic/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(genomicData),
            });

            const data = await response.json();
            if (data.success) {
                alert('유전체 데이터가 저장되었습니다.');
                return true;
            }
            return false;
        } catch (error) {
            console.error('유전체 데이터 저장 실패:', error);
            return false;
        } finally {
            setSaving(false);
        }
    };

    const addImagingStudy = async (): Promise<boolean> => {
        if (!patientId) {
            alert('먼저 기본정보를 저장하세요.');
            return false;
        }

        if (!newImaging.study_date || !newImaging.modality) {
            alert('검사일과 검사종류를 입력하세요.');
            return false;
        }

        setSaving(true);
        try {
            const response = await fetch(`${API_CONFIG.DJANGO_API}/patients/${patientId}/imaging/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newImaging),
            });

            const data = await response.json();
            if (data.success) {
                setImagingStudies([...imagingStudies, { ...newImaging }]);
                setNewImaging({
                    study_date: '',
                    modality: 'CT',
                    body_part: 'Abdomen',
                    contrast: true,
                    institution: '',
                    accession_number: '',
                    file_path: '',
                    findings: '',
                    impression: '',
                });
                alert('영상 검사가 등록되었습니다.');
                return true;
            }
            return false;
        } catch (error) {
            console.error('영상 검사 등록 실패:', error);
            return false;
        } finally {
            setSaving(false);
        }
    };

    const handleComplete = () => {
        if (patientId) {
            navigate(`/patients/${patientId}`);
        } else {
            navigate('/patients');
        }
    };

    // ============================================================
    // 렌더링
    // ============================================================
    if (loading) {
        return (
            <div className="empty-state">
                <div style={{ fontSize: '48px' }}>⏳</div>
                <div>데이터 로딩 중...</div>
            </div>
        );
    }

    return (
        <div style={{ height: 'calc(100vh - 50px - 28px)', display: 'flex', flexDirection: 'column' }}>

            {/* 헤더 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexShrink: 0 }}>
                <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#24292e' }}>
                    {isEditMode ? '✏️ 환자 정보 수정' : '➕ 환자 등록'}
                    {patientId && <span style={{ marginLeft: '12px', fontSize: '14px', color: '#666' }}>ID: {patientId}</span>}
                </h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                    <button className="btn btn-secondary" onClick={() => navigate(-1)}>
                        취소
                    </button>
                    <button className="btn btn-primary" onClick={handleComplete}>
                        완료
                    </button>
                </div>
            </div>

            {/* 탭 헤더 */}
            <div style={{ display: 'flex', gap: '4px', marginBottom: '12px', flexShrink: 0 }}>
                {[
                    { key: 'basic', label: '1. 기본정보', icon: '👤', required: true },
                    { key: 'clinical', label: '2. 임상데이터', icon: '🩺', required: false },
                    { key: 'genomic', label: '3. 유전체', icon: '🧬', required: false },
                    { key: 'imaging', label: '4. 영상검사', icon: '🖼️', required: false },
                ].map((tab) => (
                    <button
                        key={tab.key}
                        onClick={() => setActiveTab(tab.key as any)}
                        style={{
                            padding: '10px 20px',
                            background: activeTab === tab.key ? '#2b5876' : '#f6f8fa',
                            color: activeTab === tab.key ? 'white' : '#24292e',
                            border: `1px solid ${activeTab === tab.key ? '#2b5876' : '#e1e4e8'}`,
                            borderRadius: '4px 4px 0 0',
                            cursor: 'pointer',
                            fontSize: '13px',
                            fontWeight: activeTab === tab.key ? 600 : 400,
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                        }}
                    >
                        <span>{tab.icon}</span>
                        {tab.label}
                        {tab.required && <span style={{ color: activeTab === tab.key ? '#ffeb3b' : '#e53935' }}>*</span>}
                    </button>
                ))}
            </div>

            {/* 탭 컨텐츠 */}
            <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                <div className="card-body" style={{ flex: 1, overflow: 'auto', padding: '20px' }}>

                    {/* ========== 1. 기본정보 탭 ========== */}
                    {activeTab === 'basic' && (
                        <div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>
                                        이름 <span style={{ color: '#e53935' }}>*</span>
                                    </label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        value={basicInfo.name}
                                        onChange={(e) => setBasicInfo({ ...basicInfo, name: e.target.value })}
                                        placeholder="홍길동"
                                    />
                                    {errors.name && <span style={{ color: '#e53935', fontSize: '11px' }}>{errors.name}</span>}
                                </div>

                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>
                                        생년월일 <span style={{ color: '#e53935' }}>*</span>
                                    </label>
                                    <input
                                        type="date"
                                        className="form-control"
                                        value={basicInfo.birth_date}
                                        onChange={(e) => setBasicInfo({ ...basicInfo, birth_date: e.target.value })}
                                    />
                                    {errors.birth_date && <span style={{ color: '#e53935', fontSize: '11px' }}>{errors.birth_date}</span>}
                                </div>

                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>
                                        성별 <span style={{ color: '#e53935' }}>*</span>
                                    </label>
                                    <div style={{ display: 'flex', gap: '16px' }}>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                            <input
                                                type="radio"
                                                name="sex"
                                                value="male"
                                                checked={basicInfo.sex === 'male'}
                                                onChange={(e) => setBasicInfo({ ...basicInfo, sex: e.target.value })}
                                            />
                                            <span style={{ color: '#1976d2' }}>👨 남성</span>
                                        </label>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                                            <input
                                                type="radio"
                                                name="sex"
                                                value="female"
                                                checked={basicInfo.sex === 'female'}
                                                onChange={(e) => setBasicInfo({ ...basicInfo, sex: e.target.value })}
                                            />
                                            <span style={{ color: '#c2185b' }}>👩 여성</span>
                                        </label>
                                    </div>
                                </div>

                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>혈액형</label>
                                    <select
                                        className="form-control"
                                        value={basicInfo.blood_type}
                                        onChange={(e) => setBasicInfo({ ...basicInfo, blood_type: e.target.value })}
                                    >
                                        <option value="">선택</option>
                                        <option value="A+">A+</option>
                                        <option value="A-">A-</option>
                                        <option value="B+">B+</option>
                                        <option value="B-">B-</option>
                                        <option value="O+">O+</option>
                                        <option value="O-">O-</option>
                                        <option value="AB+">AB+</option>
                                        <option value="AB-">AB-</option>
                                    </select>
                                </div>

                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>연락처</label>
                                    <input
                                        type="tel"
                                        className="form-control"
                                        value={basicInfo.phone}
                                        onChange={(e) => setBasicInfo({ ...basicInfo, phone: e.target.value })}
                                        placeholder="010-1234-5678"
                                    />
                                </div>

                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>비상연락처</label>
                                    <input
                                        type="tel"
                                        className="form-control"
                                        value={basicInfo.emergency_contact}
                                        onChange={(e) => setBasicInfo({ ...basicInfo, emergency_contact: e.target.value })}
                                        placeholder="010-9876-5432"
                                    />
                                </div>

                                <div style={{ gridColumn: '1 / -1' }}>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>주소</label>
                                    <input
                                        type="text"
                                        className="form-control"
                                        value={basicInfo.address}
                                        onChange={(e) => setBasicInfo({ ...basicInfo, address: e.target.value })}
                                        placeholder="서울특별시 강남구..."
                                    />
                                </div>
                            </div>

                            <div style={{ marginTop: '24px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                <button
                                    className="btn btn-primary"
                                    onClick={async () => {
                                        const savedId = await saveBasicInfo();
                                        if (savedId) setActiveTab('clinical');
                                    }}
                                    disabled={saving}
                                >
                                    {saving ? '저장 중...' : '저장 후 다음 →'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ========== 2. 임상데이터 탭 ========== */}
                    {activeTab === 'clinical' && (
                        <div>
                            {!patientId && (
                                <div style={{ padding: '16px', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '16px' }}>
                                    ⚠️ 먼저 기본정보를 저장해주세요.
                                </div>
                            )}

                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#2b5876' }}>📅 진단 정보</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>진단일</label>
                                    <input type="date" className="form-control" value={clinicalData.diagnosis_date}
                                        onChange={(e) => setClinicalData({ ...clinicalData, diagnosis_date: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>주호소</label>
                                    <input type="text" className="form-control" value={clinicalData.chief_complaint}
                                        onChange={(e) => setClinicalData({ ...clinicalData, chief_complaint: e.target.value })}
                                        placeholder="복부 통증, 황달 등" />
                                </div>
                            </div>

                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#2b5876' }}>🧪 간기능 검사 (LFT)</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>AFP (ng/mL)</label>
                                    <input type="number" className="form-control" value={clinicalData.AFP}
                                        onChange={(e) => setClinicalData({ ...clinicalData, AFP: e.target.value })} step="0.1" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>Total Bilirubin (mg/dL)</label>
                                    <input type="number" className="form-control" value={clinicalData.bilirubin_total}
                                        onChange={(e) => setClinicalData({ ...clinicalData, bilirubin_total: e.target.value })} step="0.1" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>Albumin (g/dL)</label>
                                    <input type="number" className="form-control" value={clinicalData.albumin}
                                        onChange={(e) => setClinicalData({ ...clinicalData, albumin: e.target.value })} step="0.1" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>PT/INR</label>
                                    <input type="number" className="form-control" value={clinicalData.PT_INR}
                                        onChange={(e) => setClinicalData({ ...clinicalData, PT_INR: e.target.value })} step="0.01" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>ALT (U/L)</label>
                                    <input type="number" className="form-control" value={clinicalData.ALT}
                                        onChange={(e) => setClinicalData({ ...clinicalData, ALT: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>AST (U/L)</label>
                                    <input type="number" className="form-control" value={clinicalData.AST}
                                        onChange={(e) => setClinicalData({ ...clinicalData, AST: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>Platelet (×10³/μL)</label>
                                    <input type="number" className="form-control" value={clinicalData.platelet}
                                        onChange={(e) => setClinicalData({ ...clinicalData, platelet: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>Creatinine (mg/dL)</label>
                                    <input type="number" className="form-control" value={clinicalData.creatinine}
                                        onChange={(e) => setClinicalData({ ...clinicalData, creatinine: e.target.value })} step="0.01" />
                                </div>
                            </div>

                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#2b5876' }}>🎯 종양 정보</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '24px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>종양 크기 (cm)</label>
                                    <input type="number" className="form-control" value={clinicalData.tumor_size}
                                        onChange={(e) => setClinicalData({ ...clinicalData, tumor_size: e.target.value })} step="0.1" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>종양 개수</label>
                                    <input type="number" className="form-control" value={clinicalData.tumor_count}
                                        onChange={(e) => setClinicalData({ ...clinicalData, tumor_count: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>Child-Pugh Class</label>
                                    <select className="form-control" value={clinicalData.child_pugh_class}
                                        onChange={(e) => setClinicalData({ ...clinicalData, child_pugh_class: e.target.value })}>
                                        <option value="A">A (5-6점)</option>
                                        <option value="B">B (7-9점)</option>
                                        <option value="C">C (10-15점)</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px' }}>BCLC Stage</label>
                                    <select className="form-control" value={clinicalData.BCLC_stage}
                                        onChange={(e) => setClinicalData({ ...clinicalData, BCLC_stage: e.target.value })}>
                                        <option value="0">0 (Very Early)</option>
                                        <option value="A">A (Early)</option>
                                        <option value="B">B (Intermediate)</option>
                                        <option value="C">C (Advanced)</option>
                                        <option value="D">D (Terminal)</option>
                                    </select>
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '24px' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={clinicalData.vascular_invasion}
                                        onChange={(e) => setClinicalData({ ...clinicalData, vascular_invasion: e.target.checked })} />
                                    혈관 침범
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={clinicalData.cirrhosis}
                                        onChange={(e) => setClinicalData({ ...clinicalData, cirrhosis: e.target.checked })} />
                                    간경변
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={clinicalData.hepatitis_b}
                                        onChange={(e) => setClinicalData({ ...clinicalData, hepatitis_b: e.target.checked })} />
                                    B형 간염
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={clinicalData.hepatitis_c}
                                        onChange={(e) => setClinicalData({ ...clinicalData, hepatitis_c: e.target.checked })} />
                                    C형 간염
                                </label>
                            </div>

                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" onClick={() => setActiveTab('basic')}>← 이전</button>
                                <button className="btn btn-primary" onClick={async () => {
                                    const success = await saveClinicalData();
                                    if (success) setActiveTab('genomic');
                                }} disabled={saving || !patientId}>
                                    {saving ? '저장 중...' : '저장 후 다음 →'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ========== 3. 유전체 데이터 탭 ========== */}
                    {activeTab === 'genomic' && (
                        <div>
                            {!patientId && (
                                <div style={{ padding: '16px', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '16px' }}>
                                    ⚠️ 먼저 기본정보를 저장해주세요.
                                </div>
                            )}

                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#2b5876' }}>📅 샘플 정보</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>채취일</label>
                                    <input type="date" className="form-control" value={genomicData.sample_date}
                                        onChange={(e) => setGenomicData({ ...genomicData, sample_date: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>샘플 종류</label>
                                    <select className="form-control" value={genomicData.sample_type}
                                        onChange={(e) => setGenomicData({ ...genomicData, sample_type: e.target.value })}>
                                        <option value="tissue">조직 (Tissue)</option>
                                        <option value="blood">혈액 (Blood)</option>
                                        <option value="cfDNA">cfDNA</option>
                                    </select>
                                </div>
                            </div>

                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#4caf50' }}>🧬 주요 유전자 발현량 (Lasso-Cox 변수)</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px', padding: '16px', background: '#e8f5e9', borderRadius: '6px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>GPR182 발현량</label>
                                    <input type="number" className="form-control" value={genomicData.GPR182}
                                        onChange={(e) => setGenomicData({ ...genomicData, GPR182: e.target.value })} step="0.01"
                                        placeholder="예: 2.34" />
                                    <span style={{ fontSize: '11px', color: '#666' }}>↓ 낮을수록 보호 효과</span>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>KLRB1 발현량</label>
                                    <input type="number" className="form-control" value={genomicData.KLRB1}
                                        onChange={(e) => setGenomicData({ ...genomicData, KLRB1: e.target.value })} step="0.01"
                                        placeholder="예: 1.87" />
                                    <span style={{ fontSize: '11px', color: '#666' }}>↓ 낮을수록 보호 효과</span>
                                </div>
                            </div>

                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#2b5876' }}>🔬 돌연변이 상태</h4>
                            <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '24px' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={genomicData.TP53_mutation}
                                        onChange={(e) => setGenomicData({ ...genomicData, TP53_mutation: e.target.checked })} />
                                    TP53 돌연변이
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={genomicData.CTNNB1_mutation}
                                        onChange={(e) => setGenomicData({ ...genomicData, CTNNB1_mutation: e.target.checked })} />
                                    CTNNB1 돌연변이
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={genomicData.TERT_mutation}
                                        onChange={(e) => setGenomicData({ ...genomicData, TERT_mutation: e.target.checked })} />
                                    TERT 프로모터 돌연변이
                                </label>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                    <input type="checkbox" checked={genomicData.AXIN1_mutation}
                                        onChange={(e) => setGenomicData({ ...genomicData, AXIN1_mutation: e.target.checked })} />
                                    AXIN1 돌연변이
                                </label>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>TMB (mut/Mb)</label>
                                    <input type="number" className="form-control" value={genomicData.TMB}
                                        onChange={(e) => setGenomicData({ ...genomicData, TMB: e.target.value })} step="0.1" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>MSI 상태</label>
                                    <select className="form-control" value={genomicData.MSI_status}
                                        onChange={(e) => setGenomicData({ ...genomicData, MSI_status: e.target.value })}>
                                        <option value="MSS">MSS (Stable)</option>
                                        <option value="MSI-L">MSI-L (Low)</option>
                                        <option value="MSI-H">MSI-H (High)</option>
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>비고</label>
                                <textarea className="form-control" value={genomicData.notes}
                                    onChange={(e) => setGenomicData({ ...genomicData, notes: e.target.value })}
                                    rows={3} placeholder="추가 유전체 분석 결과나 특이사항..." />
                            </div>

                            <div style={{ marginTop: '24px', display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" onClick={() => setActiveTab('clinical')}>← 이전</button>
                                <button className="btn btn-primary" onClick={async () => {
                                    const success = await saveGenomicData();
                                    if (success) setActiveTab('imaging');
                                }} disabled={saving || !patientId}>
                                    {saving ? '저장 중...' : '저장 후 다음 →'}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* ========== 4. 영상검사 탭 ========== */}
                    {activeTab === 'imaging' && (
                        <div>
                            {!patientId && (
                                <div style={{ padding: '16px', background: '#fff3cd', border: '1px solid #ffc107', borderRadius: '4px', marginBottom: '16px' }}>
                                    ⚠️ 먼저 기본정보를 저장해주세요.
                                </div>
                            )}

                            {/* 등록된 영상 목록 */}
                            {imagingStudies.length > 0 && (
                                <div style={{ marginBottom: '24px' }}>
                                    <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#2b5876' }}>📋 등록된 영상검사</h4>
                                    <table className="table">
                                        <thead>
                                            <tr>
                                                <th>검사일</th>
                                                <th>종류</th>
                                                <th>부위</th>
                                                <th>조영제</th>
                                                <th>기관</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {imagingStudies.map((study, idx) => (
                                                <tr key={idx}>
                                                    <td>{study.study_date}</td>
                                                    <td>{study.modality}</td>
                                                    <td>{study.body_part}</td>
                                                    <td>{study.contrast ? 'Yes' : 'No'}</td>
                                                    <td>{study.institution || '-'}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            )}

                            {/* 새 영상 등록 폼 */}
                            <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px', color: '#2b5876' }}>➕ 새 영상검사 등록</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '16px' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>
                                        검사일 <span style={{ color: '#e53935' }}>*</span>
                                    </label>
                                    <input type="date" className="form-control" value={newImaging.study_date}
                                        onChange={(e) => setNewImaging({ ...newImaging, study_date: e.target.value })} />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>
                                        검사종류 <span style={{ color: '#e53935' }}>*</span>
                                    </label>
                                    <select className="form-control" value={newImaging.modality}
                                        onChange={(e) => setNewImaging({ ...newImaging, modality: e.target.value })}>
                                        <option value="CT">CT</option>
                                        <option value="MRI">MRI</option>
                                        <option value="PET-CT">PET-CT</option>
                                        <option value="Ultrasound">초음파 (US)</option>
                                        <option value="X-ray">X-ray</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>검사 부위</label>
                                    <select className="form-control" value={newImaging.body_part}
                                        onChange={(e) => setNewImaging({ ...newImaging, body_part: e.target.value })}>
                                        <option value="Abdomen">복부 (Abdomen)</option>
                                        <option value="Chest">흉부 (Chest)</option>
                                        <option value="Liver">간 (Liver)</option>
                                        <option value="Whole Body">전신 (Whole Body)</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>검사 기관</label>
                                    <input type="text" className="form-control" value={newImaging.institution}
                                        onChange={(e) => setNewImaging({ ...newImaging, institution: e.target.value })}
                                        placeholder="서울대학교병원" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>Accession Number</label>
                                    <input type="text" className="form-control" value={newImaging.accession_number}
                                        onChange={(e) => setNewImaging({ ...newImaging, accession_number: e.target.value })}
                                        placeholder="ACC-2025-001234" />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>조영제</label>
                                    <div style={{ display: 'flex', gap: '16px', paddingTop: '8px' }}>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <input type="radio" name="contrast" checked={newImaging.contrast}
                                                onChange={() => setNewImaging({ ...newImaging, contrast: true })} />
                                            사용
                                        </label>
                                        <label style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <input type="radio" name="contrast" checked={!newImaging.contrast}
                                                onChange={() => setNewImaging({ ...newImaging, contrast: false })} />
                                            미사용
                                        </label>
                                    </div>
                                </div>
                            </div>

                            <div style={{ marginBottom: '16px' }}>
                                <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>판독 소견 (Findings)</label>
                                <textarea className="form-control" value={newImaging.findings}
                                    onChange={(e) => setNewImaging({ ...newImaging, findings: e.target.value })}
                                    rows={3} placeholder="영상 판독 소견을 입력하세요..." />
                            </div>

                            <div style={{ marginBottom: '16px' }}>
                                <label style={{ display: 'block', marginBottom: '6px', fontSize: '13px', fontWeight: 500 }}>결론 (Impression)</label>
                                <textarea className="form-control" value={newImaging.impression}
                                    onChange={(e) => setNewImaging({ ...newImaging, impression: e.target.value })}
                                    rows={2} placeholder="최종 인상/결론..." />
                            </div>

                            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                                <button className="btn btn-secondary" onClick={() => setActiveTab('genomic')}>← 이전</button>
                                <button className="btn btn-outline-primary" onClick={addImagingStudy} disabled={saving || !patientId}>
                                    {saving ? '등록 중...' : '➕ 영상검사 추가'}
                                </button>
                                <button className="btn btn-primary" onClick={handleComplete}>
                                    ✅ 등록 완료
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PatientForm;