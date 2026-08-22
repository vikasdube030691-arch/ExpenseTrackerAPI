export type AccountType = 'cash' | 'bank' | 'credit_card' | 'wallet' | 'savings' | 'other';

export interface Account {
  readonly id: string;
  readonly user_id: string;
  readonly name: string;
  readonly account_type: AccountType;
  readonly currency: string;
  readonly balance: number;
  readonly is_active: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface AccountCreateRequest {
  readonly name: string;
  readonly account_type: AccountType;
  readonly currency: string;
  readonly balance: number;
}

export interface AccountUpdateRequest {
  readonly name?: string;
  readonly account_type?: AccountType;
  readonly is_active?: boolean;
}

export const ACCOUNT_TYPES: readonly { readonly value: AccountType; readonly label: string }[] = [
  { value: 'bank', label: 'Bank' },
  { value: 'cash', label: 'Cash' },
  { value: 'credit_card', label: 'Credit Card' },
  { value: 'wallet', label: 'Wallet' },
  { value: 'savings', label: 'Savings' },
  { value: 'other', label: 'Other' }
];
