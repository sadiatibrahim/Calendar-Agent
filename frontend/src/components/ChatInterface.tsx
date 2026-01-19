/**
 * ChatInterface component - Main chat interface with messages and input
 */

import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../types';
import { ApiService } from '../services/api';
import { ChatMessage } from './ChatMessage';
import { FileUpload } from './FileUpload';
import { TypingIndicator } from './TypingIndicator';
import './ChatInterface.css';

export const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputText]);

  const handleSendMessage = async () => {
    // Validate input
    if (!inputText.trim() && !selectedFile) {
      setError('Please enter a message or attach a file');
      return;
    }

    setError(null);

    // Create user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim() || '(File attached)',
      timestamp: new Date(),
      file: selectedFile
        ? {
            name: selectedFile.name,
            type: selectedFile.type,
          }
        : undefined,
    };

    // Add user message to chat
    setMessages((prev) => [...prev, userMessage]);

    // Clear input
    const messageText = inputText;
    const fileToSend = selectedFile;
    setInputText('');
    setSelectedFile(null);
    setIsLoading(true);

    try {
      // Send to backend
      const response = await ApiService.sendMessage({
        message: messageText || undefined,
        file: fileToSend || undefined,
      });

      // Create assistant message
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.message,
        timestamp: new Date(),
        error: response.error || undefined,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      // Create error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request.',
        timestamp: new Date(),
        error: err instanceof Error ? err.message : 'Unknown error',
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setInputText('');
    setSelectedFile(null);
    setError(null);
    ApiService.resetSession();
  };

  return (
    <div className="chat-interface">
      {/* Header */}
      <div className="chat-header">
        <div className="header-content">
          <div className="header-title">
            <span className="calendar-icon">📅</span>
            <h1>Calendar Assistant</h1>
          </div>
          <button onClick={handleNewChat} className="new-chat-btn" title="New chat">
            🔄
          </button>
        </div>
      </div>

      {/* Messages area */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <div className="welcome-icon">👋</div>
            <h2>Welcome to Calendar Assistant!</h2>
            <p>I can help you manage your calendar and tasks.</p>
            <div className="welcome-features">
              <div className="feature">✓ Add events and reminders</div>
              <div className="feature">✓ Create tasks with deadlines</div>
              <div className="feature">✓ Upload images or PDFs</div>
              <div className="feature">✓ Paste screenshots</div>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}

        {isLoading && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="chat-input-container">
        {error && (
          <div className="input-error">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        <FileUpload onFileSelect={setSelectedFile} selectedFile={selectedFile} />

        <div className="chat-input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-input"
            placeholder="Type your message... (Shift+Enter for new line)"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            rows={1}
          />
          <button
            className="send-btn"
            onClick={handleSendMessage}
            disabled={isLoading || (!inputText.trim() && !selectedFile)}
            aria-label="Send message"
          >
            {isLoading ? '⏳' : '🚀'}
          </button>
        </div>
      </div>
    </div>
  );
};
