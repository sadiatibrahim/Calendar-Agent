/**
 * API service for communicating with the Calendar Assistant backend
 */

import { ChatRequest, ChatResponse, ApiError } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiService {
  private static userId: string | null = null;

  /**
   * Send a chat message to the backend
   */
  static async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    try {
      const formData = new FormData();

      if (request.message) {
        formData.append('message', request.message);
      }

      if (request.file) {
        formData.append('file', request.file);
      }

      if (this.userId) {
        formData.append('user_id', this.userId);
      }

      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData: ApiError = await response.json().catch(() => ({
          message: `HTTP error! status: ${response.status}`,
        }));
        throw new Error(errorData.detail || errorData.message || 'Failed to send message');
      }

      const data: ChatResponse = await response.json();

      // Store user_id for session continuity
      if (data.user_id) {
        this.userId = data.user_id;
      }

      return data;
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  /**
   * Check backend health
   */
  static async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  /**
   * Reset session (clear user_id)
   */
  static resetSession(): void {
    this.userId = null;
  }

  /**
   * Get current user_id
   */
  static getUserId(): string | null {
    return this.userId;
  }
}
