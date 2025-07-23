import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import '../styles/Sidebar.css';

import LogoIcon from '../images/logo.svg';
import HomeIcon from '../images/home.svg';
import RecoveryIcon from '../images/recovery.svg';
import SettingIcon from '../images/setting.svg';
import InfoIcon from '../images/information.svg';

const Sidebar = () => {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'HOME', icon: HomeIcon, alt: 'HOME 아이콘' },
    { path: '/fileUpload', label: 'Recovery', icon: RecoveryIcon, alt: 'Recovery 아이콘' },
    { path: '/setting', label: 'Setting', icon: SettingIcon, alt: 'Setting 아이콘' },
    { path: '/information', label: 'Information', icon: InfoIcon, alt: 'Information 아이콘' },
  ];

  return (
    <div id="sidebar" className="container">
  <div className="menu_box">
    <div className="logo_section">
      <img src={LogoIcon} alt="앱로고" className="logo_icon" />
      <span className="logo_text">RETATO</span>
    </div>
    <div className="menu_title_section">
      <div className="menu_title">MENU</div>
      <div className="menu_divider" />
    </div>
    <ul className="menu_list">
      {navItems.map(({ path, label, icon, alt }) => (
        <li key={path}>
          <Link
            to={path}
            className={`menu_item${location.pathname === path ? ' active' : ''}`}
          >
            <img src={icon} alt={alt} className="menu_icon" />
            {label}
          </Link>
        </li>
      ))}
    </ul>
    </div>
  </div>
  );
};

export default Sidebar;
