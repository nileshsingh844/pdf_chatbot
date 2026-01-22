export interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
}

export interface ChatResponse {
  type: 'content' | 'done' | 'error';
  content: string;
  timestamp?: Date;
  session_id?: string;
  citations?: Array<{
    page: number | string;
    content: string;
  }>;
}

export interface UploadStatus {
  status: 'idle' | 'uploading' | 'success' | 'error';
  filename?: string;
  progress?: number;
  pageCount?: number;
  chunkCount?: number;
  error?: string;
}

export interface UploadResponse {
  status: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  processing_time: number;
}

export interface StatsResponse {
  document_count: number;
  total_chunks: number;
  vector_store_stats: Record<string, any>;
  search_stats: Record<string, any>;
}

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  components: {
    vector_store: boolean;
    embedder: boolean;
    groq_client: boolean;
  };
  timestamp: Date;
  error?: string;
}

export interface DocumentChunk {
  id: string;
  content: string;
  metadata: {
    page_number: number;
    chunk_id: string;
    category: string;
    filename: string;
    source: string;
  };
  score: number;
}

export interface SearchResult {
  id: string;
  content: string;
  metadata: Record<string, any>;
  score: number;
  combined_score?: number;
}

export interface SettingsState {
  top_k: number;
  threshold: number;
  alpha: number;
}

export interface ThemeState {
  theme: 'light' | 'dark' | 'system';
}

export interface AppState {
  messages: Message[];
  uploadStatus: UploadStatus;
  sessionId: string | null;
  isLoading: boolean;
  settings: SettingsState;
  theme: ThemeState;
}
