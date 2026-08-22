export type ChatRole = 'user' | 'assistant' | 'system';

export interface ChatSession {
  readonly id: string;
  readonly user_id: string;
  readonly title: string;
  readonly is_archived: boolean;
  readonly last_message_at: string;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface ChatMessage {
  readonly id: string;
  readonly session_id: string;
  readonly user_id: string;
  readonly role: ChatRole;
  readonly content: string;
  readonly metadata: Readonly<Record<string, unknown>>;
  readonly created_at: string;
}

export interface ChatRequest {
  readonly session_id?: string | null;
  readonly message: string;
}

export interface ChatResponse {
  readonly session_id: string;
  readonly user_message: ChatMessage;
  readonly assistant_message: ChatMessage;
}

export interface ChatSessionDetail {
  readonly session: ChatSession;
  readonly messages: readonly ChatMessage[];
}
