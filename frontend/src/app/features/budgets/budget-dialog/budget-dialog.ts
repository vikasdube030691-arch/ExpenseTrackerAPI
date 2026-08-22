import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { BUDGET_PERIODS, Budget, BudgetPeriod } from '../../../core/models/budget.model';
import { Category } from '../../../core/models/category.model';

export interface BudgetDialogData {
  readonly budget: Budget | null;
  readonly categories: readonly Category[];
}

export interface BudgetDialogResult {
  readonly category_id: string | null;
  readonly name: string | null;
  readonly amount: number;
  readonly currency: string;
  readonly period: BudgetPeriod;
  readonly start_date: Date;
  readonly end_date: Date | null;
}

@Component({
  selector: 'app-budget-dialog',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatIconModule
  ],
  templateUrl: './budget-dialog.html',
  styleUrl: './budget-dialog.scss'
})
export class BudgetDialog {
  private readonly fb = inject(FormBuilder);
  protected readonly data = inject<BudgetDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<BudgetDialog, BudgetDialogResult>);

  protected readonly isEditMode = this.data.budget !== null;
  protected readonly periods = BUDGET_PERIODS;
  protected readonly expenseCategories = this.data.categories.filter((c) => c.type === 'expense');

  protected readonly form = this.fb.group({
    category_id: [this.data.budget?.category_id ?? ''],
    name: [this.data.budget?.name ?? ''],
    amount: this.fb.nonNullable.control(this.data.budget?.amount ?? 0, [Validators.required, Validators.min(0.01)]),
    currency: this.fb.nonNullable.control(this.data.budget?.currency ?? 'USD', [
      Validators.required,
      Validators.minLength(3),
      Validators.maxLength(3)
    ]),
    period: this.fb.nonNullable.control<BudgetPeriod>(this.data.budget?.period ?? 'monthly', Validators.required),
    start_date: this.fb.control<Date | null>(
      this.data.budget ? new Date(this.data.budget.start_date) : new Date(),
      Validators.required
    ),
    end_date: this.fb.control<Date | null>(this.data.budget?.end_date ? new Date(this.data.budget.end_date) : null)
  });

  constructor() {
    if (this.isEditMode) {
      this.form.controls.category_id.disable();
      this.form.controls.period.disable();
      this.form.controls.start_date.disable();
      this.form.controls.currency.disable();
    }
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    this.dialogRef.close({
      category_id: raw.category_id || null,
      name: raw.name || null,
      amount: raw.amount,
      currency: raw.currency.toUpperCase(),
      period: raw.period,
      start_date: raw.start_date ?? new Date(),
      end_date: raw.end_date
    });
  }

  cancel(): void {
    this.dialogRef.close();
  }
}
