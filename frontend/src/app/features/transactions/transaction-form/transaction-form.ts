import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { forkJoin } from 'rxjs';

import { Account } from '../../../core/models/account.model';
import { Category } from '../../../core/models/category.model';
import { TransactionType } from '../../../core/models/transaction.model';
import { AccountsService } from '../../../core/services/accounts.service';
import { CategoriesService } from '../../../core/services/categories.service';
import { TransactionsService } from '../../../core/services/transactions.service';
import { ErrorState } from '../../../shared/components/error-state/error-state';
import { LoadingState } from '../../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../../shared/components/page-header/page-header';
import { toApiError } from '../../../shared/utils/http-error.util';

@Component({
  selector: 'app-transaction-form',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatChipsModule,
    MatIconModule,
    MatProgressSpinnerModule,
    PageHeader,
    LoadingState,
    ErrorState
  ],
  templateUrl: './transaction-form.html',
  styleUrl: './transaction-form.scss'
})
export class TransactionForm {
  private readonly fb = inject(FormBuilder);
  private readonly transactionsService = inject(TransactionsService);
  private readonly accountsService = inject(AccountsService);
  private readonly categoriesService = inject(CategoriesService);
  private readonly route = inject(ActivatedRoute);
  protected readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);

  private readonly transactionId = this.route.snapshot.paramMap.get('id');
  protected readonly isEditMode = this.transactionId !== null;

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly submitting = signal(false);

  protected readonly accounts = signal<readonly Account[]>([]);
  protected readonly categories = signal<readonly Category[]>([]);

  protected readonly form = this.fb.nonNullable.group({
    account_id: ['', Validators.required],
    transaction_type: this.fb.nonNullable.control<TransactionType>('expense', Validators.required),
    amount: [0, [Validators.required, Validators.min(0.01)]],
    currency: ['USD', [Validators.required, Validators.minLength(3), Validators.maxLength(3)]],
    category_id: ['', Validators.required],
    merchant: [''],
    description: [''],
    transaction_date: this.fb.control<Date | null>(new Date(), Validators.required),
    tags: this.fb.nonNullable.control<readonly string[]>([])
  });

  protected readonly filteredCategories = computed(() => {
    const type = this.form.controls.transaction_type.value;
    return this.categories().filter((category) => category.type === type);
  });

  constructor() {
    forkJoin({
      accounts: this.accountsService.list(),
      categories: this.categoriesService.list(),
      transaction: this.transactionId ? this.transactionsService.get(this.transactionId) : Promise.resolve(null)
    }).subscribe({
      next: ({ accounts, categories, transaction }) => {
        this.accounts.set(accounts);
        this.categories.set(categories);
        if (transaction) {
          this.form.patchValue({
            account_id: transaction.account_id,
            transaction_type: transaction.transaction_type,
            amount: transaction.amount,
            currency: transaction.currency,
            category_id: transaction.category_id,
            merchant: transaction.merchant ?? '',
            description: transaction.description ?? '',
            transaction_date: new Date(transaction.transaction_date),
            tags: transaction.tags
          });
        }
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.errorMessage.set(toApiError(error).message);
        this.loading.set(false);
      }
    });
  }

  addTag(rawValue: string): void {
    const value = rawValue.trim();
    if (!value) {
      return;
    }
    const current = this.form.controls.tags.value;
    if (!current.includes(value)) {
      this.form.controls.tags.setValue([...current, value]);
    }
  }

  removeTag(tag: string): void {
    this.form.controls.tags.setValue(this.form.controls.tags.value.filter((t) => t !== tag));
  }

  cancel(): void {
    this.router.navigate(['/transactions']);
  }

  submit(): void {
    if (this.form.invalid || this.submitting()) {
      this.form.markAllAsTouched();
      return;
    }

    this.submitting.set(true);
    const raw = this.form.getRawValue();
    const payload = {
      account_id: raw.account_id,
      transaction_type: raw.transaction_type,
      amount: raw.amount,
      currency: raw.currency,
      category_id: raw.category_id,
      merchant: raw.merchant || null,
      description: raw.description || null,
      transaction_date: (raw.transaction_date ?? new Date()).toISOString(),
      tags: raw.tags
    };

    const request$ = this.transactionId
      ? this.transactionsService.update(this.transactionId, payload)
      : this.transactionsService.create(payload);

    request$.subscribe({
      next: () => {
        this.snackBar.open(this.isEditMode ? 'Transaction updated' : 'Transaction created', 'Dismiss', {
          duration: 3000
        });
        this.router.navigate(['/transactions']);
      },
      error: (error: unknown) => {
        this.submitting.set(false);
        this.errorMessage.set(toApiError(error).message);
      }
    });
  }
}
