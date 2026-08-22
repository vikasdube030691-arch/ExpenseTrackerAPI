import { BudgetPeriod } from './budget.model';
import { Transaction } from './transaction.model';

export interface DashboardSummary {
  readonly period_start: string;
  readonly period_end: string;
  readonly total_income: number;
  readonly total_expense: number;
  readonly net: number;
  readonly transaction_count: number;
}

export interface CategoryBreakdownItem {
  readonly category_id: string;
  readonly total: number;
  readonly count: number;
}

export interface CategoryAnalysis {
  readonly period_start: string;
  readonly period_end: string;
  readonly breakdown: readonly CategoryBreakdownItem[];
}

export type TrendGranularity = 'day' | 'month';

export interface TrendPoint {
  readonly period: string;
  readonly income: number;
  readonly expense: number;
}

export interface Trends {
  readonly granularity: TrendGranularity;
  readonly period_start: string;
  readonly period_end: string;
  readonly points: readonly TrendPoint[];
}

export interface BudgetProgressItem {
  readonly budget_id: string;
  readonly category_id: string | null;
  readonly name: string | null;
  readonly amount: number;
  readonly spent: number;
  readonly remaining: number;
  readonly period: BudgetPeriod;
}

export interface DashboardOverview {
  readonly summary: DashboardSummary;
  readonly recent_transactions: readonly Transaction[];
  readonly budget_progress: readonly BudgetProgressItem[];
}

export interface DashboardPreferences {
  readonly id: string;
  readonly user_id: string;
  readonly default_currency: string;
  readonly theme: string;
  readonly widgets: readonly string[];
  readonly settings: Readonly<Record<string, unknown>>;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface DashboardPreferencesUpdateRequest {
  readonly default_currency?: string;
  readonly theme?: string;
  readonly widgets?: readonly string[];
  readonly settings?: Readonly<Record<string, unknown>>;
}
