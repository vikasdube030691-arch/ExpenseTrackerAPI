import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Category, CategoryType } from '../../core/models/category.model';
import { CategoriesService } from '../../core/services/categories.service';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/components/confirm-dialog/confirm-dialog';
import { EmptyState } from '../../shared/components/empty-state/empty-state';
import { ErrorState } from '../../shared/components/error-state/error-state';
import { LoadingState } from '../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../shared/components/page-header/page-header';
import { toApiError } from '../../shared/utils/http-error.util';
import { CategoryDialog, CategoryDialogData, CategoryDialogResult } from './category-dialog/category-dialog';

type CategoryFilter = 'all' | CategoryType;

@Component({
  selector: 'app-categories-page',
  imports: [
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatIconModule,
    PageHeader,
    LoadingState,
    ErrorState,
    EmptyState
  ],
  templateUrl: './categories-page.html',
  styleUrl: './categories-page.scss'
})
export class CategoriesPage {
  private readonly categoriesService = inject(CategoriesService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly categories = signal<readonly Category[]>([]);
  protected readonly filter = signal<CategoryFilter>('all');

  protected readonly filteredCategories = computed(() => {
    const filter = this.filter();
    const categories = this.categories();
    if (filter === 'all') {
      return categories;
    }
    return categories.filter((category) => category.type === filter);
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.categoriesService.list().subscribe({
      next: (categories) => {
        this.categories.set(categories);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.errorMessage.set(toApiError(error).message);
        this.loading.set(false);
      }
    });
  }

  onFilterChange(value: CategoryFilter): void {
    this.filter.set(value);
  }

  openCreateDialog(): void {
    this.openDialog(null);
  }

  openEditDialog(category: Category): void {
    this.openDialog(category);
  }

  private openDialog(category: Category | null): void {
    const data: CategoryDialogData = { category };
    this.dialog
      .open(CategoryDialog, { data, width: '420px' })
      .afterClosed()
      .subscribe((result: CategoryDialogResult | undefined) => {
        if (!result) {
          return;
        }
        const request$ = category
          ? this.categoriesService.update(category.id, {
              name: result.name,
              icon: result.icon,
              color: result.color
            })
          : this.categoriesService.create({
              name: result.name,
              type: result.type,
              icon: result.icon,
              color: result.color
            });

        request$.subscribe({
          next: () => {
            this.snackBar.open(category ? 'Category updated' : 'Category created', 'Dismiss', { duration: 3000 });
            this.load();
          },
          error: (error: unknown) => {
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }

  deleteCategory(category: Category): void {
    const data: ConfirmDialogData = {
      title: 'Delete category',
      message: `Delete "${category.name}"? Transactions already assigned to it keep their reference, but you won't be able to pick it for new ones.`,
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
        this.categoriesService.delete(category.id).subscribe({
          next: () => {
            this.snackBar.open('Category deleted', 'Dismiss', { duration: 3000 });
            this.load();
          },
          error: (error: unknown) => {
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }
}
