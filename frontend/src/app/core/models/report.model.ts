export type ReportType = 'monthly_summary' | 'category_breakdown' | 'tax_summary' | 'custom';
export type ReportFormat = 'pdf' | 'csv' | 'json';
export type ReportStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ReportFile {
  readonly url: string;
  readonly filename: string;
  readonly size_bytes: number | null;
}

export interface Report {
  readonly id: string;
  readonly user_id: string;
  readonly report_type: ReportType;
  readonly format: ReportFormat;
  readonly status: ReportStatus;
  readonly period_start: string;
  readonly period_end: string;
  readonly file: ReportFile | null;
  readonly data: Readonly<Record<string, unknown>> | null;
  readonly error_message: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface ReportCreateRequest {
  readonly report_type: ReportType;
  readonly format: ReportFormat;
  readonly period_start: string;
  readonly period_end: string;
}

export const REPORT_TYPES: readonly { readonly value: ReportType; readonly label: string }[] = [
  { value: 'monthly_summary', label: 'Monthly Summary' },
  { value: 'category_breakdown', label: 'Category Breakdown' },
  { value: 'tax_summary', label: 'Tax Summary' },
  { value: 'custom', label: 'Custom' }
];

export const REPORT_FORMATS: readonly { readonly value: ReportFormat; readonly label: string }[] = [
  { value: 'json', label: 'JSON (view in-app)' },
  { value: 'pdf', label: 'PDF' },
  { value: 'csv', label: 'CSV' }
];
