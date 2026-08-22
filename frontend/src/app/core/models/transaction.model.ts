export type TransactionType = 'income' | 'expense';

export interface ReceiptReference {
  readonly url: string;
  readonly filename: string | null;
  readonly content_type: string | null;
  readonly size_bytes: number | null;
}

export interface Transaction {
  readonly id: string;
  readonly user_id: string;
  readonly account_id: string;
  readonly transaction_type: TransactionType;
  readonly amount: number;
  readonly currency: string;
  readonly category_id: string;
  readonly merchant: string | null;
  readonly description: string | null;
  readonly transaction_date: string;
  readonly tags: readonly string[];
  readonly receipt: ReceiptReference | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface TransactionCreateRequest {
  readonly account_id: string;
  readonly transaction_type: TransactionType;
  readonly amount: number;
  readonly currency: string;
  readonly category_id: string;
  readonly merchant?: string | null;
  readonly description?: string | null;
  readonly transaction_date: string;
  readonly tags: readonly string[];
}

export type TransactionUpdateRequest = Partial<TransactionCreateRequest>;

export interface TransactionFilter {
  readonly transaction_type?: TransactionType;
  readonly account_id?: string;
  readonly category_id?: string;
  readonly start_date?: string;
  readonly end_date?: string;
  readonly min_amount?: number;
  readonly max_amount?: number;
  readonly search?: string;
}

export const TRANSACTION_SORT_FIELDS: readonly { readonly value: string; readonly label: string }[] = [
  { value: '-transaction_date', label: 'Date (newest first)' },
  { value: 'transaction_date', label: 'Date (oldest first)' },
  { value: '-amount', label: 'Amount (high to low)' },
  { value: 'amount', label: 'Amount (low to high)' }
];
