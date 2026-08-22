import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';

import { ACCOUNT_TYPES, Account, AccountType } from '../../../core/models/account.model';

export interface AccountDialogData {
  readonly account: Account | null;
}

export interface AccountDialogResult {
  readonly name: string;
  readonly account_type: AccountType;
  readonly currency: string;
  readonly balance: number;
  readonly is_active: boolean;
}

@Component({
  selector: 'app-account-dialog',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatSlideToggleModule,
    MatIconModule
  ],
  templateUrl: './account-dialog.html',
  styleUrl: './account-dialog.scss'
})
export class AccountDialog {
  private readonly fb = inject(FormBuilder);
  protected readonly data = inject<AccountDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<AccountDialog, AccountDialogResult>);

  protected readonly isEditMode = this.data.account !== null;
  protected readonly accountTypes = ACCOUNT_TYPES;

  protected readonly form = this.fb.group({
    name: this.fb.nonNullable.control(this.data.account?.name ?? '', [Validators.required, Validators.maxLength(255)]),
    account_type: this.fb.nonNullable.control<AccountType>(this.data.account?.account_type ?? 'bank', Validators.required),
    currency: this.fb.nonNullable.control(this.data.account?.currency ?? 'USD', [
      Validators.required,
      Validators.minLength(3),
      Validators.maxLength(3)
    ]),
    balance: this.fb.nonNullable.control(this.data.account?.balance ?? 0, Validators.required),
    is_active: this.fb.nonNullable.control(this.data.account?.is_active ?? true)
  });

  constructor() {
    if (this.isEditMode) {
      this.form.controls.currency.disable();
      this.form.controls.balance.disable();
    }
  }

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    this.dialogRef.close({
      name: raw.name,
      account_type: raw.account_type,
      currency: raw.currency.toUpperCase(),
      balance: raw.balance,
      is_active: raw.is_active
    });
  }

  cancel(): void {
    this.dialogRef.close();
  }
}
