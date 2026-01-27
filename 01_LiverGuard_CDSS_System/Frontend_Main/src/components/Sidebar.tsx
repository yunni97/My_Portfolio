import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ADMIN_URL } from '../services/apiConfig';

interface DoctorData {
    doctor_id: number;
    name: string;
    email: string;
    phone: string;
    department: string | null;
    position: string | null;
    sex: string;
}

interface SidebarProps {
    doctor: DoctorData;
    onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ doctor: _doctor, onLogout }) => {
    const navigate = useNavigate();
    const location = useLocation();

    const menuItems = [
        { path: '/dashboard', icon: '📊', label: '대시보드' },
        { path: '/patients', icon: '👥', label: '환자 관리' },
        { path: '/records', icon: '📋', label: '진료 기록' },
        { path: '/dicom', icon: '🔬', label: 'DICOM 분석' },
    ];

    const adminItems = [
        { path: '/admin', icon: '⚙️', label: '시스템 설정' },
        { path: '/logout', icon: '🚪', label: '로그아웃' },
    ];

    const isActive = (path: string) => {
        if (path === '/dashboard') {
            return location.pathname === '/dashboard' || location.pathname === '/';
        }
        return location.pathname.startsWith(path);
    };

    const handleMenuClick = (path: string) => {
        if (path === '/logout') {
            if (window.confirm('로그아웃 하시겠습니까?')) {
                onLogout();
            }
        } else if (path === '/admin') {
            window.open(ADMIN_URL, '_blank');
        } else {
            navigate(path);
        }
    };

    return (
        <div className="sidebar">
            <div className="sidebar-header">
                LiverGuard CDSS
            </div>

            <div className="sidebar-menu">
                {menuItems.map((item) => (
                    <a
                        key={item.path}
                        className={`menu-item ${isActive(item.path) ? 'active' : ''}`}
                        onClick={() => handleMenuClick(item.path)}
                    >
                        <span className="menu-icon">{item.icon}</span>
                        <span>{item.label}</span>
                    </a>
                ))}

                <div className="menu-group">관리</div>

                {adminItems.map((item) => (
                    <a
                        key={item.path}
                        className={`menu-item ${isActive(item.path) ? 'active' : ''}`}
                        onClick={() => handleMenuClick(item.path)}
                    >
                        <span className="menu-icon">{item.icon}</span>
                        <span>{item.label}</span>
                    </a>
                ))}
            </div>
        </div>
    );
};

export default Sidebar;