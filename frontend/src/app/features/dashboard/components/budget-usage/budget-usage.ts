import { Component, inject, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { Router } from '@angular/router';

import { BudgetProgressItem } from '../../../../core/models/dashboard.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });

@Component({
  selector: 'app-budget-usage',
  imports: [MatCardModule, MatProgressBarModule, EmptyState],
  templateUrl: './budget-usage.html',
  styleUrl: './budget-usage.scss'
})
export class BudgetUsage {
  private readonly router = inject(Router);

  readonly budgetProgress = input.required<readonly BudgetProgressItem[]>();

  protected goToBudgets(): void {
    this.router.navigate(['/budgets']);
  }

  protected ratio(item: BudgetProgressItem): number {
    if (item.amount <= 0) {
      return 0;
    }
    return item.spent / item.amount;
  }

  protected color(item: BudgetProgressItem): 'primary' | 'accent' | 'warn' {
    const ratio = this.ratio(item);
    if (ratio >= 1) {
      return 'warn';
    }
    if (ratio >= 0.85) {
      return 'accent';
    }
    return 'primary';
  }

  protected detail(item: BudgetProgressItem): string {
    return `${CURRENCY_FORMATTER.format(item.spent)} of ${CURRENCY_FORMATTER.format(item.amount)}`;
  }
}
