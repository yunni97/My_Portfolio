import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './MenuBar.css';

interface MenuBarProps {
    activeTab?: string;
    onTabChange?: (tab: string) => void;
}

const MenuBar: React.FC<MenuBarProps> = ({ activeTab = '진료기록', onTabChange }) => {
    const navigate = useNavigate();
    const [currentTab, setCurrentTab] = useState(activeTab);

    const tabs = ['진료기록', 'CT영상', '예후진단'];

    const handleTabClick = (tab: string) => {
        setCurrentTab(tab);
        if (onTabChange) {
            onTabChange(tab);
        }

        // 탭에 따라 페이지 이동
        if (tab === '진료기록') {
            navigate('/patients');
        } else if (tab === 'CT영상') {
            navigate('/dicom');
        } else if (tab === '예후진단') {
            navigate('/survival');
        }
    };

    return (
        <div className="menu-bar">
            <div className="menu-tabs">
                {tabs.map((tab) => (
                    <button
                        key={tab}
                        className={`menu-tab ${currentTab === tab ? 'active' : ''}`}
                        onClick={() => handleTabClick(tab)}
                    >
                        {tab}
                    </button>
                ))}
            </div>
        </div>
    );
};

export default MenuBar;
