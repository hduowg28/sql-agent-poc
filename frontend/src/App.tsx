import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { SuggestedPrompts } from './components/SuggestedPrompts';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import type { Message } from './types/chat';
import { askQuestion, checkBackendHealth } from './services/api';
import { Bot } from 'lucide-react';

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [sessionId] = useState<string>(() => `session_${Date.now()}`);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Periodic Backend Health Check
  useEffect(() => {
    const verifyHealth = async () => {
      try {
        await checkBackendHealth();
        setIsOnline(true);
      } catch (err) {
        setIsOnline(false);
      }
    };

    verifyHealth();
    const interval = setInterval(verifyHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Auto scroll to bottom when messages update or loading state changes
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSendMessage = async (questionText: string) => {
    const userMessage: Message = {
      id: `msg_user_${Date.now()}`,
      role: 'user',
      content: questionText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await askQuestion(questionText, sessionId);

      const assistantMessage: Message = {
        id: `msg_assistant_${Date.now()}`,
        role: 'assistant',
        content: response.answer || 'Không nhận được câu trả lời từ SQL Agent.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        generatedSql: response.generated_sql,
        executionMeta: response.execution_meta,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMessage: Message = {
        id: `msg_error_${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Lỗi**: ${err.message || 'Không thể kết nối đến SQL Agent Backend.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  return (
    <div className="app-container">
      <Header
        isOnline={isOnline}
        onClearChat={handleClearChat}
        hasMessages={messages.length > 0}
      />

      <div className="chat-container">
        {messages.length === 0 ? (
          <SuggestedPrompts onSelectPrompt={handleSendMessage} />
        ) : (
          messages.map((msg) => <ChatMessage key={msg.id} message={msg} />)
        )}

        {isLoading && (
          <div className="message-wrapper assistant">
            <div className="avatar assistant">
              <Bot size={18} />
            </div>
            <div className="message-bubble" style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)' }}>
              <div className="typing-indicator">
                <span style={{ fontSize: '0.85rem', color: '#9ca3af', marginRight: '0.4rem' }}>
                  SQL Agent đang suy nghĩ & sinh truy vấn...
                </span>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
                <div className="typing-dot"></div>
              </div>
            </div>
          </div>
        )}

        <div ref={chatBottomRef} />
      </div>

      <ChatInput
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
        disabled={!isOnline}
      />
    </div>
  );
};

export default App;
