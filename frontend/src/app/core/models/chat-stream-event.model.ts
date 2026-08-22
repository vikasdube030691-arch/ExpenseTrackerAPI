export type ChatStreamEvent =
  | { readonly type: 'session'; readonly session_id: string }
  | { readonly type: 'delta'; readonly delta: string }
  | { readonly type: 'done' };
