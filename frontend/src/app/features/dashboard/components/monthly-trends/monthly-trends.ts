import { Component, computed, input, output } from '@angular/core';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';

import { TrendGranularity, Trends } from '../../../../core/models/dashboard.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });

interface TrendBar {
  readonly period: string;
  readonly incomePercent: number;
  readonly expensePercent: number;
  readonly incomeLabel: string;
  readonly expenseLabel: string;
}

@Component({
  selector: 'app-monthly-trends',
  imports: [MatCardModule, MatButtonToggleModule, EmptyState],
  templateUrl: './monthly-trends.html',
  styleUrl: './monthly-trends.scss'
})
export class MonthlyTrends {
  readonly trends = input.required<Trends>();
  readonly granularityChange = output<TrendGranularity>();

  protected readonly bars = computed<readonly TrendBar[]>(() => {
    const points = this.trends().points;
    const max = Math.max(1, ...points.flatMap((point) => [point.income, point.expense]));
    return points.map((point) => ({
      period: point.period,
      incomePercent: (point.income / max) * 100,
      expensePercent: (point.expense / max) * 100,
      incomeLabel: CURRENCY_FORMATTER.format(point.income),
      expenseLabel: CURRENCY_FORMATTER.format(point.expense)
    }));
  });

  protected onGranularityChange(value: TrendGranularity): void {
    this.granularityChange.emit(value);
  }
}
