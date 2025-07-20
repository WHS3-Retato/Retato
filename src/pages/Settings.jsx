import React, { useState } from 'react';
import '../styles/Setting.css';
import Button from '../components/Button';

const Settings = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [savePath, setSavePath] = useState('C:\\Users\\Downloads');
  const [videoFormat, setVideoFormat] = useState('AVI');

  const handlePathChange = () => {
    // Electron ipcRenderer 등을 사용해야 실제로 경로 선택 가능
    const fakePath = 'C:\\Users\\Retato\\Recovered'; // 테스트용
    setSavePath(fakePath);
  };

  return (
    <div className="settings_page">
      <h1 className="settings_title">Setting</h1>
      <p className="settings_desc">RETATO 애플리케이션의 설정을 관리하세요</p>

      {/* 테마 설정 */}
      <div className="settings_box">
        <h2 className="settings_box_title">테마 설정</h2>
        <p className="settings_box_desc">다크 모드를 활성화하거나 비활성화합니다</p>
        <label className="toggle-switch">
          <input type="checkbox" checked={isDarkMode} onChange={() => setIsDarkMode(!isDarkMode)} />
          <span className="slider"></span>
        </label>
      </div>

      {/* 저장 경로 설정 */}
      <div className="settings_box">
        <h2 className="settings_box_title">저장 경로 설정</h2>
        <p className="settings_box_desc">복구된 파일이 저장될 기본 경로를 설정합니다</p>
        <div className="path_input_area">
          <input type="text" value={savePath} readOnly className="path_input" />
          <div className="path_input_area">
            <input type="text" value={savePath} readOnly className="path_input" />
            <Button variant="dark" onClick={handlePathChange}>찾아보기</Button>
          </div>
        </div>
      </div>

      {/* 영상 포맷 설정 */}
      <div className="settings_box">
        <h2 className="settings_box_title">영상 다운로드 포맷</h2>
        <p className="settings_box_desc">다운로드할 영상 파일의 기본 포맷을 선택하세요</p>
        <div className="format_options">
          <label className={`radio-btn ${videoFormat === 'AVI' ? 'selected' : ''}`}>
            <input type="radio" value="AVI" checked={videoFormat === 'AVI'} onChange={() => setVideoFormat('AVI')} />
            AVI
          </label>
          <label className={`radio-btn ${videoFormat === 'MP4' ? 'selected' : ''}`}>
            <input type="radio" value="MP4" checked={videoFormat === 'MP4'} onChange={() => setVideoFormat('MP4')} />
            MP4
          </label>
        </div>
      </div>
    </div>
  );
};

export default Settings;
