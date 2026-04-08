export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  content_type: 'text' | 'sql' | 'chart' | 'report';
  execution_metadata?: {
    sql?: string;
    confidence?: number;
    query_result?: {
      columns: string[];
      total_rows: number;
      execution_time_ms: number;
    };
    needs_clarification?: boolean;
  };
  created_at: string;
}

export interface Conversation {
  id: string;
  title?: string;
  current_agent_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  agent_id?: string;
}

export interface ChatResponse {
  message: Message;
  sql?: string;
  results?: Record<string, unknown>[];
  explanation?: string;
  needs_verification: boolean;
}
