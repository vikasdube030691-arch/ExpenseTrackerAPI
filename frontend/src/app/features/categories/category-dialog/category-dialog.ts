import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { Category, CategoryType } from '../../../core/models/category.model';

export interface CategoryDialogData {
  readonly category: Category | null;
}

export interface CategoryDialogResult {
  readonly name: string;
  readonly type: CategoryType;
  readonly icon: string | null;
  readonly color: string | null;
}

const DEFAULT_COLOR = '#1e88e5';

@Component({
  selector: 'app-category-dialog',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule
  ],
  templateUrl: './category-dialog.html',
  styleUrl: './category-dialog.scss'
})
export class CategoryDialog {
  private readonly fb = inject(FormBuilder);
  protected readonly data = inject<CategoryDialogData>(MAT_DIALOG_DATA);
  private readonly dialogRef = inject(MatDialogRef<CategoryDialog, CategoryDialogResult>);

  protected readonly isEditMode = this.data.category !== null;

  protected readonly form = this.fb.nonNullable.group({
    name: [this.data.category?.name ?? '', [Validators.required, Validators.maxLength(100)]],
    type: this.fb.nonNullable.control<CategoryType>(this.data.category?.type ?? 'expense', Validators.required),
    icon: [this.data.category?.icon ?? ''],
    color: [this.data.category?.color ?? DEFAULT_COLOR]
  });

  submit(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const raw = this.form.getRawValue();
    this.dialogRef.close({
      name: raw.name,
      type: raw.type,
      icon: raw.icon || null,
      color: raw.color || null
    });
  }

  cancel(): void {
    this.dialogRef.close();
  }
}
