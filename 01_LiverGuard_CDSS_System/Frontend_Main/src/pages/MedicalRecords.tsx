// src/pages/MedicalRecords.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../services/apiConfig';

interface MedicalRecord {
    record_id: number;
    visit_date: string;
    patient_name: string;
    doctor_name: string;
    chief_complaint: string;
    assessment: string;
}

const MedicalRecords: React.FC = () => {
    const navigate = useNavigate();
    const [records, setRecords] = useState<MedicalRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchRecords();
    }, []);

    const fetchRecords = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/records/`);
            const data = await response.json();
            if (data.success) {
                setRecords(data.data.records);
            }
            setLoading(false);
        } catch (error) {
            console.error('진료기록 목록 조회 실패:', error);
            setLoading(false);
        }
    };

    const filteredRecords = records.filter(
        (record) =>
            record.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            record.chief_complaint?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                <div>Loading...</div>
            </div>
        );
    }

    return (
        <div style={{ height: 'calc(100vh - 50px - 28px)', display: 'flex', flexDirection: 'column' }}>
            {/* 헤더 영역 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexShrink: 0 }}>
                <h2 style={{ fontSize: '18px', fontWeight: 600, color: '#24292e', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    📋 진료 기록
                    <span className="badge-count">{records.length}건</span>
                </h2>
            </div>

            {/* 검색 */}
            <div className="card" style={{ marginBottom: '12px', flexShrink: 0 }}>
                <div className="card-body" style={{ padding: '10px 16px' }}>
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <input
                            type="text"
                            className="form-control"
                            placeholder="환자명 또는 증상으로 검색..."
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
                    {filteredRecords.length > 0 ? (
                        <div style={{ overflow: 'auto', flex: 1 }}>
                            <table className="table">
                                <thead style={{ position: 'sticky', top: 0, background: '#fafbfc', zIndex: 1 }}>
                                    <tr>
                                        <th style={{ width: '60px' }}>No.</th>
                                        <th style={{ width: '120px' }}>진료일시</th>
                                        <th style={{ width: '100px' }}>환자명</th>
                                        <th style={{ width: '100px' }}>담당의</th>
                                        <th>주증상 (CC)</th>
                                        <th>진단 (Assessment)</th>
                                        <th style={{ width: '80px', textAlign: 'center' }}>상세</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filteredRecords.map((record, index) => (
                                        <tr key={record.record_id} onClick={() => navigate(`/patients/${record.record_id}`)}> {/* Note: Linking to patient detail for now, or maybe record detail if exists */}
                                            <td><span className="patient-id">{index + 1}</span></td>
                                            <td>{new Date(record.visit_date).toLocaleDateString('ko-KR')}</td>
                                            <td style={{ fontWeight: 500 }}>{record.patient_name}</td>
                                            <td>{record.doctor_name}</td>
                                            <td>{record.chief_complaint || '-'}</td>
                                            <td>{record.assessment || '-'}</td>
                                            <td style={{ textAlign: 'center' }}>
                                                <button
                                                    className="btn btn-outline-primary btn-sm"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        // Assuming we want to go to the patient's detail page where records are shown
                                                        // Or a specific record detail page if it existed.
                                                        // For now, let's assume we don't have a standalone record detail page, so maybe just do nothing or link to patient.
                                                        // The user asked for the list view.
                                                    }}
                                                    title="상세보기"
                                                >
                                                    👁️ 상세
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    ) : (
                        <div className="empty-state" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                            <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
                            <p style={{ fontSize: '16px', color: '#666', fontWeight: 500 }}>
                                {searchTerm ? '검색 결과가 없습니다.' : '진료 기록이 없습니다.'}
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MedicalRecords;
