import { Injectable } from '@angular/core';

import { CategoryAnalysis, DashboardOverview, Trends } from '../../core/models/dashboard.model';
import { Category } from '../../core/models/category.model';
import { DashboardWidget } from './models/dashboard-widget.model';

const HIGH_BUDGET_USAGE_RATIO = 0.85;
const CURRENCY_FORMATTER = new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' });

function formatCurrency(amount: number): string {
  return CURRENCY_FORMATTER.format(amount);
}

function categoryName(categoryId: string, categories: readonly Category[]): string {
  return categories.find((c) => c.id === categoryId)?.name ?? 'Uncategorized';
}

/**
 * Derives a handful of "AI insight" widgets purely from data already fetched for the
 * dashboard — no model call happens here. This is a stand-in for a real LLM-driven
 * insight generator (the backend's own `/chat` has the same kind of placeholder —
 * see `app/services/ai/chat_completion.py`), kept deliberately simple and inspectable
 * so it's obvious it's rule-based rather than claiming AI capability it doesn't have.
 */
@Injectable({ providedIn: 'root' })
export class DynamicWidgetsService {
  deriveInsights(
    overview: DashboardOverview,
    categoryAnalysis: CategoryAnalysis,
    trends: Trends,
    categories: readonly Category[]
  ): readonly DashboardWidget[] {
    const widgets: DashboardWidget[] = [];

    const topCategory = [...categoryAnalysis.breakdown].sort((a, b) => b.total - a.total)[0];
    if (topCategory) {
      widgets.push({
        kind: 'insight',
        id: 'top-category',
        title: 'Top spending category',
        icon: 'insights',
        tone: 'neutral',
        body: `${categoryName(topCategory.category_id, categories)} is your biggest expense category this period, at ${formatCurrency(topCategory.total)} across ${topCategory.count} transaction${topCategory.count === 1 ? '' : 's'}.`
      });
    }

    const atRiskBudget = overview.budget_progress.find((b) => b.amount > 0 && b.spent / b.amount >= HIGH_BUDGET_USAGE_RATIO);
    if (atRiskBudget) {
      const usagePercent = Math.round((atRiskBudget.spent / atRiskBudget.amount) * 100);
      widgets.push({
        kind: 'insight',
        id: `budget-risk-${atRiskBudget.budget_id}`,
        title: 'Budget running high',
        icon: 'warning',
        tone: usagePercent >= 100 ? 'negative' : 'neutral',
        body: `You've used ${usagePercent}% of your ${atRiskBudget.name ?? 'overall'} budget${
          usagePercent >= 100 ? ' — you are over budget.' : '.'
        }`
      });
    }

    if (trends.points.length >= 2) {
      const last = trends.points[trends.points.length - 1];
      const previous = trends.points[trends.points.length - 2];
      if (last && previous && previous.expense > 0) {
        const changePercent = Math.round(((last.expense - previous.expense) / previous.expense) * 100);
        if (Math.abs(changePercent) >= 5) {
          widgets.push({
            kind: 'insight',
            id: 'trend-change',
            title: 'Spending trend',
            icon: changePercent > 0 ? 'trending_up' : 'trending_down',
            tone: changePercent > 0 ? 'negative' : 'positive',
            body: `Expenses ${changePercent > 0 ? 'increased' : 'decreased'} by ${Math.abs(changePercent)}% compared to the previous ${trends.granularity}.`
          });
        }
      }
    }

    if (widgets.length === 0) {
      widgets.push({
        kind: 'insight',
        id: 'no-insights-yet',
        title: 'Keep going',
        icon: 'auto_awesome',
        tone: 'neutral',
        body: 'Add a few more transactions and budgets and insights will start showing up here.'
      });
    }

    return widgets;
  }
}
