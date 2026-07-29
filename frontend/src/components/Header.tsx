import React from 'react';
import { Database, RefreshCw } from 'lucide-react';

interface HeaderProps {
  isOnline: boolean;
  onClearChat: () => void;
  hasMessages: boolean;
}

export const Header: React.FC<HeaderProps> = ({ isOnline, onClearChat, hasMessages }) => {
  const buttonStyle: React.CSSProperties = {
    padding: '0.35rem 0.65rem',
    fontSize: '0.8rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.35rem'
  };

  return (
    <header className="header glass-card">
      <div className="brand">
        <div className="brand-logo">
          <Database size={20} />
        </div>
        <div>
          <div className="brand-title">SQL Agent POC</div>
          <div className="brand-subtitle">FastAPI • LangChain • Gemini 3.1 Flash</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div className="status-badge">
          <span className={`status-dot ${isOnline ? 'online' : 'offline'}`}></span>
          <span>{isOnline ? 'Backend Online' : 'Offline'}</span>
        </div>

        {hasMessages && (
          <button
            onClick={onClearChat}
            className="prompt-card"
            style={buttonStyle}
            title="Xóa hội thoại"
          >
            <RefreshCw size={14} />
            <span>Làm mới</span>
          </button>
        )}
      </div>
    </header>
  );
};
