// src/pages/Dashboard.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL, API_BASE } from '../services/apiConfig';

interface DoctorData {
  doctor_id: number;
  name: string;
  email: string;
  department: string | null;
}

interface DashboardProps {
  doctor: DoctorData;
}

interface Patient {
  patient_id: number;
  name: string;
  birth_date: string;
  sex: string;
  phone?: string;
  address?: string;
  resident_number?: string;
  created_at?: string;
  updated_at?: string;
}

interface CalendarEvent {
  date: string;
  type: 'surgery' | 'meeting' | 'checkup';
  title: string;
}

interface AIResult {
  created_at: string;
  thumbnail_url: string;
  slices: Array<{ url: string; filename: string }>;
  total_slices: number;
}

const Dashboard: React.FC<DashboardProps> = ({ doctor: _doctor }) => {
  const navigate = useNavigate();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [updateKey, setUpdateKey] = useState(0); // 강제 리렌더링용
  const [aiResult, setAiResult] = useState<AIResult | null>(null);
  const [loadingAI, setLoadingAI] = useState(false);
  const [selectedAnnouncement, setSelectedAnnouncement] = useState<any>(null);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [selectedDate, setSelectedDate] = useState<string | null>(null); // 선택된 날짜 (YYYY-MM-DD)
  const [appointments, setAppointments] = useState<any[]>([]); // 모든 예약 데이터 저장

  // 공지사항
  const announcements = [
    {
      id: 1,
      title: '시스템 점검 안내',
      badge: 'important',
      content: '12월 25일 오전 2시 ~ 4시 시스템 정기 점검이 있습니다.',
      detail: '간암 생존율 예측 시스템의 안정적인 운영을 위해 서버 점검을 실시합니다. 점검 시간 동안 시스템 이용이 일시 중단될 수 있으니 양해 부탁드립니다.'
    },
    {
      id: 2,
      title: '신규 AI 분석 기능 추가',
      badge: 'new',
      content: '새로운 생존율 분석 기능이 업데이트되었습니다.',
      detail: 'BentoML 기반의 최신 딥러닝 모델이 적용되어 더욱 정확한 간암 생존율 예측이 가능합니다. DICOM 파일 업로드 시 자동으로 분석이 진행됩니다.'
    },
    {
      id: 3,
      title: '환자 데이터 백업 완료',
      badge: '',
      content: '모든 환자 데이터가 안전하게 백업되었습니다.',
      detail: '2024년 12월 7일 기준 모든 환자 진료 기록, DICOM 영상, AI 분석 결과가 백업 서버에 안전하게 저장되었습니다.'
    },
  ];

  // 캘린더 이벤트 (실제 예약 데이터에서 가져옴)
  const [events, setEvents] = useState<CalendarEvent[]>([]);

  useEffect(() => {
    fetchPatients();
    fetchAppointments();
  }, []);

  const fetchAppointments = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/appointments/`);
      const data = await response.json();

      if (data.success) {
        // 모든 예약 데이터 저장
        setAppointments(data.data);

        // 예약 데이터를 캘린더 이벤트로 변환
        const calendarEvents: CalendarEvent[] = data.data.map((apt: any) => {
          // notes 내용에 따라 이벤트 타입 결정
          let eventType: 'surgery' | 'meeting' | 'checkup' = 'checkup';
          const notes = apt.notes?.toLowerCase() || '';

          if (notes.includes('수술') || notes.includes('surgery') || notes.includes('절제')) {
            eventType = 'surgery';
          } else if (notes.includes('회의') || notes.includes('meeting') || notes.includes('상담')) {
            eventType = 'meeting';
          } else if (notes.includes('검사') || notes.includes('check') || notes.includes('ct') || notes.includes('mri')) {
            eventType = 'checkup';
          }

          return {
            date: apt.appointment_date,
            type: eventType,
            title: apt.notes || `${apt.patient.name} 예약`
          };
        });

        setEvents(calendarEvents);

        // 오늘 날짜를 기본으로 선택
        const today = new Date().toISOString().split('T')[0];
        setSelectedDate(today);
      }
    } catch (error) {
      console.error('예약 데이터 로드 실패:', error);
    }
  };

  // 디버깅: selectedPatient 변경 감지
  useEffect(() => {
    console.log('🔵 selectedPatient 변경됨:', selectedPatient);
    console.log('🔵 updateKey:', updateKey);

    // 환자 선택 시 AI 결과 가져오기
    if (selectedPatient) {
      fetchAIResults(selectedPatient.patient_id);
    } else {
      setAiResult(null);
    }
  }, [selectedPatient, updateKey]);

  const fetchAIResults = async (patientId: number) => {
    setLoadingAI(true);
    try {
      const response = await fetch(`${API_BASE_URL}/patients/${patientId}/ai-results/`);
      const data = await response.json();

      if (data.success && data.data.latest_result) {
        setAiResult(data.data.latest_result);
      } else {
        setAiResult(null);
      }
    } catch (error) {
      console.error('AI 결과 로드 실패:', error);
      setAiResult(null);
    } finally {
      setLoadingAI(false);
    }
  };

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

  // 날짜별 예약 환자 필터링
  const getAppointmentPatientIds = (date: string | null) => {
    if (!date) return [];
    return appointments
      .filter(apt => apt.appointment_date === date)
      .map(apt => apt.patient.patient_id);
  };

  const filteredPatients = patients.filter(p => {
    // 검색어 필터
    const matchesSearch = p.name.toLowerCase().includes(searchQuery.toLowerCase());

    // 선택된 날짜가 있으면 해당 날짜의 예약 환자만 표시
    if (selectedDate) {
      const appointmentPatientIds = getAppointmentPatientIds(selectedDate);
      return matchesSearch && appointmentPatientIds.includes(p.patient_id);
    }

    return matchesSearch;
  });

  // 캘린더 함수들
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const prevMonthDays = new Date(year, month, 0).getDate();
    return { firstDay, daysInMonth, prevMonthDays };
  };

  const formatDate = (year: number, month: number, day: number) => {
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  };

  const getEventForDate = (dateStr: string) => {
    return events.find(e => e.date === dateStr);
  };

  const { firstDay, daysInMonth, prevMonthDays } = getDaysInMonth(currentDate);

  const prevMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  const nextMonth = () => setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  const goToToday = () => setCurrentDate(new Date());

  const today = new Date();
  const todayStr = formatDate(today.getFullYear(), today.getMonth(), today.getDate());

  // 캘린더 날짜 배열 생성
  const calendarDays: Array<{
    day: number;
    muted: boolean;
    dateStr: string;
    isToday?: boolean;
    isSunday?: boolean;
    isSaturday?: boolean;
    event?: CalendarEvent;
  }> = [];

  for (let i = firstDay - 1; i >= 0; i--) {
    calendarDays.push({ day: prevMonthDays - i, muted: true, dateStr: '' });
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = formatDate(currentDate.getFullYear(), currentDate.getMonth(), d);
    const dayOfWeek = (firstDay + d - 1) % 7;
    calendarDays.push({
      day: d,
      muted: false,
      dateStr,
      isToday: dateStr === todayStr,
      isSunday: dayOfWeek === 0,
      isSaturday: dayOfWeek === 6,
      event: getEventForDate(dateStr)
    });
  }

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
      {/* ========== 좌측 패널 ========== */}
      <div className="left-panel">
        {/* 시스템 프로필 */}
        <div className="doctor-profile">
          <div className="doctor-avatar">🏥</div>
          <div className="profile-name">LiverGuard CDSS</div>
          <div className="doctor-info">
            <div className="info-item">
              <span>📊</span>
              <span>통합 관리 시스템</span>
            </div>
            <div className="info-item">
              <span>🔒</span>
              <span>보안 인증</span>
            </div>
            <div className="info-item">
              <span>⚡</span>
              <span>실시간 업데이트</span>
            </div>
          </div>
        </div>

        {/* 환자 등록 버튼 */}
        <button
          className="btn btn-primary btn-full"
          onClick={() => navigate('/patients/add')}
        >
          + 환자 등록
        </button>

        {/* 캘린더 */}
        <div className="calendar-card">
          <div className="cal-header">
            <span className="cal-title">
              {currentDate.getFullYear()}-{String(currentDate.getMonth() + 1).padStart(2, '0')}
            </span>
            <div className="cal-nav">
              <button className="cal-btn" onClick={prevMonth}>◀</button>
              <button className="cal-btn" onClick={goToToday}>Today</button>
              <button className="cal-btn" onClick={nextMonth}>▶</button>
            </div>
          </div>

          <div className="cal-grid">
            {['일', '월', '화', '수', '목', '금', '토'].map((dow, i) => (
              <div
                key={dow}
                className="cal-dow"
                style={{ color: i === 0 ? '#e53935' : i === 6 ? '#1e88e5' : undefined }}
              >
                {dow}
              </div>
            ))}

            {calendarDays.map((item, idx) => {
              const isSelected = selectedDate === item.dateStr;

              return (
                <div
                  key={idx}
                  className="cal-cell"
                  onClick={() => {
                    // 날짜 클릭 시 해당 날짜 선택 (muted가 아닌 경우에만)
                    if (!item.muted && item.dateStr) {
                      setSelectedDate(item.dateStr);
                      // 선택한 환자 초기화
                      setSelectedPatient(null);
                    }
                  }}
                  style={{ cursor: item.muted ? 'default' : 'pointer' }}
                >
                  <div
                    className={`cal-day ${item.muted ? 'muted' : ''} ${item.isToday ? 'today' : ''} ${isSelected ? 'selected' : ''}`}
                    style={{
                      color: item.muted ? '#ccc' :
                        item.isToday ? '#0366d6' :
                          item.isSunday ? '#e53935' :
                            item.isSaturday ? '#1e88e5' : undefined,
                      fontWeight: isSelected ? 'bold' : undefined,
                      background: isSelected ? '#e3f2fd' : undefined,
                    }}
                    title={item.event?.title}
                  >
                    {item.day}
                  </div>
                  {item.event && (
                    <span
                      className={`cal-dot ${item.event.type}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (item.event) {
                          setSelectedEvent(item.event);
                        }
                      }}
                      style={{ cursor: 'pointer' }}
                    ></span>
                  )}
                </div>
              );
            })}
          </div>

          <div className="cal-legend">
            <span className="cal-leg">
              <span className="cal-pill" style={{ background: '#e53935' }}></span> 수술
            </span>
            <span className="cal-leg">
              <span className="cal-pill" style={{ background: '#1e88e5' }}></span> 회의
            </span>
            <span className="cal-leg">
              <span className="cal-pill" style={{ background: '#fb8c00' }}></span> 검사
            </span>
          </div>
        </div>

        {/* 공지사항 - flex:1로 남은 공간 채움 */}
        <div className="announcement-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
          <div className="announcement-header">
            <span className="announcement-title">📢 오늘의 공지사항</span>
            <span className="announcement-date">{todayStr}</span>
          </div>
          <ul className="announcement-list" style={{ overflow: 'auto', flex: 1 }}>
            {announcements.map((ann) => (
              <li
                key={ann.id}
                className="announcement-item"
                onClick={() => setSelectedAnnouncement(ann)}
                style={{ cursor: 'pointer' }}
              >
                <div className="announcement-item-title">
                  {ann.title}
                  {ann.badge === 'important' && <span className="announcement-badge badge-important">중요</span>}
                  {ann.badge === 'new' && <span className="announcement-badge badge-new">NEW</span>}
                </div>
                <div className="announcement-item-content">{ann.content}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* 공지사항 모달 */}
      {selectedAnnouncement && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedAnnouncement(null)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              maxWidth: '500px',
              width: '90%',
              maxHeight: '80vh',
              overflow: 'auto',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '20px', fontWeight: 600, margin: 0 }}>
                {selectedAnnouncement.title}
                {selectedAnnouncement.badge === 'important' && (
                  <span className="announcement-badge badge-important" style={{ marginLeft: '8px' }}>중요</span>
                )}
                {selectedAnnouncement.badge === 'new' && (
                  <span className="announcement-badge badge-new" style={{ marginLeft: '8px' }}>NEW</span>
                )}
              </h3>
              <button
                onClick={() => setSelectedAnnouncement(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#6b7280',
                  padding: '0 8px',
                  lineHeight: 1,
                }}
              >
                ×
              </button>
            </div>
            <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '16px' }}>
              {todayStr}
            </div>
            <div style={{ fontSize: '15px', lineHeight: '1.6', color: '#24292e' }}>
              {selectedAnnouncement.detail}
            </div>
            <div style={{ marginTop: '24px', textAlign: 'right' }}>
              <button
                className="btn btn-primary"
                onClick={() => setSelectedAnnouncement(null)}
                style={{ padding: '8px 16px' }}
              >
                확인
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 일정 팝업 모달 */}
      {selectedEvent && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedEvent(null)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '12px',
              padding: '24px',
              maxWidth: '400px',
              width: '90%',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    background: selectedEvent.type === 'surgery' ? '#e53935' :
                                selectedEvent.type === 'meeting' ? '#1e88e5' : '#fb8c00',
                  }}
                ></span>
                {selectedEvent.type === 'surgery' ? '수술' :
                 selectedEvent.type === 'meeting' ? '회의' : '검사'}
              </h3>
              <button
                onClick={() => setSelectedEvent(null)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '24px',
                  cursor: 'pointer',
                  color: '#6b7280',
                  padding: '0 8px',
                  lineHeight: 1,
                }}
              >
                ×
              </button>
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                📅 {selectedEvent.date}
              </div>
              <div style={{ fontSize: '16px', fontWeight: 500, color: '#24292e' }}>
                {selectedEvent.title}
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <button
                className="btn btn-primary"
                onClick={() => setSelectedEvent(null)}
                style={{ padding: '8px 16px' }}
              >
                확인
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========== 중앙 패널: 환자 목록 ========== */}
      <div className="center-panel">
        <div className="patient-list-card">
          <div className="patient-list-header">
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className="patient-list-title">당일 방문 환자</span>
                <span className="badge-count">{filteredPatients.length}명</span>
              </div>
              {selectedDate && (
                <div style={{ fontSize: '12px', color: '#6b7280' }}>
                  📅 {new Date(selectedDate).toLocaleDateString('ko-KR', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </div>
              )}
            </div>
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
                    <th>최근 수정일</th>
                    <th style={{ width: '70px', textAlign: 'center' }}>상세</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPatients.map((patient, idx) => (
                    <tr
                      key={patient.patient_id}
                      onClick={() => {
                        setSelectedPatient({ ...patient });
                        setUpdateKey(prev => prev + 1);
                      }}
                      className={selectedPatient?.patient_id === patient.patient_id ? 'selected' : ''}
                    >
                      <td><span className="patient-id">{idx + 1}</span></td>
                      <td>{patient.name}</td>
                      <td>{patient.created_at ? new Date(patient.created_at).toLocaleDateString('ko-KR') : '-'}</td>
                      <td style={{ textAlign: 'center' }}>
                        <button
                          className="btn btn-outline-primary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/patients/${patient.patient_id}`);
                          }}
                          style={{ padding: '4px 8px', fontSize: '11px' }}
                        >
                          상세
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-state-icon">📋</div>
              <p className="empty-state-text">등록된 환자가 없습니다.</p>
              <p style={{ fontSize: '12px', marginTop: '8px' }}>새 환자를 추가해주세요.</p>
            </div>
          )}
        </div>
      </div>

      {/* ========== 우측 패널 ========== */}
      <div className="right-panel">
        {/* 환자 상세정보 */}
        <div className="detail-card">
          <div className="detail-title">환자 상세정보</div>

          {selectedPatient ? (
            <div className="detail-grid" style={{ gap: '12px' }}>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">환자 ID</div>
                <div className="detail-val">{selectedPatient?.patient_id || '-'}</div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">이름</div>
                <div className="detail-val">{selectedPatient?.name || '-'}</div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">생년월일</div>
                <div className="detail-val">{selectedPatient?.birth_date || '-'}</div>
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
                <div className="detail-val">{selectedPatient?.phone || '-'}</div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">주소</div>
                <div className="detail-val">{selectedPatient?.address || '-'}</div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">등록일</div>
                <div className="detail-val">
                  {selectedPatient?.created_at ? new Date(selectedPatient.created_at).toLocaleDateString('ko-KR') : '-'}
                </div>
              </div>
              <div className="detail-item" style={{ padding: '4px 0' }}>
                <div className="detail-key">수정일</div>
                <div className="detail-val">
                  {selectedPatient?.updated_at ? new Date(selectedPatient.updated_at).toLocaleDateString('ko-KR') : '-'}
                </div>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
              환자를 선택해주세요
            </div>
          )}

          {/* 버튼 영역 */}
          {selectedPatient && (
            <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px solid #e1e4e8', display: 'flex', gap: '8px' }}>
              <button
                className="btn btn-primary btn-sm"
                onClick={() => navigate(`/patients/${selectedPatient.patient_id}`)}
              >
                진료 기록
              </button>
              <button
                className="btn btn-secondary btn-sm"
                onClick={() => navigate(`/patients/${selectedPatient.patient_id}/edit`)}
              >
                정보 수정
              </button>
              <button
                className="btn btn-sm"
                style={{ background: '#8B5CF6', color: 'white' }}
                onClick={() => navigate(`/dicom/${selectedPatient.patient_id}`)}
              >
                영상 분석
              </button>
            </div>
          )}
        </div>

        {/* 영상/이미지 보드 - AI 분석 결과 */}
        <div className="image-board">
          <div className="image-head">
            <span className="tag">AI 분석</span>
            {aiResult && (
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                분석일: {new Date(aiResult.created_at).toLocaleString('ko-KR')}
              </span>
            )}
          </div>

          <div className="image-grid" style={{ flex: 1, padding: '16px' }}>
            {loadingAI ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', marginBottom: '8px' }}>⏳</div>
                  <p style={{ color: '#6b7280' }}>AI 결과 로딩 중...</p>
                </div>
              </div>
            ) : !selectedPatient ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔬</div>
                  <p style={{ color: '#6b7280' }}>환자를 선택하면 AI 분석 결과가 표시됩니다</p>
                </div>
              </div>
            ) : !aiResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                <div style={{ textAlign: 'center', marginBottom: '20px' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px' }}>📋</div>
                  <p style={{ color: '#6b7280', marginBottom: '8px' }}>아직 분석된 DICOM 데이터가 없습니다</p>
                  <p style={{ fontSize: '12px', color: '#9ca3af' }}>간호사가 DICOM 파일을 업로드하면 자동으로 분석됩니다</p>
                </div>
                <button
                  className="btn btn-primary btn-sm"
                  onClick={() => navigate(`/dicom/${selectedPatient.patient_id}`)}
                >
                  DICOM 분석 페이지로 이동
                </button>
              </div>
            ) : (
              <>
                {/* AI 분석 결과 표시 */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                  gap: '12px',
                  marginBottom: '16px'
                }}>
                  {aiResult.slices.map((slice, idx) => (
                    <div
                      key={idx}
                      style={{
                        border: '2px solid #e1e4e8',
                        borderRadius: '8px',
                        overflow: 'hidden',
                        cursor: 'pointer',
                        transition: 'transform 0.2s, border-color 0.2s',
                      }}
                      onClick={() => navigate(`/dicom/${selectedPatient.patient_id}`)}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'scale(1.05)';
                        e.currentTarget.style.borderColor = '#0366d6';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.borderColor = '#e1e4e8';
                      }}
                    >
                      <img
                        src={`${API_BASE}${slice.url}`}
                        alt={slice.filename}
                        style={{
                          width: '100%',
                          height: 'auto',
                          display: 'block'
                        }}
                      />
                      <div style={{
                        padding: '6px',
                        background: '#f6f8fa',
                        fontSize: '11px',
                        textAlign: 'center',
                        color: '#586069'
                      }}>
                        슬라이스 {idx + 1}/{aiResult.total_slices}
                      </div>
                    </div>
                  ))}
                </div>

                {/* 분석 페이지로 이동 버튼 */}
                <div style={{ textAlign: 'center' }}>
                  <button
                    className="btn btn-primary btn-sm"
                    onClick={() => navigate(`/dicom/${selectedPatient.patient_id}`)}
                  >
                    🔬 상세 분석 보기
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;