import { DecimalPipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { forkJoin } from 'rxjs';

import { Budget } from '../../core/models/budget.model';
import { Category } from '../../core/models/category.model';
import { BudgetProgressItem } from '../../core/models/dashboard.model';
import { BudgetsService } from '../../core/services/budgets.service';
import { CategoriesService } from '../../core/services/categories.service';
import { DashboardService } from '../../core/services/dashboard.service';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/components/confirm-dialog/confirm-dialog';
import { EmptyState } from '../../shared/components/empty-state/empty-state';
import { ErrorState } from '../../shared/components/error-state/error-state';
import { LoadingState } from '../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../shared/components/page-header/page-header';
import { toApiError } from '../../shared/utils/http-error.util';
import { BudgetDialog, BudgetDialogData, BudgetDialogResult } from './budget-dialog/budget-dialog';

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });

@Component({
  selector: 'app-budgets-page',
  imports: [
    DecimalPipe,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    PageHeader,
    LoadingState,
    ErrorState,
    EmptyState
  ],
  templateUrl: './budgets-page.html',
  styleUrl: './budgets-page.scss'
})
export class BudgetsPage {
  private readonly budgetsService = inject(BudgetsService);
  private readonly categoriesService = inject(CategoriesService);
  private readonly dashboardService = inject(DashboardService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly budgets = signal<readonly Budget[]>([]);
  protected readonly categories = signal<readonly Category[]>([]);
  private readonly progressItems = signal<readonly BudgetProgressItem[]>([]);

  protected readonly progressByBudgetId = computed(() => {
    return new Map(this.progressItems().map((item) => [item.budget_id, item]));
  });

  protected readonly categoryName = computed(() => {
    const map = new Map(this.categories().map((category) => [category.id, category.name]));
    return (categoryId: string | null): string => (categoryId ? (map.get(categoryId) ?? 'Uncategorized') : 'Overall');
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);

    forkJoin({
      budgets: this.budgetsService.list(),
      categories: this.categoriesService.list(),
      overview: this.dashboardService.getOverview()
    }).subscribe({
      next: ({ budgets, categories, overview }) => {
        this.budgets.set(budgets);
        this.categories.set(categories);
        this.progressItems.set(overview.budget_progress);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.errorMessage.set(toApiError(error).message);
        this.loading.set(false);
      }
    });
  }

  spent(budget: Budget): number {
    return this.progressByBudgetId().get(budget.id)?.spent ?? 0;
  }

  ratio(budget: Budget): number {
    if (budget.amount <= 0) {
      return 0;
    }
    return this.spent(budget) / budget.amount;
  }

  progressColor(budget: Budget): 'primary' | 'accent' | 'warn' {
    const ratio = this.ratio(budget);
    if (ratio >= 1) {
      return 'warn';
    }
    if (ratio >= 0.85) {
      return 'accent';
    }
    return 'primary';
  }

  formatAmount(amount: number): string {
    return CURRENCY_FORMATTER.format(amount);
  }

  openCreateDialog(): void {
    this.openDialog(null);
  }

  openEditDialog(budget: Budget): void {
    this.openDialog(budget);
  }

  private openDialog(budget: Budget | null): void {
    const data: BudgetDialogData = { budget, categories: this.categories() };
    this.dialog
      .open(BudgetDialog, { data, width: '480px' })
      .afterClosed()
      .subscribe((result: BudgetDialogResult | undefined) => {
        if (!result) {
          return;
        }

        const request$ = budget
          ? this.budgetsService.update(budget.id, {
              name: result.name,
              amount: result.amount,
              end_date: result.end_date ? result.end_date.toISOString() : null
            })
          : this.budgetsService.create({
              category_id: result.category_id,
              name: result.name,
              amount: result.amount,
              currency: result.currency,
              period: result.period,
              start_date: result.start_date.toISOString(),
              end_date: result.end_date ? result.end_date.toISOString() : null
            });

        request$.subscribe({
          next: () => {
            this.snackBar.open(budget ? 'Budget updated' : 'Budget created', 'Dismiss', { duration: 3000 });
            this.load();
          },
          error: (error: unknown) => {
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }

  deleteBudget(budget: Budget): void {
    const data: ConfirmDialogData = {
      title: 'Delete budget',
      message: `Delete the "${budget.name ?? this.categoryName()(budget.category_id)}" budget? This cannot be undone.`,
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
        this.budgetsService.delete(budget.id).subscribe({
          next: () => {
            this.snackBar.open('Budget deleted', 'Dismiss', { duration: 3000 });
            this.load();
          },
          error: (error: unknown) => {
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }
}
