import React from 'react';
import '../styles/Information.css';


const Information = () => {
  return (
    <div className="info_page">
      <h1 className="info_title">Information</h1>
      {/* 소프트웨어 정보 */}
      <div className="info_box">
        <h1>소프트웨어 정보</h1>
        <table className="info_table">
          <tbody>
            <tr>
              <th>제품명</th>
              <td>RETATO</td>
            </tr>
            <tr>
              <th>버전</th>
              <td>v1.0.0</td>
            </tr>
            <tr>
              <th>출시일</th>
              <td>2024년 7월 20일</td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 개발자 정보 */}
      <div className="info_box">
        <h1>개발자 정보</h1>
        <table className="info_table">
          <tbody>
            <tr>
              <th>팀</th>
              <td>복원하는 감자입니다만...?</td>
            </tr>
            <tr>
              <th>소속</th>
              <td>화이트햇 스쿨 3기</td>
            </tr>
            <tr>
              <th>GitHub:</th>
              <td><a href="https://github.com/WHS3-Retato/Retato" target="_blank" rel="noreferrer">https://github.com/WHS3-Retato/Retato</a></td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* 기술 스택 */}
      <div className="info_box">
        <h1>기술 스택</h1>
        <div className="tech_stack">
          <div><strong>프론트엔드</strong> <span className="tag">Electron</span> <span className="tag">React</span> <span className="tag">JavaScript</span></div>
          <div><strong>백엔드</strong> <span className="tag">Python</span> <span className="tag">Node.js</span></div>
          <div><strong>기타 도구</strong> <span className="tag">FFmpeg</span></div>
        </div>
      </div>
    </div>
  );
};

export default Information;
