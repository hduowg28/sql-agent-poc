import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User, Clock, Cpu, CheckCircle2 } from 'lucide-react';
import type { Message } from '../types/chat';
import { SqlDrawer } from './SqlDrawer';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`message-wrapper ${message.role} ${message.isError ? 'error' : ''}`}>
      <div className={`avatar ${message.role}`}>
        {isUser ? <User size={18} /> : <Bot size={18} />}
      </div>

      <div style={{ flex: 1, maxWidth: '100%' }}>
        <div className="message-bubble">
          {isUser ? (
            <div style={{ whiteSpace: 'pre-wrap' }}>{message.content}</div>
          ) : (
            <div className="markdown-content">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {!isUser && message.generatedSql && (
            <SqlDrawer sql={message.generatedSql} />
          )}

          {!isUser && message.executionMeta && (
            <div className="meta-info">
              <span className="meta-tag">
                <Clock size={12} />
                {message.executionMeta.execution_time_ms} ms
              </span>

              {message.executionMeta.model_name && (
                <span className="meta-tag">
                  <Cpu size={12} />
                  {message.executionMeta.model_name}
                </span>
              )}

              {message.executionMeta.sql_executed && (
                <span className="meta-tag" style={{ color: '#10b981' }}>
                  <CheckCircle2 size={12} />
                  SQL Executed
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
