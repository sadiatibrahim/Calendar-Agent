/**
 * TypingIndicator component - Shows when assistant is typing
 */

import React from 'react';
import './TypingIndicator.css';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="typing-indicator">
      <div className="typing-bubble">
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
        <div className="typing-dot"></div>
      </div>
    </div>
  );
};
