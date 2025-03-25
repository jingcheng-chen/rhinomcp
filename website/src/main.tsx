import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';
// eslint-disable-next-line react-refresh/only-export-components
function Overlay() {
  return (
    <div style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none', width: '100%', height: '100%' }}>
      <a href='https://pmnd.rs/' style={{ position: 'absolute', bottom: 40, left: 90, fontSize: '13px' }}>
        pmnd.rs
        <br />
        dev collective
      </a>
      <div style={{ position: 'absolute', top: 40, left: 40, fontSize: '13px' }}>😄 —</div>
      <div style={{ position: 'absolute', bottom: 40, right: 40, fontSize: '13px' }}>30/10/2022</div>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
    <Overlay />
    <img src={'https://www.adaptivewfs.com/wp-content/uploads/2020/07/logo-placeholder-image.png'} style={{ position: 'absolute', bottom: 40, left: 40, width: 30 }} />
  </StrictMode>
);
