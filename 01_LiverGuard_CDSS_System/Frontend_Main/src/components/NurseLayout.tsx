// src/components/NurseLayout.tsx

import React from 'react';
import { useNavigate } from 'react-router-dom';

interface NurseData {
  nurse_id: number;
  name: string;
  email: string;
  department: string | null;
}

interface NurseLayoutProps {
  nurse: NurseData;
  onLogout: () => void;
  children: React.ReactNode;
}

const NurseLayout: React.FC<NurseLayoutProps> = ({ nurse, onLogout, children }) => {
  const navigate = useNavigate();

  const handleProfileClick = () => {
    navigate('/nurse-profile');
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <h1 className="header-title" onClick={() => navigate('/nurse-dashboard')} style={{ cursor: 'pointer' }}>
            🏥 LiverGuard CDSS <span style={{ fontSize: '14px', color: '#6b7280' }}>(간호사)</span>
          </h1>
        </div>
        <div className="header-right">
          <span className="header-user">
            👩‍⚕️ {nurse.name} 간호사
          </span>
          <button className="header-btn" onClick={handleProfileClick}>
            프로필
          </button>
          <button className="header-btn logout-btn" onClick={onLogout}>
            로그아웃
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default NurseLayout;
