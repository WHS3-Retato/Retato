import React, { useRef, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import Stepbar from '../components/Stepbar.jsx';
import Box from '../components/Box.jsx';
import Button from '../components/Button.jsx';
import Alert from '../components/Alert.jsx';
import Badge from '../components/Badge.jsx';
import Potato from '../components/Potato.jsx';
import '../styles/Stepbar.css';  
import '../styles/Recovery.css'; 
import '../styles/Button.css';
import '../styles/Alert.css';
import alertIcon from '../images/alert_file.svg';
import drivingIcon from '../images/driving.svg';
import parkingIcon from '../images/parking.svg';
import eventIcon from '../images/event.svg';
import deletedIcon from '../images/deleted.svg';
import downloadIcon from '../images/download.svg';
import basicIcon from '../images/information.svg';
import integrityIcon from '../images/integrity.svg';
import slackIcon from '../images/slack.svg';
import structureIcon from '../images/struc.svg';
import replayIcon from '../images/view_replay.svg';
import pauseIcon from '../images/view_pause.svg';
import fullscreenIcon from '../images/view_fullscreen.svg';
import integrityGreen from '../images/integrity_g.svg';
import integrityRed from '../images/integrity_r.svg';
import integrityYellow from '../images/integrity_y.svg';
import completeIcon from '../images/complete.svg';
import { useNavigate } from 'react-router-dom';

const Recovery = () => {
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const [showAlert, setShowAlert] = useState(false);
  const [recoveryDone, setRecoveryDone] = useState(false);
  const [showDownloadPopup, setShowDownloadPopup] = useState(false);

  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedPath, setSelectedPath] = useState("C:\\Users\\Downloads");

  const [isRecovering, setIsRecovering] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentCount, setCurrentCount] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);

  const [selectedAnalysisFile, setSelectedAnalysisFile] = useState(null); 
  const [activeTab, setActiveTab] = useState('basic');
  const [showComplete, setShowComplete] = useState(false);
  const [showDownloadAlert, setShowDownloadAlert] = useState(false);
  
  const location = useLocation();

  const [autoStart, setAutoStart] = useState(location.state?.autoStart || false);

  useEffect(() => {
    if (progress >= 100) {
      setIsRecovering(false);
      setRecoveryDone(true); 
    }

    setHistory(prev => [...prev, 'result']);
    setView('result');

  }, [progress]);

  const categoryIcons = {
    driving: drivingIcon,
    parking: parkingIcon,
    event: eventIcon,
    slack: slackIcon,
    deleted: deletedIcon,
  };

  // Progress Bar, 나중에 백엔드 연동 예정
  useEffect(() => {
  if (isRecovering) {
    const interval = setInterval(() => {
      setCurrentCount((prev) => {
        const next = prev + 100;
        const newProgress = Math.floor((next / 300) * 100); // 총 300개로 가정

        setProgress(newProgress);

        if (newProgress >= 100) {
          clearInterval(interval);
          setProgress(100);
          setIsRecovering(false);   
          setRecoveryDone(true);    
        }

        return next;
      });
    }, 8000);

    return () => clearInterval(interval);
  }
}, [isRecovering]);


  const handleFile = (file) => {
    if (!file.name.toLowerCase().endsWith('.e01')) {
      setShowAlert(true);
      return;
    }

    setSelectedFile(file);
    setShowAlert(false);
    
    setIsRecovering(true);
    setCurrentCount(0);
    setProgress(0);
    setTotalFiles(300);
  };


  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  };

  const handleClick = () => {
    inputRef.current.click();
  };

  const startRecovery = () => {
    if (!selectedFile) return;
    setShowRange(false);
    setIsRecovering(true);
    setCurrentCount(0);
    setProgress(0);
    setTotalFiles(300);
    setShowComplete(true); // 하드코딩: 백엔드에서 받을 예정
  };

  const toggleGroup = (id) => {
    const el = document.getElementById(id);
    if (!el) return;
    const isOpen = el.style.display === 'block';
    el.style.display = isOpen ? 'none' : 'block';

    const headers = document.getElementsByClassName('result-group-header');
    for (let h of headers) {
      if (h.textContent.includes(id.charAt(0).toUpperCase() + id.slice(1))) {
        h.classList.toggle('open', !isOpen);
      }
    }
  };

  const confirmDownload = () => {
    console.log("최종 저장 경로:", selectedPath);
  };

  const handleDownload = () => {
    setShowDownloadPopup(true); 
  };

  const closeDownloadPopup = () => {
    setShowDownloadPopup(false); // 팝업 닫기
  };

  const handleInvalidFile = () => {
    setShowAlert(true);
  };

  const handleDownloadClick = () => {
    setShowDownloadPopup(true);
  };

  const handleFolderSelect = async () => {
    const path = await window.electronAPI.selectFolder();
    if (path) setSelectedPath(path);
  };

  // 다운로드 백엔드
  const handleDownloadConfirm = () => {
  // 다운로드 로직 (백엔드 연결 예정)
  setShowComplete(true);
  setShowComplete(true); 
  setShowDownloadPopup(false); // 팝업 닫기
  };

  const handleDownloadCancel = () => {
    setShowDownloadPopup(false);
  };

  const handleFileClick = (filename) => {
    setSelectedAnalysisFile(filename);   
    setActiveTab('basic'); 
    setHistory(prev => [...prev, 'parser']);
    setView('parser');            
  };

  const handlePathSelect = async () => {
    const result = await window.api.selectFolder();  // api로 접근
    if (result && !result.canceled && result.filePaths.length > 0) {
      setSelectedPath(result.filePaths[0]);  // 경로 반영
    }
  };

  // Stepbar currentStep
  let currentStep = 0;

  if (showComplete) {
    currentStep = 3;
  } else if (isRecovering) {
    currentStep = 1;
  } else if (recoveryDone) {
    currentStep = 2;
  } else {
    currentStep = 0;
  }

  // view
  useEffect(() => {
  const video = document.getElementById('parser-video');
  const playPauseBtn = document.getElementById('playPauseBtn');
  const playPauseIcon = document.getElementById('playPauseIcon');
  const replayBtn = document.getElementById('replayBtn');
  const fullscreenBtn = document.getElementById('fullscreenBtn');
  const progressBar = document.getElementById('progressBar');
  const timeText = document.getElementById('timeText');

  if (!video) return;

  playPauseBtn.onclick = () => {
    if (video.paused) {
      video.play();
      playPauseIcon.src = 'view_pause.svg';
    } else {
      video.pause();
      playPauseIcon.src = 'view_play.svg';
    }
  };

  replayBtn.onclick = () => {
    video.currentTime = 0;
    video.play();
  };

  fullscreenBtn.onclick = () => {
    if (video.requestFullscreen) video.requestFullscreen();
  };

  video.ontimeupdate = () => {
    progressBar.value = video.currentTime;
    timeText.textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
  };

  progressBar.oninput = () => {
    video.currentTime = progressBar.value;
  };

  video.onloadedmetadata = () => {
    progressBar.max = video.duration;
  };

  function formatTime(seconds) {
    const min = Math.floor(seconds / 60).toString().padStart(2, '0');
    const sec = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${min}:${sec}`;
  }
}, []); // 컴포넌트가 mount될 때 1번만 실행

  const startRecoveryFromDownload = () => {
    setShowDownloadPopup(false);  
    setShowComplete(false);   
    setIsRecovering(true); 
    setCurrentCount(0);
    setProgress(0);
    setTotalFiles(300);      
  };

  // closeButton -> Result 뒤로가기
  const [view, setView] = useState('upload');
  const [history, setHistory] = useState(['upload']);

  const handleBack = () => {
    console.log('뒤로가기 실행됨');
    if (history.length > 1) {
      const newHistory = [...history];
      newHistory.pop();
      const prevView = newHistory[newHistory.length - 1];
      console.log('이전 화면:', prevView);
      setHistory(newHistory);
      setView(prevView);

      if (prevView === 'upload') {
        setIsRecovering(false);
        setRecoveryDone(false);
        setShowComplete(false);
        setSelectedAnalysisFile(null);
      } else if (prevView === 'recovering') {
        setIsRecovering(true);
        setRecoveryDone(false);
        setShowComplete(false);
        setSelectedAnalysisFile(null);
      } else if (prevView === 'result') {
        setIsRecovering(false);
        setRecoveryDone(true);
        setShowComplete(false);
        setSelectedAnalysisFile(null);
      } else if (prevView === 'parser') {
        setIsRecovering(false);
        setRecoveryDone(true);
        setShowComplete(false);
      }
    }
  };


  return (
  <>
  <Stepbar currentStep={currentStep} />
  <Box>
    {showComplete ? (
    <>
      <h1 className="upload-title">Result</h1>
      <div className="recovery-complete-area">
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
        }}>
          <img src={completeIcon} alt="완료 아이콘" style={{ width: '100px', margin: '3rem 0', marginTop:'5rem'}} />
        </div>
        <p style={{ textAlign: 'center', fontSize: '1rem' }}>
          선택된 경로에 복원된 영상이 저장되었습니다.
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem' }}>
          <Button variant="dark" onClick={() => navigate('/')}>홈으로</Button>
        </div>
      </div>
    </>
    ) : isRecovering ? (
        <>
          <h1 className="upload-title">File Recovery</h1>
          <p className="recovery-desc-left">잠시만 기다려 주세요… 영상을 복원하고 있어요</p>

          <div className="recovery-file-box">
              <div className="recovery-file-left">
                <Badge label="진행중" />
                <span className="file-name">{selectedFile?.name}</span>
              </div>
              <button className="close-btn" onClick={() => setIsRecovering(false)}>✕</button>
              </div>
              <div style={{ display: "flex", justifyContent: "center" }}>
                <Potato />
              </div>
          <div className="recovery-desc-center">Recovering...</div>

          <div className="progress-bar-wrapper">
            <div className="progress-bar-track">
              <div
                className="progress-bar-fill"
                style={{
                  width: `${progress}%`,
                  transition: 'width 0.6s ease',
                }}
              />
            </div>
          </div>
        </>
  ) : !isRecovering && !recoveryDone ? (
      <>
      <h1 className="upload-title">File Upload</h1>
      <p className="upload-subtitle">E01 파일을 업로드 해주세요</p>
        <div
          className="dropzone"
          id="dadDrop"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={handleClick}
        >
          <p className="dropzone-title">복구할 블랙박스 이미지(E01) 선택</p>
          <p className="dropzone-desc">
            E01 파일을 드래그 앤 드롭하거나 클릭하여 선택하세요<br />
            분할된 E01 파일(.E01, E02, E03 ...)을 자동으로 인식합니다
          </p>

          <input
            type="file"
            id="dadFile"
            accept=".E01"
            ref={inputRef}
            onChange={handleFileChange}
            hidden
          />
          <Button variant="gray">
            ⭱ <span>{selectedFile ? selectedFile.name : '업로드'}</span>
          </Button>
        </div>
        </>

        // 여기부터 Result Parser
    ) : recoveryDone ? (
      selectedAnalysisFile ? (
        <>
        <h1 className="upload-title">Result</h1>

        <div className="recovery-file-box">
          <span className="file-name">{selectedAnalysisFile}</span>
          <div className="recovery-file-controls">
            <Badge label="전방" onClick={() => console.log('전방 선택')} />
            <Badge label="후방" onClick={() => console.log('후방 클릭')} />
            <button className="close-btn" onClick={handleBack}>✕</button>
          </div>
        </div>


        <div className="result-scroll-area">
          {/* View */}
          <div className="video-container">
            <video
              id="parser-video"
              preload="metadata"
              src={`/stream/${encodeURIComponent(selectedAnalysisFile)}`}
            ></video>

            <div className="parser-controls">
              <button id="replayBtn">
                <img src={replayIcon} alt="Replay" />
              </button>
              <button id="playPauseBtn">
                <img id="playPauseIcon" src={pauseIcon} alt="Pause" />
              </button>
              <input type="range" id="progressBar" min="0" value="0" step="0.01" />
              <span id="timeText">00:00 / 00:00</span>
              <button id="fullscreenBtn">
                <img src={fullscreenIcon} alt="Fullscreen" />
              </button>
            </div>
          </div>

          {/* Parser */}
        <div className="parser-tabs">
            <button
              className={`parser-tab-button ${activeTab === 'basic' ? 'active' : ''}`}
              onClick={() => setActiveTab('basic')}
            >
              <img src={basicIcon} alt="기본 정보" />
              <span>기본 정보</span>
            </button>
            <button
              className={`parser-tab-button ${activeTab === 'integrity' ? 'active' : ''}`}
              onClick={() => setActiveTab('integrity')}
            >
              <img src={integrityIcon} alt="무결성 검사" />
              <span>무결성 검사</span>
            </button>
            <button
              className={`parser-tab-button ${activeTab === 'slack' ? 'active' : ''}`}
              onClick={() => setActiveTab('slack')}
            >
              <img src={slackIcon} alt="슬랙 정보" />
              <span>슬랙 정보</span>
            </button>
            <button
              className={`parser-tab-button ${activeTab === 'structure' ? 'active' : ''}`}
              onClick={() => setActiveTab('structure')}
            >
              <img src={structureIcon} alt="구조 정보" />
              <span>구조 정보</span>
            </button>
          </div>

          {/* 기본 정보 */}
          <div className={`parser-tab-content ${activeTab === 'basic' ? 'active' : ''}`}>
            <div className="parser-info-table">
              <div className="parser-info-row">
                <span className="parser-info-label">파일 포맷:</span>
                <span className="parser-info-value">MP4</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">생성 시간:</span>
                <span className="parser-info-value">2024-12-30 09:30:45</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">수정 시간:</span>
                <span className="parser-info-value">2024-12-30 09:30:45</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">마지막 접근 시간:</span>
                <span className="parser-info-value">2024-12-30 09:30:45</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">파일 크기:</span>
                <span className="parser-info-value">2.1 GB</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">재생 시간:</span>
                <span className="parser-info-value">00:30</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">비디오 코덱:</span>
                <span className="parser-info-value">H.264</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">해상도:</span>
                <span className="parser-info-value">1920×1080</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">프레임 레이트:</span>
                <span className="parser-info-value">30 fps</span>
              </div>
            </div>
          </div>

          <div className={`parser-tab-content ${activeTab === 'integrity' ? 'active' : ''}`}>
            <div className={`parser-tab-content ${activeTab === 'integrity' ? 'active' : ''}`}>
            <div className="parser-info-table">
              <div className="parser-info-row">
                <span className="parser-info-label">전체 상태:</span>
                <span className="parser-info-value">
                  <img src={integrityYellow} alt="부분 손상" className="status-icon" />
                  <span className="status-text yellow">부분 손상</span>
                </span>
              </div>
                <div className="parser-info-row">
                  <span className="parser-info-label">moov box:</span>
                  <span className="parser-info-value">
                    <img src={integrityRed} alt="심각한 손상" className="status-icon" />
                    <span className="status-text red">심각한 손상</span>
                  </span>
                </div>
                <div className="parser-info-row">
                  <span className="parser-info-label">mdat box:</span>
                  <span className="parser-info-value">
                    <img src={integrityGreen} alt="정상" className="status-icon" />
                    <span className="status-text green">정상</span>
                  </span>
                </div>
                <div className="parser-info-row">
                  <span className="parser-info-label">헤더 손상:</span>
                  <span className="parser-info-value">
                    <img src={integrityGreen} alt="정상" className="status-icon" />
                    <span className="status-text green">정상</span>
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className={`parser-tab-content ${activeTab === 'slack' ? 'active' : ''}`}>
            <div className="parser-info-table">
              <div className="parser-info-row">
                <span className="parser-info-label">전체 크기:</span>
                <span className="parser-info-value">47,448,064 bytes</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">사용된 크기:</span>
                <span className="parser-info-value">47,448,064 bytes</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">슬랙 크기:</span>
                <span className="parser-info-value">2,248,064 bytes</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">슬랙 비율:</span>
                <span className="parser-info-value">4.7%</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">유효 데이터 비율:</span>
                <span className="parser-info-value">95.3%</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">데이터 분포</span>
              </div>
              <div className="data-bar-wrapper">
                <div
                  className="data-bar-used"
                  style={{ width: '95.3%' }} // 유효 데이터 비율만큼 채움
                />
              </div>
            </div>
          </div>

          <div className={`parser-tab-content ${activeTab === 'structure' ? 'active' : ''}`}>
            <div className="parser-structure">
                <h4>AVI Structure</h4>
                  file size : 0x6AAAFEA<br />
                  file data size : 0x6AAAEF2<br />
                  <br />
                  [LIST-hdrl] offset: 0xC / size: 0x21C<br />
                  JUNK start offset : 0x230<br />
                  JUNK size : 0xF4<br />
                  <br />
                  [LIST-movi] offset: 0x32C / size: 0x6A9BECE<br />
                  idx1 start offset : 0x6A9C202<br />
                  idx1 size : 0xEBA0<br />
                  <br />
                  JUNK start offset : 0x6AAADA<br />
                  JUNK size : 0x140<br />
                  <br />
                  JUNK start offset : 0x6AAAEF2<br />
                  JUNK size : 0x4211106
              </div>
          </div>
        </div>
      </>
    ) : (
      <>
        {/* 분석 후 바로 나오는 화면 */}
        <h1 className="upload-title">Result</h1>
        <div class="result-wrapper">
        <p className="result-summary">총 5개의 파일, 용량: 5.4GB</p>

        <div className="result-scroll-area">
          {['driving', 'parking', 'event', 'slack', 'deleted'].map((category) => (
            <div className="result-group" key={category}>
              <div
                className="result-group-header open"
                onClick={() => toggleGroup(category)}
              >
                <span className="result-group-toggle"></span>
                <img
                  className="result-group-icon"
                  src={categoryIcons[category]}
                  alt={`${category} icon`}
                />
                {category.charAt(0).toUpperCase() + category.slice(1)} (2)
              </div>

              <div
                className="result-file-list"
                id={category}
                style={{ display: 'block' }}
              >
                <div className="result-file-item">
                  <input className="result-checkbox" type="checkbox" />
                  <div className="result-file-info">
                    <button
                      className="text-button"
                      onClick={() => handleFileClick('2023-08-14_17-12-11_Front.mp4')}
                    >
                      2023-08-14_17-12-11_Front.mp4
                    </button>
                    <br />
                    17:12:11 ~ 17:13:08<br />
                    45.2MB ・ 슬랙비율: 12%
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', marginRight:'2rem' }}>
          <Button variant="dark" onClick={handleDownload}>다운로드</Button>
        </div>
        </div>
      </>
    )
  ) : null
}
  </Box>

    {showAlert && (
      <Alert
        icon={alertIcon}
        title="파일 형식 오류"
        description={
          <>
            선택한 파일은 E01 이미지 형식이 아닙니다<br />
            해당 도구는 .E01 형식만 지원됩니다<br />
            올바른 파일을 다시 선택해 주세요
          </>
        }
      >
        <Button variant="dark" onClick={() => setShowAlert(false)}>다시 선택</Button>
      </Alert>
    )}
    
    {showDownloadPopup && (
      <Alert
        icon={downloadIcon}
        title="다운로드 옵션"
        description={
          <>
            <div className="download-popup-wide">
              복원 결과물을 이미지(jpeg) 형식으로도 저장하시겠습니까?<br />  <br />
              <div className="download-options">
                <label><input type="radio" name="path" value="desktop" />Y</label>
                <label><input type="radio" name="path" value="downloads" /> N </label><br />   <br />   
              </div>
              <div className="path-box" style={{ display: 'flex', marginTop: '1rem', gap: '1rem' }}>
                <input
                  type="text"
                  value={selectedPath}
                  readOnly
                  className="custom-path-input"
                  style={{ flex: 1 }}
                />
                <Button variant="gray" onClick={handlePathSelect}>경로 지정</Button><br />   
              </div>
            </div>
          </>
        }
      >
        <div className="alert-buttons" style={{ marginTop: '1rem', display: 'flex', gap: '10px' }}>
          <Button variant="gray" onClick={handleDownloadCancel}>이전</Button>
          <Button variant="dark" onClick={handleDownloadConfirm}>완료</Button>
        </div>
      </Alert>
    )}
  </>
  );
}

export default Recovery;