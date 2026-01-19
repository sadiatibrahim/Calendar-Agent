/**
 * ChatMessage component - Displays individual messages in the chat
 */

import React from 'react';
import { Message } from '../types';
import './ChatMessage.css';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`message ${isUser ? 'message-user' : 'message-assistant'}`}>
      <div className="message-content">
        {message.file && (
          <div className="message-file">
            <div className="file-badge">
              <span className="file-icon">📎</span>
              <span className="file-name">{message.file.name}</span>
            </div>
          </div>
        )}
        <div className="message-text">
          {message.content}
        </div>
        {message.error && (
          <div className="message-error">
            <span className="error-icon">⚠️</span>
            <span className="error-text">{message.error}</span>
          </div>
        )}
      </div>
      <div className="message-timestamp">
        {message.timestamp.toLocaleTimeString([], { 
          hour: '2-digit', 
          minute: '2-digit' 
        })}
      </div>
    </div>
  );
};
