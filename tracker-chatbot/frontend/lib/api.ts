import { ChatRequest, ChatResponse, UploadResponse, StatsResponse, HealthResponse } from './types';

const API_URL = typeof window !== 'undefined' 
  ? (window as any).__NEXT_PUBLIC_API_URL || ''
  : process.env.NEXT_PUBLIC_API_URL || '';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    const response = await fetch(url, {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  // Upload PDF
  async uploadPDF(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/api/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload Error: ${response.status} - ${errorText}`);
    }

    return response.json();
  }

  // Simple chat response (non-streaming)
  async streamChat(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat Error: ${response.status} - ${errorText}`);
    }

    const data = await response.json();
    
    // Convert backend JSON response to ChatResponse format
    return {
      type: 'done',
      content: data.answer,
      session_id: data.session_id,
      citations: data.citations || []
    };
  }

  // Get system stats
  async getStats(): Promise<StatsResponse> {
    return this.request<StatsResponse>('/api/stats');
  }

  // Export conversation
  async exportConversation(sessionId: string): Promise<Blob> {
    const formData = new FormData();
    formData.append('session_id', sessionId);

    const response = await fetch(`${this.baseUrl}/api/export`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Export Error: ${response.status} - ${errorText}`);
    }

    return response.blob();
  }

  // Reset session or clear all data
  async resetSession(sessionId?: string): Promise<{ message: string }> {
    const url = sessionId ? `/api/reset?session_id=${sessionId}` : '/api/reset';
    
    return this.request<{ message: string }>(url, {
      method: 'DELETE',
    });
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health');
  }

  // Test connection
  async testConnection(): Promise<boolean> {
    try {
      await this.healthCheck();
      return true;
    } catch (error) {
      console.error('Connection test failed:', error);
      return false;
    }
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export utility functions
export const uploadPDF = (file: File) => apiClient.uploadPDF(file);
export const streamChat = (request: ChatRequest) => apiClient.streamChat(request);
export const getStats = () => apiClient.getStats();
export const exportConversation = (sessionId: string) => apiClient.exportConversation(sessionId);
export const resetSession = (sessionId?: string) => apiClient.resetSession(sessionId);
export const healthCheck = () => apiClient.healthCheck();
export const testConnection = () => apiClient.testConnection();
