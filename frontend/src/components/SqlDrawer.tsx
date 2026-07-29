import React, { useState } from 'react';
import { Copy, Check, ChevronDown, ChevronRight, Terminal } from 'lucide-react';

interface SqlDrawerProps {
  sql: string;
}

export const SqlDrawer: React.FC<SqlDrawerProps> = ({ sql }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const buttonStyle: React.CSSProperties = {
    background: 'transparent',
    border: 'none',
    color: copied ? '#10b981' : '#9ca3af',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
    fontSize: '0.75rem'
  };

  return (
    <div className="sql-accordion">
      <div className="sql-header" onClick={() => setIsOpen(!isOpen)}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          <Terminal size={14} />
          <span>Xem SQL Query đã thực thi</span>
        </div>
        <button onClick={handleCopy} style={buttonStyle}>
          {copied ? <Check size={14} /> : <Copy size={14} />}
          <span>{copied ? 'Đã chép' : 'Copy'}</span>
        </button>
      </div>

      {isOpen && (
        <pre className="sql-code-block">
          <code>{sql}</code>
        </pre>
      )}
    </div>
  );
};
