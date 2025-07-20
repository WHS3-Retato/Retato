import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Home from './pages/Home';
import Recovery from './pages/Recovery';
import Setting from './pages/Settings';
import Information from './pages/Information';
import './styles/App.css'; 

function App() {
  return (
    <div className="container">
      <Sidebar />
      <main className="app_main">
        <Routes>
          <Route path="/" element={<Home />} />   
          <Route path="/fileUpload" element={<Recovery />} />
          <Route path="/setting" element={<Setting />} />
          <Route path="/information" element={<Information />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
