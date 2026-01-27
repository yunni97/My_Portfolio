// src/pages/DoctorProfile.tsx

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../services/apiConfig';

interface DoctorData {
  doctor_id: number;
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

interface DoctorProfileProps {
  doctor: DoctorData;
}

const DoctorProfile: React.FC<DoctorProfileProps> = ({ doctor }) => {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  // 프로필 수정 폼
  const [formData, setFormData] = useState({
    phone: doctor.phone || '',
    email: doctor.email || '',
    position: doctor.position || '',
    status: doctor.status || 'off_duty',
  });

  // 비밀번호 변경 폼
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // 프로필 정보 새로고침
  const [profileData, setProfileData] = useState<DoctorData>(doctor);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/doctors/${doctor.doctor_id}/profile/`);
      const data = await response.json();
      if (data.success) {
        setProfileData(data.data);
        setFormData({
          phone: data.data.phone || '',
          email: data.data.email || '',
          position: data.data.position || '',
          status: data.data.status || 'off_duty',
        });
      }
    } catch (err) {
      console.error('프로필 로드 실패:', err);
    }
  };

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const response = await fetch(`${API_BASE_URL}/doctors/${doctor.doctor_id}/profile/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (data.success) {
        setMessage('개인정보가 성공적으로 수정되었습니다.');
        setIsEditing(false);
        await fetchProfile();

        // localStorage 업데이트
        const storedData = localStorage.getItem('doctorData');
        if (storedData) {
          const updatedData = { ...JSON.parse(storedData), ...formData };
          localStorage.setItem('doctorData', JSON.stringify(updatedData));
        }
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다.');
      console.error('프로필 업데이트 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('새 비밀번호가 일치하지 않습니다.');
      setLoading(false);
      return;
    }

    if (passwordData.new_password.length < 4) {
      setError('비밀번호는 최소 4자 이상이어야 합니다.');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/doctors/${doctor.doctor_id}/change-password/`, {
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
        setIsChangingPassword(false);
        setPasswordData({
          current_password: '',
          new_password: '',
          confirm_password: '',
        });
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다.');
      console.error('비밀번호 변경 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>의사 개인정보</h1>
          <p style={{ color: '#586069', fontSize: '14px' }}>개인정보를 조회하고 수정할 수 있습니다.</p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={() => navigate('/dashboard')}
        >
          ← 대시보드로
        </button>
      </div>

      {/* 메시지 표시 */}
      {message && (
        <div style={{
          padding: '12px 16px',
          background: '#d4edda',
          border: '1px solid #c3e6cb',
          borderRadius: '6px',
          color: '#155724',
          marginBottom: '16px',
        }}>
          {message}
        </div>
      )}

      {error && (
        <div style={{
          padding: '12px 16px',
          background: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '6px',
          color: '#721c24',
          marginBottom: '16px',
        }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* 왼쪽: 프로필 정보 */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>👨‍⚕️ 기본 정보</span>
            {!isEditing && (
              <button
                className="btn btn-primary btn-sm"
                onClick={() => setIsEditing(true)}
              >
                수정
              </button>
            )}
          </div>
          <div className="card-body">
            {!isEditing ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '36px',
                    color: 'white',
                  }}>
                    {profileData.sex === 'male' ? '👨‍⚕️' : '👩‍⚕️'}
                  </div>
                  <div>
                    <div style={{ fontSize: '20px', fontWeight: 600, marginBottom: '4px' }}>{profileData.name}</div>
                    <div style={{ color: '#586069', fontSize: '13px' }}>{profileData.position || '의사'}</div>
                  </div>
                </div>

                <div style={{ borderTop: '1px solid #e1e4e8', paddingTop: '16px' }}>
                  <div className="detail-grid" style={{ gap: '12px' }}>
                    <div className="detail-item">
                      <div className="detail-key">ID</div>
                      <div className="detail-val">{profileData.doctor_id}</div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">이름</div>
                      <div className="detail-val">{profileData.name}</div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">성별</div>
                      <div className="detail-val">
                        {profileData.sex === 'male' ? '남성' : '여성'}
                      </div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">연락처</div>
                      <div className="detail-val">{profileData.phone || '-'}</div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">이메일</div>
                      <div className="detail-val">{profileData.email || '-'}</div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">부서</div>
                      <div className="detail-val">{profileData.department || '-'}</div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">직책</div>
                      <div className="detail-val">{profileData.position || '-'}</div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">상태</div>
                      <div className="detail-val">
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          background: profileData.status === 'on_duty' ? '#d4edda' : '#f8f9fa',
                          color: profileData.status === 'on_duty' ? '#155724' : '#6c757d',
                        }}>
                          {profileData.status === 'on_duty' ? '근무중' :
                           profileData.status === 'available' ? '대기중' : '퇴근'}
                        </span>
                      </div>
                    </div>
                    <div className="detail-item">
                      <div className="detail-key">등록일</div>
                      <div className="detail-val">
                        {profileData.created_at ? new Date(profileData.created_at).toLocaleDateString('ko-KR') : '-'}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <form onSubmit={handleProfileUpdate}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label className="form-label">연락처</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      placeholder="010-1234-5678"
                    />
                  </div>

                  <div>
                    <label className="form-label">이메일</label>
                    <input
                      type="email"
                      className="form-control"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="doctor@hospital.com"
                    />
                  </div>

                  <div>
                    <label className="form-label">직책</label>
                    <input
                      type="text"
                      className="form-control"
                      value={formData.position}
                      onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                      placeholder="전문의, 과장 등"
                    />
                  </div>

                  <div>
                    <label className="form-label">근무 상태</label>
                    <select
                      className="form-control"
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    >
                      <option value="on_duty">근무중</option>
                      <option value="available">대기중</option>
                      <option value="off_duty">퇴근</option>
                    </select>
                  </div>

                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                      style={{ flex: 1 }}
                    >
                      {loading ? '저장 중...' : '저장'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => {
                        setIsEditing(false);
                        setFormData({
                          phone: profileData.phone || '',
                          email: profileData.email || '',
                          position: profileData.position || '',
                          status: profileData.status || 'off_duty',
                        });
                      }}
                      style={{ flex: 1 }}
                    >
                      취소
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* 오른쪽: 비밀번호 변경 */}
        <div className="card">
          <div className="card-header">🔒 비밀번호 변경</div>
          <div className="card-body">
            {!isChangingPassword ? (
              <div style={{ textAlign: 'center', padding: '40px 20px' }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔐</div>
                <p style={{ color: '#586069', marginBottom: '24px' }}>
                  보안을 위해 정기적으로 비밀번호를 변경해주세요.
                </p>
                <button
                  className="btn btn-primary"
                  onClick={() => setIsChangingPassword(true)}
                >
                  비밀번호 변경하기
                </button>
              </div>
            ) : (
              <form onSubmit={handlePasswordChange}>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div>
                    <label className="form-label">현재 비밀번호</label>
                    <input
                      type="password"
                      className="form-control"
                      value={passwordData.current_password}
                      onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                      placeholder="현재 비밀번호를 입력하세요"
                      required
                    />
                  </div>

                  <div>
                    <label className="form-label">새 비밀번호</label>
                    <input
                      type="password"
                      className="form-control"
                      value={passwordData.new_password}
                      onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                      placeholder="새 비밀번호를 입력하세요"
                      required
                    />
                    <small style={{ color: '#6a737d', fontSize: '12px', marginTop: '4px', display: 'block' }}>
                      최소 4자 이상 입력해주세요
                    </small>
                  </div>

                  <div>
                    <label className="form-label">새 비밀번호 확인</label>
                    <input
                      type="password"
                      className="form-control"
                      value={passwordData.confirm_password}
                      onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                      placeholder="새 비밀번호를 다시 입력하세요"
                      required
                    />
                  </div>

                  <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={loading}
                      style={{ flex: 1 }}
                    >
                      {loading ? '변경 중...' : '비밀번호 변경'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={() => {
                        setIsChangingPassword(false);
                        setPasswordData({
                          current_password: '',
                          new_password: '',
                          confirm_password: '',
                        });
                        setError('');
                      }}
                      style={{ flex: 1 }}
                    >
                      취소
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>
      </div>

      {/* 추가 정보 섹션 */}
      <div className="card" style={{ marginTop: '24px' }}>
        <div className="card-header">ℹ️ 계정 정보</div>
        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div style={{ padding: '16px', background: '#f6f8fa', borderRadius: '6px' }}>
              <div style={{ fontSize: '13px', color: '#586069', marginBottom: '4px' }}>의사 ID</div>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>{profileData.doctor_id}</div>
              <small style={{ color: '#6a737d', fontSize: '11px' }}>변경 불가</small>
            </div>
            <div style={{ padding: '16px', background: '#f6f8fa', borderRadius: '6px' }}>
              <div style={{ fontSize: '13px', color: '#586069', marginBottom: '4px' }}>부서 코드</div>
              <div style={{ fontSize: '16px', fontWeight: 600 }}>{profileData.department_code || '-'}</div>
              <small style={{ color: '#6a737d', fontSize: '11px' }}>관리자에게 문의</small>
            </div>
          </div>

          <div style={{ marginTop: '16px', padding: '12px', background: '#fff3cd', border: '1px solid #ffeeba', borderRadius: '6px' }}>
            <strong style={{ color: '#856404' }}>📌 참고사항</strong>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', color: '#856404', fontSize: '13px' }}>
              <li>의사 ID와 이름은 변경할 수 없습니다.</li>
              <li>부서 변경은 관리자에게 문의해주세요.</li>
              <li>비밀번호는 정기적으로 변경하는 것을 권장합니다.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DoctorProfile;
