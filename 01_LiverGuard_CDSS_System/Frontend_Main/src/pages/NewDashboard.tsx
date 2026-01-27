import React, { useState } from 'react';
import './NewDashboard.css';

interface PatientProfile {
    id: number;
    name: string;
    age: number;
    sex: string;
    resident_number: string;
    phone: string;
    blood_type: string;
}

interface VitalSign {
    bloodPressure: string;
    heartRate: string;
    temperature: string;
    weight: string;
    height: string;
    bmi: string;
}

interface DiagnosisCheck {
    medication: boolean;
    imaging: boolean;
    labTest: boolean;
    surgery: boolean;
    hospitalization: boolean;
    rehabilitation: boolean;
    consultation: boolean;
    followUp: boolean;
}

interface ConsultationHistory {
    id: number;
    date: string;
    content: string;
}

interface Appointment {
    id: number;
    date: string;
    time: string;
    type: string;
}

const NewDashboard: React.FC = () => {
    const [patient] = useState<PatientProfile>({
        id: 1,
        name: '홍길동',
        age: 45,
        sex: 'M',
        resident_number: '750101',
        phone: '010-1234-5678',
        blood_type: 'A+'
    });

    const [vitalSigns] = useState<VitalSign>({
        bloodPressure: '120/80',
        heartRate: '72',
        temperature: '36.5',
        weight: '70',
        height: '175',
        bmi: '22.9'
    });

    const [consultationHistories] = useState<ConsultationHistory[]>([
        { id: 1, date: '2024-01-15', content: '정기 검진, 특이사항 없음' },
        { id: 2, date: '2024-02-20', content: '복통 호소, 위내시경 예약' },
        { id: 3, date: '2024-03-10', content: '위내시경 결과 양호' }
    ]);

    const [selectedHistory, setSelectedHistory] = useState<number | null>(null);
    const [selectedPrescriptionHistory, setSelectedPrescriptionHistory] = useState<number | null>(null);
    const [consultationNote, setConsultationNote] = useState('');
    const [prescriptionNote, setPrescriptionNote] = useState('');
    const [drugInteractionQuery, setDrugInteractionQuery] = useState('');
    const [chatMessage, setChatMessage] = useState('');
    const [chatHistory, setChatHistory] = useState<Array<{ role: 'user' | 'ai', message: string }>>([
        { role: 'ai', message: '안녕하세요! 의료 AI 어시스턴트입니다. 무엇을 도와드릴까요?' }
    ]);

    const [prescriptionHistories] = useState<ConsultationHistory[]>([
        { id: 1, date: '2024-01-15', content: '아스피린 100mg, 1일 1회\n혈압약 5mg, 1일 2회' },
        { id: 2, date: '2024-02-20', content: '위장약 20mg, 1일 3회\n진통제 필요시 복용' },
        { id: 3, date: '2024-03-10', content: '항생제 250mg, 1일 2회\n유산균 복용 권장' }
    ]);

    const [diagnosisChecks, setDiagnosisChecks] = useState<DiagnosisCheck>({
        medication: false,
        imaging: false,
        labTest: false,
        surgery: false,
        hospitalization: false,
        rehabilitation: false,
        consultation: false,
        followUp: false
    });

    const [appointments, _setAppointments] = useState<Appointment[]>([
        { id: 1, date: '2024-12-15', time: '14:00', type: '정기 검진' },
        { id: 2, date: '2024-12-20', time: '10:30', type: 'CT 촬영' }
    ]);

    const [currentDate, setCurrentDate] = useState(new Date());

    const handleCheckChange = (key: keyof DiagnosisCheck) => {
        setDiagnosisChecks(prev => ({ ...prev, [key]: !prev[key] }));
    };

    const handleHistorySelect = (history: ConsultationHistory) => {
        setSelectedHistory(history.id);
        setConsultationNote(history.content);
    };

    const handlePrescriptionHistorySelect = (history: ConsultationHistory) => {
        setSelectedPrescriptionHistory(history.id);
        setPrescriptionNote(history.content);
    };

    const handleSaveConsultation = () => {
        console.log('진료 상담 저장:', consultationNote);
        alert('진료 상담 내용이 저장되었습니다.');
    };

    const handleSavePrescription = () => {
        console.log('처방 기록 저장:', prescriptionNote);
        alert('처방 기록이 저장되었습니다.');
    };

    const handleDrugInteractionCheck = () => {
        if (!drugInteractionQuery.trim()) {
            alert('약물명을 입력해주세요.');
            return;
        }
        console.log('약물 상호작용 검색:', drugInteractionQuery);
        // TODO: 실제 API 호출 또는 검색 로직
        alert(`"${drugInteractionQuery}" 약물 상호작용을 검색합니다.`);
    };

    const handleChatSend = () => {
        if (!chatMessage.trim()) return;

        const newUserMessage = { role: 'user' as const, message: chatMessage };
        setChatHistory([...chatHistory, newUserMessage]);
        setChatMessage('');

        // 간단한 AI 응답 시뮬레이션
        setTimeout(() => {
            const aiResponse = {
                role: 'ai' as const,
                message: '답변을 생성 중입니다. 실제 AI API와 연동하시면 더 유용한 답변을 받으실 수 있습니다.'
            };
            setChatHistory(prev => [...prev, aiResponse]);
        }, 500);
    };

    // 간단한 캘린더 생성
    const getDaysInMonth = (date: Date) => {
        const year = date.getFullYear();
        const month = date.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const daysInMonth = lastDay.getDate();
        const startDayOfWeek = firstDay.getDay();

        const days = [];
        for (let i = 0; i < startDayOfWeek; i++) {
            days.push(null);
        }
        for (let i = 1; i <= daysInMonth; i++) {
            days.push(i);
        }
        return days;
    };

    return (
        <div className="new-dashboard">
            {/* 좌측 섹션 */}
            <div className="left-section">
                {/* 환자 프로필 */}
                <div className="patient-profile-card compact">
                    <div className="profile-header compact">
                        <div className="profile-info">
                            <h2 className="profile-name compact">
                                {patient.name}
                                <span className={`profile-sex ${patient.sex.toLowerCase()}`}>
                                    {patient.sex === 'M' ? '남' : '여'}
                                </span>
                            </h2>
                            <p className="profile-detail compact">#{patient.id} · {patient.age}세</p>
                        </div>
                    </div>
                    <div className="profile-details compact">
                        <div className="detail-row">
                            <span className="detail-label">주민등록</span>
                            <span className="detail-value">{patient.resident_number}</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">전화번호</span>
                            <span className="detail-value">{patient.phone}</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">혈액형</span>
                            <span className="detail-value">{patient.blood_type}</span>
                        </div>
                    </div>
                </div>

                {/* 진료 상담 기록 */}
                <div className="consultation-card">
                    <div className="card-header">
                        <h3>진료 상담 기록</h3>
                        <button className="save-btn" onClick={handleSaveConsultation}>저장</button>
                    </div>
                    <div className="consultation-body">
                        <div className="consultation-history">
                            <div className="history-title">이전 기록</div>
                            {consultationHistories.map(history => (
                                <div
                                    key={history.id}
                                    className={`history-item ${selectedHistory === history.id ? 'selected' : ''}`}
                                    onClick={() => handleHistorySelect(history)}
                                >
                                    <span className="history-date">{history.date}</span>
                                </div>
                            ))}
                        </div>
                        <div className="consultation-editor">
                            <textarea
                                className="consultation-textarea"
                                placeholder="환자와의 상담 내용을 기록하세요..."
                                value={consultationNote}
                                onChange={(e) => setConsultationNote(e.target.value)}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* 중앙 섹션 */}
            <div className="center-section">
                {/* 신체/바이탈 정보 */}
                <div className="vital-signs-card">
                    <div className="card-header compact">
                        <h3>신체 · 바이탈</h3>
                    </div>
                    <div className="card-body compact">
                        <div className="vital-grid">
                            <div className="vital-item">
                                <div className="vital-info">
                                    <span className="vital-label">혈압</span>
                                    <span className="vital-value">{vitalSigns.bloodPressure}</span>
                                </div>
                            </div>
                            <div className="vital-item">
                                <div className="vital-info">
                                    <span className="vital-label">심박수</span>
                                    <span className="vital-value">{vitalSigns.heartRate} bpm</span>
                                </div>
                            </div>
                            <div className="vital-item">
                                <div className="vital-info">
                                    <span className="vital-label">체온</span>
                                    <span className="vital-value">{vitalSigns.temperature}°C</span>
                                </div>
                            </div>
                            <div className="vital-item">
                                <div className="vital-info">
                                    <span className="vital-label">체중</span>
                                    <span className="vital-value">{vitalSigns.weight} kg</span>
                                </div>
                            </div>
                            <div className="vital-item">
                                <div className="vital-info">
                                    <span className="vital-label">신장</span>
                                    <span className="vital-value">{vitalSigns.height} cm</span>
                                </div>
                            </div>
                            <div className="vital-item">
                                <div className="vital-info">
                                    <span className="vital-label">BMI</span>
                                    <span className="vital-value">{vitalSigns.bmi}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* 진단 정보 */}
                <div className="diagnosis-card">
                    <div className="card-header">
                        <h3>진단 정보</h3>
                        <span className="checked-count">
                            {Object.values(diagnosisChecks).filter(Boolean).length} / {Object.keys(diagnosisChecks).length}
                        </span>
                    </div>
                    <div className="card-body">
                        <div className="diagnosis-checks">
                            {Object.entries({
                                medication: '약물 처방',
                                imaging: '영상 촬영',
                                labTest: '검사 의뢰',
                                surgery: '수술 예정',
                                hospitalization: '입원 필요',
                                rehabilitation: '재활 치료',
                                consultation: '타과 협진',
                                followUp: '추적 관찰'
                            }).map(([key, label]) => (
                                <label key={key} className="check-item">
                                    <input
                                        type="checkbox"
                                        checked={diagnosisChecks[key as keyof DiagnosisCheck]}
                                        onChange={() => handleCheckChange(key as keyof DiagnosisCheck)}
                                    />
                                    <span className="check-label">
                                        {label}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 처방 기록 */}
                <div className="prescription-card">
                    <div className="card-header">
                        <h3>처방 기록</h3>
                        <button className="save-btn" onClick={handleSavePrescription}>저장</button>
                    </div>
                    <div className="card-body">
                        {/* 약물 상호작용 검색 */}
                        <div className="drug-interaction-search">
                            <div className="search-warning-icon">⚠️</div>
                            <div className="search-content">
                                <div className="search-title">약물 상호작용 간편 분석</div>
                                <div className="search-input-wrapper">
                                    <input
                                        type="text"
                                        className="drug-search-input"
                                        placeholder="약물명 입력 (Enter로 추가)"
                                        value={drugInteractionQuery}
                                        onChange={(e) => setDrugInteractionQuery(e.target.value)}
                                        onKeyPress={(e) => {
                                            if (e.key === 'Enter') {
                                                handleDrugInteractionCheck();
                                            }
                                        }}
                                    />
                                    <button className="search-analyze-btn" onClick={handleDrugInteractionCheck}>
                                        패턴 분석
                                    </button>
                                </div>
                                <div className="search-info">약물을 2개 이상 추가하세요</div>
                            </div>
                        </div>

                        <div className="prescription-body">
                            <div className="prescription-history">
                                <div className="history-title">이전 기록</div>
                                {prescriptionHistories.map(history => (
                                    <div
                                        key={history.id}
                                        className={`history-item ${selectedPrescriptionHistory === history.id ? 'selected' : ''}`}
                                        onClick={() => handlePrescriptionHistorySelect(history)}
                                    >
                                        <span className="history-date">{history.date}</span>
                                    </div>
                                ))}
                            </div>
                            <div className="prescription-editor">
                                <textarea
                                    className="prescription-textarea"
                                    placeholder="처방 내용을 작성하세요...&#10;&#10;- 처방 약물명 및 용량&#10;- 복용 방법&#10;- 주의사항"
                                    value={prescriptionNote}
                                    onChange={(e) => setPrescriptionNote(e.target.value)}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* 우측 섹션 (캘린더 & 일정) */}
            <div className="right-section">
                {/* 상단: 캘린더 + 진료일정 */}
                <div className="right-section-top">
                    {/* 캘린더 */}
                    <div className="calendar-card">
                        <div className="card-header">
                            <button className="calendar-nav-btn" onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1))}>◀</button>
                            <h3>{currentDate.getFullYear()}년 {currentDate.getMonth() + 1}월</h3>
                            <button className="calendar-nav-btn" onClick={() => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1))}>▶</button>
                        </div>
                        <div className="calendar-body">
                            <div className="calendar-weekdays">
                                {['일', '월', '화', '수', '목', '금', '토'].map(day => (
                                    <div key={day} className="calendar-weekday">{day}</div>
                                ))}
                            </div>
                            <div className="calendar-days">
                                {getDaysInMonth(currentDate).map((day, idx) => (
                                    <div
                                        key={idx}
                                        className={`calendar-day ${day === null ? 'empty' : ''} ${day === new Date().getDate() && currentDate.getMonth() === new Date().getMonth() ? 'today' : ''}`}
                                    >
                                        {day}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* 진료 일정 */}
                    <div className="appointments-card">
                        <div className="card-header">
                            <h3>진료 일정</h3>
                            <button className="add-btn">+</button>
                        </div>
                        <div className="appointments-body">
                            {appointments.map(appointment => (
                                <div key={appointment.id} className="appointment-item">
                                    <div className="appointment-date">
                                        <span className="appointment-day">{new Date(appointment.date).getDate()}</span>
                                        <span className="appointment-month">{new Date(appointment.date).getMonth() + 1}월</span>
                                    </div>
                                    <div className="appointment-info">
                                        <div className="appointment-type">{appointment.type}</div>
                                        <div className="appointment-time">🕐 {appointment.time}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* 하단: AI 어시스턴트 */}
                <div className="right-section-bottom">
                    <div className="chatbot-card">
                        <div className="card-header">
                            <h3>🤖 AI 어시스턴트</h3>
                        </div>
                        <div className="chatbot-body">
                            <div className="chat-messages">
                                {chatHistory.map((chat, idx) => (
                                    <div key={idx} className={`chat-bubble ${chat.role}`}>
                                        <div className="chat-content">{chat.message}</div>
                                    </div>
                                ))}
                            </div>
                            <div className="chat-input-wrapper">
                                <input
                                    type="text"
                                    className="chat-input"
                                    placeholder="메시지를 입력하세요..."
                                    value={chatMessage}
                                    onChange={(e) => setChatMessage(e.target.value)}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter') {
                                            handleChatSend();
                                        }
                                    }}
                                />
                                <button className="chat-send-btn" onClick={handleChatSend}>전송</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NewDashboard;
