// Field names mirror the API's JSON exactly (snake_case) — no camelCase mapping layer,
// so what you see in a network tab is what you see in the code and templates.

export type UserRole = 'user' | 'admin';

export interface User {
  readonly id: string;
  readonly email: string;
  readonly full_name: string;
  readonly role: UserRole;
  readonly is_active: boolean;
  readonly is_verified: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}
