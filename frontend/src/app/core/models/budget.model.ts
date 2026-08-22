export type BudgetPeriod = 'weekly' | 'monthly' | 'yearly' | 'custom';

export interface Budget {
  readonly id: string;
  readonly user_id: string;
  readonly category_id: string | null;
  readonly name: string | null;
  readonly amount: number;
  readonly currency: string;
  readonly period: BudgetPeriod;
  readonly start_date: string;
  readonly end_date: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface BudgetCreateRequest {
  readonly category_id?: string | null;
  readonly name?: string | null;
  readonly amount: number;
  readonly currency: string;
  readonly period: BudgetPeriod;
  readonly start_date: string;
  readonly end_date?: string | null;
}

export interface BudgetUpdateRequest {
  readonly name?: string | null;
  readonly amount?: number;
  readonly end_date?: string | null;
}

export const BUDGET_PERIODS: readonly { readonly value: BudgetPeriod; readonly label: string }[] = [
  { value: 'weekly', label: 'Weekly' },
  { value: 'monthly', label: 'Monthly' },
  { value: 'yearly', label: 'Yearly' },
  { value: 'custom', label: 'Custom' }
];
