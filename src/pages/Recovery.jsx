import React, { useRef, useState, useEffect, useMemo } from 'react';
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
import basicIcon from '../images/information_t.svg';
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
  const [saveFrames, setSaveFrames] = useState(false);
  const [selectedPath, setSelectedPath] = useState("C:\\Users\\Downloads");

  const [isRecovering, setIsRecovering] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentCount, setCurrentCount] = useState(0);
  const [totalFiles, setTotalFiles] = useState(0);

  const [results, setResults] = useState([]);
  const [openGroups, setOpenGroups] = useState({});
  function groupByCategory(list) {
    return list.reduce((acc, file) => {
      const cat = file.path.split(/[/\\]/)[1] || 'unknown'
      if (!acc[cat]) acc[cat] = []
      acc[cat].push(file)
      return acc
    }, {})
  }
  const groupedResults = useMemo(() => groupByCategory(results), [results])

  const [selectedAnalysisFile, setSelectedAnalysisFile] = useState(null); 
  const [activeTab, setActiveTab] = useState('basic');
  const [showComplete, setShowComplete] = useState(false);
  const [showDownloadAlert, setShowDownloadAlert] = useState(false);
  
  const location = useLocation();
  const initialFile = location.state?.e01File || null;
  const autoStart   = location.state?.autoStart || false;

  // 바이트 → MB 변환
  const bytesToMB = (bytes) => (bytes / 1024 / 1024).toFixed(1) + ' MB';

  // ex: "h264" → "H.264"
  const formatCodec = (codec) =>
    codec
      .toUpperCase()
      .replace(/^([HE]\d{3,4})$/, (m) => m[0] + '.' + m.slice(1));

  const analysis = useMemo(
    () => results.find(f => f.name === selectedAnalysisFile)?.analysis,
    [results, selectedAnalysisFile]
  );

  const slack_info = analysis?.slack_info ?? { slack_rate: 0 };
  const slackPercent = (slack_info.slack_rate * 100).toFixed(1);
  const validPercent = (100 - slack_info.slack_rate * 100).toFixed(1);

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

  // special override: 'shock' 인 경우 event 아이콘
  const specialCategoryMap = {
    shock: 'event',
    // 필요시 더 추가…
  };

  // 아이콘 결정 헬퍼
  const getCategoryIcon = (category) => {
    const cat = category.toLowerCase();
    // special first
    for (const [match, iconKey] of Object.entries(specialCategoryMap)) {
      if (cat.includes(match)) {
        return categoryIcons[iconKey];
      }
    }
    // prefix 기본 매핑
    const prefix = Object.keys(categoryIcons).find((k) =>
      cat.startsWith(k)
    
    );
    return prefix ? categoryIcons[prefix] : slackIcon;
  };

  // 메인에서 progress/done 이벤트 받아오기
  useEffect(() => {
    console.log('📡 onProgress useEffect mounted');
    const offProg = window.api.onProgress(({ processed, total }) => {
      console.log('📈 progress event', processed, total);
      setTotalFiles(total);
      setProgress(Math.floor((processed / total) * 100));
  });
  const offDone = window.api.onDone(() => {
    console.log('✅ recovery done event');
    setProgress(100);
    setIsRecovering(false);
    setRecoveryDone(true);
  });
  return () => { offProg(); offDone(); };
}, []);

  useEffect(() => {
    console.log('📡 onResults listener registered')
    const off = window.api.onResults(data => {
      console.log('📥 [Debug] onResults data:', data)
      if (data.error) setResultError(data.error);
      else setResults(data);
    });
    return off;
  }, []);

  useEffect(() => {
    const init = {}
    Object.keys(groupedResults).forEach(cat => { init[cat] = true })
    setOpenGroups(init)
  }, [groupedResults])

  // isRecovering가 true가 되면 startRecovery 호출
  useEffect(() => {
    if (isRecovering && selectedFile) {
      window.api.startRecovery(selectedFile.path);
    }
  }, [isRecovering, selectedFile]);

  useEffect(() => {
    if (autoStart && initialFile) {
      handleFile(initialFile);
    }
  }, [autoStart, initialFile]);

  const handleFile = file => {
    if (!file.name.toLowerCase().endsWith('.e01')) {
      setShowAlert(true);
      return;
    }
    setSelectedFile(file);
    setShowAlert(false);
    setIsRecovering(true);
    setRecoveryDone(false);
    setProgress(0);
    setTotalFiles(0);
    
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

  const handleClick = async () => {
    const filePath = await window.api.openE01File();
    if (filePath) {
      const parts = filePath.split(/[/\\]/);
      const fileName = parts[parts.length - 1];
      handleFile({ path: filePath, name: fileName });
    }
  };

  const startRecovery = () => {
    if (!selectedFile) return;
    setShowRange(false);
    setIsRecovering(true);
    setCurrentCount(0);
    setProgress(0);
    setTotalFiles(300);
  };

  const toggleGroup = (cat) =>
    setOpenGroups(prev => ({ ...prev, [cat]: !prev[cat] }))

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
  const handleDownloadConfirm =  async() => {
    const choice = saveFrames ? 'both' : 'video';

    try {
      await window.api.invoke('run-download', {
        analysisJsonPath: tmpJsonPath,
        choice,
        downloadPath: selectedPath
      });

      setShowComplete(true)
    } catch (err) {
      console.error('다운로드 실패:', err);
    } finally {
      setShowDownloadPopup(false);
    }
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
    let dir;

    if (result && !result.canceled && result.filePaths.length > 0) {
      dir = result.filePaths[0];
    } else {
      dir = await window.api.invoke('select-download-dir');
    }

    if (dir) {
      setSelectedPath(dir);
    }
  };

  // Stepbar currentStep
  let currentStep = 0;

  if (recoveryDone) {
    currentStep = 3;
  } else if (isRecovering) {
    currentStep = 1;
  } else if (recoveryDone) {
    currentStep = 2;
  } else {
    currentStep = 0;
  }

  // 뷰정의

useEffect(() => {
  if (!selectedAnalysisFile) return;

  const waitForDOMAndSetup = () => {
    const video = document.getElementById('parser-video');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const playPauseIcon = document.getElementById('playPauseIcon');
    const replayBtn = document.getElementById('replayBtn');
    const fullscreenBtn = document.getElementById('fullscreenBtn');
    const progressBar = document.getElementById('progressBar');
    const timeText = document.getElementById('timeText');

    if (!video || !playPauseBtn || !replayBtn || !fullscreenBtn || !progressBar || !timeText || !playPauseIcon) {
      console.warn('🎥 video 또는 컨트롤 요소가 아직 없음, 재시도');
      requestAnimationFrame(waitForDOMAndSetup);
      return;
    }

    // 초기 상태: 재생 중이라 가정 (filter 없음)
    playPauseIcon.style.filter = 'none';

    video.onloadedmetadata = () => {
      console.log('🎬 영상 메타데이터 로드됨');
      console.log('📏 duration:', video.duration);
      console.log('🎯 src:', video.src);

      progressBar.max = video.duration;

      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            console.log('▶️ 자동 재생 성공');
            playPauseIcon.style.filter = 'none';
          })
          .catch((err) => {
            console.warn('⚠️ 자동 재생 실패:', err);
            playPauseIcon.style.filter = 'grayscale(100%) brightness(0.8)';
          });
      }
    };

    playPauseBtn.onclick = () => {
      if (video.paused) {
        video.play();
        playPauseIcon.style.filter = 'none';
      } else {
        video.pause();
        playPauseIcon.style.filter = 'grayscale(100%) brightness(0.8)';
      }
    };

    replayBtn.onclick = () => {
      video.currentTime = 0;
      video.play();
      playPauseIcon.style.filter = 'none';
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

    function formatTime(seconds) {
      const min = Math.floor(seconds / 60).toString().padStart(2, '0');
      const sec = Math.floor(seconds % 60).toString().padStart(2, '0');
      return `${min}:${sec}`;
    }
  };

  requestAnimationFrame(waitForDOMAndSetup);
}, [selectedAnalysisFile]);


//   useEffect(() => {
//   const video = document.getElementById('parser-video');
//   const playPauseBtn = document.getElementById('playPauseBtn');
//   const playPauseIcon = document.getElementById('playPauseIcon');
//   const replayBtn = document.getElementById('replayBtn');
//   const fullscreenBtn = document.getElementById('fullscreenBtn');
//   const progressBar = document.getElementById('progressBar');
//   const timeText = document.getElementById('timeText');

//   if (!video) return;

//     video.onloadedmetadata = () => {
//     progressBar.max = video.duration;

//     // 자동재생 시도
//     const playPromise = video.play();
//     if (playPromise !== undefined) {
//       playPromise
//         .then(() => {
//           // 성공적으로 자동 재생됨
//           playPauseIcon.src = 'view_pause.svg';
//         })
//         .catch((err) => {
//           console.warn('⚠️ 자동 재생 실패:', err);
//           playPauseIcon.src = 'view_play.svg'; // 실패 시 재생 아이콘으로
//         });
//     }
//   };

//   playPauseBtn.onclick = () => {
//     if (video.paused) {
//       video.play();
//       playPauseIcon.src = 'view_pause.svg';
//     } else {
//       video.pause();
//       playPauseIcon.src = 'view_play.svg';
//     }
//   };

//   replayBtn.onclick = () => {
//     video.currentTime = 0;
//     video.play();
//   };

//   fullscreenBtn.onclick = () => {
//     if (video.requestFullscreen) video.requestFullscreen();
//   };

//   video.ontimeupdate = () => {
//     progressBar.value = video.currentTime;
//     timeText.textContent = `${formatTime(video.currentTime)} / ${formatTime(video.duration)}`;
//   };

//   progressBar.oninput = () => {
//     video.currentTime = progressBar.value;
//   };

//   video.onloadedmetadata = () => {
//     progressBar.max = video.duration;
//   };

//   function formatTime(seconds) {
//     const min = Math.floor(seconds / 60).toString().padStart(2, '0');
//     const sec = Math.floor(seconds % 60).toString().padStart(2, '0');
//     return `${min}:${sec}`;
//   }
// }, []); // 컴포넌트가 mount될 때 1번만 실행

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
                style={{ width: `${progress}%`, transition: 'width 0.6s ease' }}
              />
            </div>
            <div className="progress-bar-text">
              {progress}%
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
            {selectedAnalysisFile.toLowerCase().endsWith('.avi') && (
              <>
                <Badge label="전방" onClick={() => console.log('전방 선택')} />
                <Badge label="후방" onClick={() => console.log('후방 클릭')} />
              </>
            )}
            <button className="close-btn" onClick={handleBack}>✕</button>
          </div>
        </div>

        <div className="result-scroll-area">
          {/* 뷰위치 */}
          <div className="video-container">
            <video
              id="parser-video"
              preload="metadata"
              controls
              style={{
                width: '100%',
                maxWidth: '1200px',
                height: 'auto',
                backgroundColor: 'white',
              }}
              src={
              results.find(f => f.name === selectedAnalysisFile)?.origin_video
                ? `file:///${results
                    .find(f => f.name === selectedAnalysisFile)
                    .origin_video.replace(/\\/g, '/')}`
                : ''
            }
                         ></video>

            <div className="parser-controls">
              <button id="replayBtn">
                <img src={replayIcon} alt="Replay" />
              </button>
              <button
                id="playPauseBtn"
                style={{ background: 'none', border: 'none', cursor: 'pointer' }}
              >
                <img
                  id="playPauseIcon"
                  src={pauseIcon}
                  alt="Pause"
                  style={{
                    width: '30px',
                    transition: 'filter 0.2s',
                    filter: 'none', // 초기값: 원래색
                  }}
                />
              </button>

              <input type="range" id="progressBar" min="0" defaultValue="0" step="0.01" />
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
                <span className="parser-info-label">파일 포맷</span>
                <span className="parser-info-value">{analysis.basic.format}</span>
              </div>

              {/* 파일시스템에서 시간 파싱하지 말고 복구 시간만 표시하기 */}
              <div className="parser-info-row">
                <span className="parser-info-label">복구 시간</span>
                <span className="parser-info-value">{analysis.basic.timestamps.created}</span>
              </div>

              <div className="parser-info-row">
                <span className="parser-info-label">파일 크기</span>
                <span className="parser-info-value">
                  {bytesToMB(analysis.basic.file_size)}
                </span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">비디오 코덱</span>
                <span className="parser-info-value">
                  {formatCodec(analysis.basic.video_metadata.codec)}
                </span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">해상도</span>
                <span className="parser-info-value">
                  {analysis.basic.video_metadata.width}×{analysis.basic.video_metadata.height}
                </span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">프레임 레이트</span>
                <span className="parser-info-value">
                  {Math.round(analysis.basic.video_metadata.frame_rate)} fps
                </span>
              </div>
            </div>
          </div>

          <div className={`parser-tab-content ${activeTab === 'integrity' ? 'active' : ''}`}>
            <div className="parser-info-table">
              <div className="parser-info-row">
                <span className="parser-info-label">전체 상태</span>
                <span className="parser-info-value">
                  <img
                    src={analysis.integrity.damaged ? integrityRed : integrityGreen}
                    alt={analysis.integrity.damaged ? "손상" : "정상"}
                    className="status-icon"
                  />
                  <span className={`status-text ${analysis.integrity.damaged ? 'red' : 'green'}`}>
                    {analysis.integrity.damaged ? '손상됨' : '정상'}
                  </span>
                </span>
              </div>
              {analysis.integrity.damaged && analysis.integrity.reasons.length > 0 && (
                <div className="parser-info-row">
                  <span className="parser-info-label">손상 사유</span>
                  <span className="parser-info-value">
                    <ul className="reason-list">
                      {analysis.integrity.reasons.map((reason, idx) => (
                        <li key={idx}>{reason}</li>
                      ))}
                    </ul>
                  </span>
                </div>
              )}
            </div>
          </div>  
          
          <div className={`parser-tab-content ${activeTab === 'slack' ? 'active' : ''}`}>
            <div className="parser-info-table">
              <div className="parser-info-row">
                <span className="parser-info-label">슬랙 비율</span>
                <span className="parser-info-value">{slackPercent} %</span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">유효 데이터 비율</span>
                <span className="parser-info-value">
                  {(100 - (slack_info?.slack_rate ?? 0) * 100).toFixed(1)} %
                </span>
              </div>
              <div className="parser-info-row">
                <span className="parser-info-label">데이터 분포</span>
              </div>
              <div className="data-bar-wrapper">
                <div
                  className="data-bar-used"
                  style={{
                    width: `${(100 - (slack_info?.slack_rate ?? 0) * 100).toFixed(1)}%`
                  }}
                />
              </div>
            </div>
          </div>

          <div className={`parser-tab-content ${activeTab === 'structure' ? 'active' : ''}`}>
            <div className="parser-structure">
                <h4>{analysis.structure.type.toUpperCase()} Structure</h4>
                <pre className="structure-pre">
                  {analysis.structure.structure.join('\n')}
                </pre>
              </div>
          </div>
        </div>
      </>
    ) : (
      <>
        {/* 분석 후 바로 나오는 화면 */}
        <h1 className="upload-title">Result</h1>
        <div className="recovery-file-box">
          <span className="result-recovery-text">복원된 파일 목록</span>
        </div>
        <div className="result-wrapper">
          {/* 요약: 개수 + 전체 용량 */}
          <p className="result-summary">
            총 {results.length}개의 파일, 용량{' '}
            {bytesToMB(
              results.reduce((sum, f) => sum + f.size, 0)
            )}
          </p>

          <div className="result-scroll-area" style={{ position: 'relative' }}>
            {Object.entries(groupedResults).map(([category, files]) => (
              <div className="result-group" key={category}>
                {/* 그룹 헤더 */}
                <div
                  className={`result-group-header ${openGroups[category] ? 'open' : ''}`}
                  onClick={() => toggleGroup(category)}
                >
                  <span className="result-group-toggle"/>
                  <img
                    className="result-group-icon"
                    src={getCategoryIcon(category)}
                    alt={`${category} icon`}
                  />
                  {category} ({files.length})
                </div>

                {/* 그룹 열려있을 때만 리스트 */}
                {openGroups[category] && (
                  <div className="result-file-list">
                    {files.map((file) => {
                      const mb = bytesToMB(file.size);
                      const rawRate = file.slack_info.slack_rate;
                      const slackRatePercent =
                        rawRate <= 1
                          ? (rawRate * 100).toFixed(0)
                          : rawRate.toFixed(0);
                      
                      return (
                        <div className="result-file-item" key={file.path}>
                          <div className="result-file-info">
                            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
                                <button
                                  className="text-button"
                                  onClick={() => handleFileClick(file.name)}
                                >
                                  {file.name}
                                </button>
                                {slackRatePercent > 0 && <Badge label="슬랙 포함" />}
                              </div>
                            <br />
                            {mb} MB ・ 슬랙비율 {slackRatePercent} %
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>
  
          <div
            style={{
              position: 'absolute',  
              bottom: '1.5rem',      
              right: '4rem',       
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            <Button variant="dark" onClick={handleDownload}>
              다운로드
            </Button>
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
            <div className="download-popup-wide">
              <p>
                영상과 함께 각 프레임 이미지를 ZIP으로 다운받으시겠습니까?
              </p>
              <div className="download-options" style={{ margin: '1rem 0' }}>
                <label style={{ marginRight: '1rem' }}>
                  <input
                    type="radio"
                    name="saveFrames"
                    checked={saveFrames === true}
                    onChange={() => setSaveFrames(true)}
                  /> 예
                </label>
                <label>
                  <input
                  type="radio"
                  name="saveFrames"
                  checked={saveFrames === false}
                  onChange={() => setSaveFrames(false)}
                /> 아니요
              </label>  
            </div>
          <div
            className="path-box"
            style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}
          >
            <input
              type="text"
              value={selectedPath}
              readOnly
              className="custom-path-input"
              style={{ flex: 1 }}
            />
            <Button variant="gray" onClick={handlePathSelect}>
              경로 지정
            </Button> 
          </div>
        </div>
        }
      >
        <div 
          className="alert-buttons"
          style={{ marginTop: '1rem', display: 'flex', gap: '10px' }}
        >
          <Button variant="gray" onClick={handleDownloadCancel}>이전</Button>
          <Button variant="dark" onClick={handleDownloadConfirm}>완료</Button>
        </div>
      </Alert>
    )}
  </>
  );
}

export default Recovery;