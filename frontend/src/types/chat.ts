export interface ChatExecutionMeta {
  execution_time_ms: number;
  tokens_used?: number | null;
  model_name?: string | null;
  sql_executed: boolean;
}

export interface ChatResponse {
  success: boolean;
  answer: string;
  generated_sql?: string | null;
  execution_meta?: ChatExecutionMeta | null;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  generatedSql?: string | null;
  executionMeta?: ChatExecutionMeta | null;
  isError?: boolean;
}

export interface HealthCheckResponse {
  status: string;
  env: string;
}
