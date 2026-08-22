import { Component, computed, input } from '@angular/core';

import { DashboardSummary } from '../../../../core/models/dashboard.model';
import { StatCard } from '../../../../shared/components/stat-card/stat-card';

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });

@Component({
  selector: 'app-summary-cards',
  imports: [StatCard],
  templateUrl: './summary-cards.html',
  styleUrl: './summary-cards.scss'
})
export class SummaryCards {
  readonly summary = input.required<DashboardSummary>();

  protected readonly incomeValue = computed(() => CURRENCY_FORMATTER.format(this.summary().total_income));
  protected readonly expenseValue = computed(() => CURRENCY_FORMATTER.format(this.summary().total_expense));
  protected readonly savingsValue = computed(() => CURRENCY_FORMATTER.format(this.summary().net));
  protected readonly savingsPercent = computed(() => {
    const income = this.summary().total_income;
    if (income <= 0) {
      return 0;
    }
    return Math.round((this.summary().net / income) * 100);
  });
  protected readonly savingsTone = computed(() => (this.summary().net >= 0 ? 'positive' : 'negative'));
}
