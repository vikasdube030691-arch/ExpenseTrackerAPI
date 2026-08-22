import { Component, computed, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { Category } from '../../../../core/models/category.model';
import { CategoryBreakdownItem } from '../../../../core/models/dashboard.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });
const BAR_COLORS = ['#3f51b5', '#00897b', '#f9a825', '#e53935', '#8e24aa', '#546e7a'];

interface CategoryBar {
  readonly categoryId: string;
  readonly name: string;
  readonly total: number;
  readonly percent: number;
  readonly color: string;
}

@Component({
  selector: 'app-category-breakdown',
  imports: [MatCardModule, EmptyState],
  templateUrl: './category-breakdown.html',
  styleUrl: './category-breakdown.scss'
})
export class CategoryBreakdown {
  readonly breakdown = input.required<readonly CategoryBreakdownItem[]>();
  readonly categories = input<readonly Category[]>([]);

  protected readonly bars = computed<readonly CategoryBar[]>(() => {
    const items = this.breakdown();
    const max = Math.max(1, ...items.map((item) => item.total));
    return items.map((item, index) => ({
      categoryId: item.category_id,
      name: this.categories().find((c) => c.id === item.category_id)?.name ?? 'Uncategorized',
      total: item.total,
      percent: (item.total / max) * 100,
      color: BAR_COLORS[index % BAR_COLORS.length] ?? '#3f51b5'
    }));
  });

  protected formatCurrency(amount: number): string {
    return CURRENCY_FORMATTER.format(amount);
  }
}
