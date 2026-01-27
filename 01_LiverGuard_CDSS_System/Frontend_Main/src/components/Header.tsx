import React from 'react';
import { useNavigate } from 'react-router-dom';

interface DoctorData {
    doctor_id: number;
    name: string;
    email: string;
    phone: string;
    department: string | null;
    position: string | null;
    sex: string;
}

interface HeaderProps {
    doctor: DoctorData;
    onLogout: () => void;
}

const Header: React.FC<HeaderProps> = ({ doctor, onLogout }) => {
    const navigate = useNavigate();

    const handleProfileClick = () => {
        navigate('/profile');
    };

    const handleLogoutClick = () => {
        if (window.confirm('로그아웃 하시겠습니까?')) {
            onLogout();
        }
    };

    return (
        <div className="header">
            <div className="header-left">
                <h1
                    onClick={() => navigate('/dashboard')}
                    style={{ cursor: 'pointer' }}
                >
                    간암 의사결정지원시스템 (LiverGuard CDSS)
                </h1>
            </div>
            <div className="header-right">
                <span className="doctor-name">{doctor.name} 님</span>
                <button className="header-btn" onClick={handleProfileClick}>
                    프로필
                </button>
                <button className="header-btn" onClick={handleLogoutClick}>
                    로그아웃
                </button>
            </div>
        </div>
    );
};

export default Header;