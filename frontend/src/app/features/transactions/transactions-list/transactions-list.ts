import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatNativeDateModule } from '@angular/material/core';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { RouterLink } from '@angular/router';
import { debounceTime } from 'rxjs';

import { Category } from '../../../core/models/category.model';
import { Transaction, TRANSACTION_SORT_FIELDS, TransactionType } from '../../../core/models/transaction.model';
import { CategoriesService } from '../../../core/services/categories.service';
import { TransactionsService } from '../../../core/services/transactions.service';
import { ConfirmDialog, ConfirmDialogData } from '../../../shared/components/confirm-dialog/confirm-dialog';
import { EmptyState } from '../../../shared/components/empty-state/empty-state';
import { ErrorState } from '../../../shared/components/error-state/error-state';
import { LoadingState } from '../../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../../shared/components/page-header/page-header';
import { toApiError } from '../../../shared/utils/http-error.util';

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });
const DISPLAYED_COLUMNS = ['transaction_date', 'merchant', 'category', 'transaction_type', 'amount', 'actions'] as const;

@Component({
  selector: 'app-transactions-list',
  imports: [
    ReactiveFormsModule,
    RouterLink,
    DatePipe,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatTableModule,
    MatPaginatorModule,
    MatIconModule,
    PageHeader,
    LoadingState,
    ErrorState,
    EmptyState
  ],
  templateUrl: './transactions-list.html',
  styleUrl: './transactions-list.scss'
})
export class TransactionsList {
  private readonly fb = inject(FormBuilder);
  private readonly transactionsService = inject(TransactionsService);
  private readonly categoriesService = inject(CategoriesService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly displayedColumns = DISPLAYED_COLUMNS;
  protected readonly sortFields = TRANSACTION_SORT_FIELDS;

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly transactions = signal<readonly Transaction[]>([]);
  protected readonly total = signal(0);
  protected readonly categories = signal<readonly Category[]>([]);

  protected readonly pageIndex = signal(0);
  protected readonly pageSize = signal(20);
  protected readonly sort = signal('-transaction_date');

  protected readonly filterForm = this.fb.nonNullable.group({
    search: [''],
    transaction_type: [''],
    category_id: [''],
    start_date: this.fb.control<Date | null>(null),
    end_date: this.fb.control<Date | null>(null)
  });

  protected readonly categoryName = computed(() => {
    const map = new Map(this.categories().map((category) => [category.id, category.name]));
    return (categoryId: string): string => map.get(categoryId) ?? 'Uncategorized';
  });

  constructor() {
    this.categoriesService.list().subscribe((categories) => this.categories.set(categories));

    this.filterForm.valueChanges.pipe(debounceTime(300)).subscribe(() => {
      this.pageIndex.set(0);
      this.load();
    });

    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);

    const { search, transaction_type, category_id, start_date, end_date } = this.filterForm.getRawValue();

    this.transactionsService
      .list({
        page: this.pageIndex() + 1,
        page_size: this.pageSize(),
        sort: this.sort(),
        search: search || undefined,
        transaction_type: (transaction_type || undefined) as TransactionType | undefined,
        category_id: category_id || undefined,
        start_date: start_date ? start_date.toISOString() : undefined,
        end_date: end_date ? end_date.toISOString() : undefined
      })
      .subscribe({
        next: (response) => {
          this.transactions.set(response.items);
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

  onSortChange(value: string): void {
    this.sort.set(value);
    this.load();
  }

  formatAmount(transaction: Transaction): string {
    const amount = CURRENCY_FORMATTER.format(transaction.amount);
    return transaction.transaction_type === 'income' ? `+${amount}` : `-${amount}`;
  }

  deleteTransaction(transaction: Transaction): void {
    const data: ConfirmDialogData = {
      title: 'Delete transaction',
      message: `Delete this ${transaction.transaction_type} of ${CURRENCY_FORMATTER.format(transaction.amount)}? This cannot be undone.`,
      confirmLabel: 'Delete',
      destructive: true
    };

    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed: boolean | undefined) => {
        if (!confirmed) {
          return;
        }
        this.transactionsService.delete(transaction.id).subscribe({
          next: () => {
            this.snackBar.open('Transaction deleted', 'Dismiss', { duration: 3000 });
            this.load();
          },
          error: (error: unknown) => {
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }
}
