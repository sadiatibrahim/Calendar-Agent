/**
 * Type definitions for the Calendar Assistant frontend
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  error?: string;
  file?: {
    name: string;
    type: string;
    url?: string;
  };
}

export interface ChatResponse {
  message: string;
  user_id?: string | null;
  error?: string | null;
}

export interface ChatRequest {
  message?: string;
  file?: File;
  user_id?: string;
}

export interface ApiError {
  detail?: string;
  message?: string;
}
