import { DatePipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { RouterLink } from '@angular/router';

import { Category } from '../../../../core/models/category.model';
import { Transaction } from '../../../../core/models/transaction.model';
import { EmptyState } from '../../../../shared/components/empty-state/empty-state';

const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });

@Component({
  selector: 'app-recent-transactions',
  imports: [MatCardModule, MatListModule, MatIconModule, RouterLink, EmptyState, DatePipe],
  templateUrl: './recent-transactions.html',
  styleUrl: './recent-transactions.scss'
})
export class RecentTransactions {
  readonly transactions = input.required<readonly Transaction[]>();
  readonly categories = input<readonly Category[]>([]);

  protected categoryName(categoryId: string): string {
    return this.categories().find((c) => c.id === categoryId)?.name ?? 'Uncategorized';
  }

  protected formattedAmount(transaction: Transaction): string {
    const amount = CURRENCY_FORMATTER.format(transaction.amount);
    return transaction.transaction_type === 'income' ? `+${amount}` : `-${amount}`;
  }
}
