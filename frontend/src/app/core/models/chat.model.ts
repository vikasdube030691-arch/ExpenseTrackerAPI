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
  /** Generative UI blocks the backend already validated (see
   * `app/schemas/generative_ui.py`) — still typed `unknown` here because the
   * renderer (`GenerativeUiRenderer` / `ui-component-validator.ts`) treats
   * every value on this wire as untrusted regardless of that guarantee. */
  readonly ui_blocks: readonly unknown[];
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
