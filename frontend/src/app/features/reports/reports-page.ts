import { DatePipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';

import { REPORT_FORMATS, REPORT_TYPES, Report } from '../../core/models/report.model';
import { ReportsService } from '../../core/services/reports.service';
import { EmptyState } from '../../shared/components/empty-state/empty-state';
import { ErrorState } from '../../shared/components/error-state/error-state';
import { LoadingState } from '../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../shared/components/page-header/page-header';
import { toApiError } from '../../shared/utils/http-error.util';

function firstOfMonth(): Date {
  const now = new Date();
  return new Date(now.getFullYear(), now.getMonth(), 1);
}

@Component({
  selector: 'app-reports-page',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatFormFieldModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatIconModule,
    MatTableModule,
    MatPaginatorModule,
    MatProgressSpinnerModule,
    PageHeader,
    LoadingState,
    ErrorState,
    EmptyState
  ],
  templateUrl: './reports-page.html',
  styleUrl: './reports-page.scss'
})
export class ReportsPage {
  private readonly fb = inject(FormBuilder);
  private readonly reportsService = inject(ReportsService);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly reportTypes = REPORT_TYPES;
  protected readonly reportFormats = REPORT_FORMATS;
  protected readonly displayedColumns = ['report_type', 'format', 'status', 'period', 'created_at', 'actions'] as const;

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly reports = signal<readonly Report[]>([]);
  protected readonly total = signal(0);
  protected readonly pageIndex = signal(0);
  protected readonly pageSize = signal(10);

  protected readonly generating = signal(false);
  protected readonly selectedReport = signal<Report | null>(null);

  protected readonly generateForm = this.fb.nonNullable.group({
    report_type: this.fb.nonNullable.control<Report['report_type']>('monthly_summary', Validators.required),
    format: this.fb.nonNullable.control<Report['format']>('json', Validators.required),
    period_start: this.fb.control<Date | null>(firstOfMonth(), Validators.required),
    period_end: this.fb.control<Date | null>(new Date(), Validators.required)
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.reportsService.list(this.pageIndex() + 1, this.pageSize()).subscribe({
      next: (response) => {
        this.reports.set(response.items);
        this.total.set(response.total);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.errorMessage.set(toApiError(error).message);
        this.loading.set(false);
      }
    });
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.load();
  }

  generate(): void {
    if (this.generateForm.invalid || this.generating()) {
      this.generateForm.markAllAsTouched();
      return;
    }

    const raw = this.generateForm.getRawValue();
    if (!raw.period_start || !raw.period_end) {
      return;
    }

    this.generating.set(true);
    this.reportsService
      .generate({
        report_type: raw.report_type,
        format: raw.format,
        period_start: raw.period_start.toISOString(),
        period_end: raw.period_end.toISOString()
      })
      .subscribe({
        next: (report) => {
          this.generating.set(false);
          this.snackBar.open('Report generated', 'Dismiss', { duration: 3000 });
          this.selectedReport.set(report);
          this.pageIndex.set(0);
          this.load();
        },
        error: (error: unknown) => {
          this.generating.set(false);
          this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
        }
      });
  }

  viewReport(report: Report): void {
    if (report.data !== null || report.file !== null) {
      this.selectedReport.set(report);
      return;
    }
    this.reportsService.get(report.id).subscribe({
      next: (full) => this.selectedReport.set(full),
      error: (error: unknown) => this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 })
    });
  }

  closeDetail(): void {
    this.selectedReport.set(null);
  }

  formatEntries(report: Report): readonly (readonly [string, unknown])[] {
    if (!report.data) {
      return [];
    }
    return Object.entries(report.data);
  }

  formatValue(value: unknown): string {
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    if (value === null || value === undefined) {
      return '—';
    }
    if (typeof value === 'object') {
      return JSON.stringify(value);
    }
    return String(value);
  }
}
