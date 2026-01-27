// src/pages/NurseProfile.tsx

import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../services/apiConfig';

interface NurseData {
  nurse_id: number;
  name: string;
  email: string;
  phone: string;
  department: string | null;
  department_code: string | null;
  position: string | null;
  status: string;
  sex: string;
  created_at?: string;
}

interface NurseProfileProps {
  nurse: NurseData;
}

const NurseProfile: React.FC<NurseProfileProps> = ({ nurse }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // 프로필 편집 폼
  const [formData, setFormData] = useState({
    phone: nurse.phone || '',
    email: nurse.email || '',
    position: nurse.position || '',
    status: nurse.status || 'on_duty',
  });

  // 비밀번호 변경 폼
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState<'success' | 'error'>('success');

  useEffect(() => {
    setFormData({
      phone: nurse.phone || '',
      email: nurse.email || '',
      position: nurse.position || '',
      status: nurse.status || 'on_duty',
    });
  }, [nurse]);

  // 프로필 저장
  const handleSaveProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/nurses/${nurse.nurse_id}/profile/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.success) {
        setMessage('프로필이 성공적으로 수정되었습니다.');
        setMessageType('success');
        setIsEditing(false);

        // localStorage 업데이트
        const nurseData = JSON.parse(localStorage.getItem('nurseData') || '{}');
        localStorage.setItem('nurseData', JSON.stringify({ ...nurseData, ...formData }));

        setTimeout(() => window.location.reload(), 1500);
      } else {
        setMessage(data.message || '프로필 수정에 실패했습니다.');
        setMessageType('error');
      }
    } catch (error) {
      console.error('프로필 수정 오류:', error);
      setMessage('서버 연결 오류가 발생했습니다.');
      setMessageType('error');
    }
  };

  // 비밀번호 변경
  const handleChangePassword = async () => {
    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage('새 비밀번호가 일치하지 않습니다.');
      setMessageType('error');
      return;
    }

    if (passwordData.new_password.length < 4) {
      setMessage('비밀번호는 최소 4자 이상이어야 합니다.');
      setMessageType('error');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/nurses/${nurse.nurse_id}/change-password/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: passwordData.current_password,
          new_password: passwordData.new_password,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setMessage('비밀번호가 성공적으로 변경되었습니다.');
        setMessageType('success');
        setIsChangingPassword(false);
        setPasswordData({
          current_password: '',
          new_password: '',
          confirm_password: '',
        });
      } else {
        setMessage(data.message || '비밀번호 변경에 실패했습니다.');
        setMessageType('error');
      }
    } catch (error) {
      console.error('비밀번호 변경 오류:', error);
      setMessage('서버 연결 오류가 발생했습니다.');
      setMessageType('error');
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <div className="detail-card" style={{ marginBottom: '20px' }}>
        <div className="detail-title">👩‍⚕️ 간호사 프로필</div>

        {message && (
          <div style={{
            padding: '12px',
            marginBottom: '16px',
            borderRadius: '6px',
            background: messageType === 'success' ? '#10b98120' : '#ef444420',
            border: `1px solid ${messageType === 'success' ? '#10b981' : '#ef4444'}`,
            color: messageType === 'success' ? '#10b981' : '#ef4444',
          }}>
            {message}
          </div>
        )}

        <div className="detail-grid" style={{ gap: '16px' }}>
          {/* 간호사 ID (읽기 전용) */}
          <div className="detail-item">
            <div className="detail-key">간호사 ID</div>
            <div className="detail-val" style={{ color: '#6b7280' }}>{nurse.nurse_id}</div>
          </div>

          {/* 이름 (읽기 전용) */}
          <div className="detail-item">
            <div className="detail-key">이름</div>
            <div className="detail-val" style={{ color: '#6b7280' }}>{nurse.name}</div>
          </div>

          {/* 성별 (읽기 전용) */}
          <div className="detail-item">
            <div className="detail-key">성별</div>
            <div className="detail-val" style={{ color: '#6b7280' }}>
              {nurse.sex === 'male' ? '남성' : nurse.sex === 'female' ? '여성' : nurse.sex}
            </div>
          </div>

          {/* 부서 (읽기 전용) */}
          <div className="detail-item">
            <div className="detail-key">부서</div>
            <div className="detail-val" style={{ color: '#6b7280' }}>{nurse.department || '-'}</div>
          </div>

          {/* 연락처 (편집 가능) */}
          <div className="detail-item">
            <div className="detail-key">연락처</div>
            <div className="detail-val">
              {isEditing ? (
                <input
                  type="tel"
                  className="form-control"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  style={{ width: '100%' }}
                />
              ) : (
                <span>{formData.phone || '-'}</span>
              )}
            </div>
          </div>

          {/* 이메일 (편집 가능) */}
          <div className="detail-item">
            <div className="detail-key">이메일</div>
            <div className="detail-val">
              {isEditing ? (
                <input
                  type="email"
                  className="form-control"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  style={{ width: '100%' }}
                />
              ) : (
                <span>{formData.email || '-'}</span>
              )}
            </div>
          </div>

          {/* 직급 (편집 가능) */}
          <div className="detail-item">
            <div className="detail-key">직급</div>
            <div className="detail-val">
              {isEditing ? (
                <input
                  type="text"
                  className="form-control"
                  value={formData.position}
                  onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                  style={{ width: '100%' }}
                />
              ) : (
                <span>{formData.position || '-'}</span>
              )}
            </div>
          </div>

          {/* 근무 상태 (편집 가능) */}
          <div className="detail-item">
            <div className="detail-key">근무 상태</div>
            <div className="detail-val">
              {isEditing ? (
                <select
                  className="form-control"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  style={{ width: '100%' }}
                >
                  <option value="on_duty">근무 중</option>
                  <option value="off_duty">퇴근</option>
                  <option value="on_leave">휴가</option>
                </select>
              ) : (
                <span>{formData.status === 'on_duty' ? '근무 중' : formData.status === 'off_duty' ? '퇴근' : '휴가'}</span>
              )}
            </div>
          </div>

          {/* 등록일 (읽기 전용) */}
          <div className="detail-item">
            <div className="detail-key">등록일</div>
            <div className="detail-val" style={{ color: '#6b7280' }}>
              {nurse.created_at ? new Date(nurse.created_at).toLocaleDateString('ko-KR') : '-'}
            </div>
          </div>
        </div>

        {/* 버튼 영역 */}
        <div style={{ marginTop: '24px', display: 'flex', gap: '8px' }}>
          {isEditing ? (
            <>
              <button className="btn btn-primary" onClick={handleSaveProfile}>
                💾 저장
              </button>
              <button className="btn btn-secondary" onClick={() => setIsEditing(false)}>
                취소
              </button>
            </>
          ) : (
            <button className="btn btn-primary" onClick={() => setIsEditing(true)}>
              ✏️ 프로필 수정
            </button>
          )}
          <button
            className="btn"
            style={{ background: '#8B5CF6', color: 'white' }}
            onClick={() => setIsChangingPassword(!isChangingPassword)}
          >
            🔒 비밀번호 변경
          </button>
        </div>
      </div>

      {/* 비밀번호 변경 섹션 */}
      {isChangingPassword && (
        <div className="detail-card">
          <div className="detail-title">🔐 비밀번호 변경</div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div>
              <label className="detail-key" style={{ display: 'block', marginBottom: '8px' }}>
                현재 비밀번호
              </label>
              <input
                type="password"
                className="form-control"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                placeholder="현재 비밀번호를 입력하세요"
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label className="detail-key" style={{ display: 'block', marginBottom: '8px' }}>
                새 비밀번호
              </label>
              <input
                type="password"
                className="form-control"
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                placeholder="새 비밀번호를 입력하세요"
                style={{ width: '100%' }}
              />
            </div>

            <div>
              <label className="detail-key" style={{ display: 'block', marginBottom: '8px' }}>
                새 비밀번호 확인
              </label>
              <input
                type="password"
                className="form-control"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                placeholder="새 비밀번호를 다시 입력하세요"
                style={{ width: '100%' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-primary" onClick={handleChangePassword}>
                비밀번호 변경
              </button>
              <button className="btn btn-secondary" onClick={() => {
                setIsChangingPassword(false);
                setPasswordData({
                  current_password: '',
                  new_password: '',
                  confirm_password: '',
                });
              }}>
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default NurseProfile;
