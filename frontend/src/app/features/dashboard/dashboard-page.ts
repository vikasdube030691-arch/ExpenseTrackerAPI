import { Component, computed, inject, signal } from '@angular/core';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

import {
  CategoryAnalysis,
  DashboardOverview,
  DashboardPreferences,
  TrendGranularity,
  Trends
} from '../../core/models/dashboard.model';
import { Category } from '../../core/models/category.model';
import { CategoriesService } from '../../core/services/categories.service';
import { DashboardService } from '../../core/services/dashboard.service';
import { ErrorState } from '../../shared/components/error-state/error-state';
import { LoadingState } from '../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../shared/components/page-header/page-header';
import { toApiError } from '../../shared/utils/http-error.util';
import { BudgetUsage } from './components/budget-usage/budget-usage';
import { CategoryBreakdown } from './components/category-breakdown/category-breakdown';
import { MonthlyTrends } from './components/monthly-trends/monthly-trends';
import { RecentTransactions } from './components/recent-transactions/recent-transactions';
import { SummaryCards } from './components/summary-cards/summary-cards';
import { DynamicWidgetsService } from '../generative-ui/dynamic-widgets.service';
import { WidgetRenderer } from '../generative-ui/widget-renderer/widget-renderer';

@Component({
  selector: 'app-dashboard-page',
  imports: [
    PageHeader,
    LoadingState,
    ErrorState,
    SummaryCards,
    BudgetUsage,
    RecentTransactions,
    CategoryBreakdown,
    MonthlyTrends,
    WidgetRenderer
  ],
  templateUrl: './dashboard-page.html',
  styleUrl: './dashboard-page.scss'
})
export class DashboardPage {
  private readonly dashboardService = inject(DashboardService);
  private readonly categoriesService = inject(CategoriesService);
  private readonly dynamicWidgetsService = inject(DynamicWidgetsService);

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly granularity = signal<TrendGranularity>('month');

  private readonly overview = signal<DashboardOverview | null>(null);
  private readonly categoryAnalysis = signal<CategoryAnalysis | null>(null);
  protected readonly trends = signal<Trends | null>(null);
  private readonly categories = signal<readonly Category[]>([]);
  private readonly preferences = signal<DashboardPreferences | null>(null);

  protected readonly showCategoryBreakdown = computed(
    () => this.preferences()?.widgets.includes('spending_by_category') ?? true
  );
  protected readonly showMonthlyTrends = computed(
    () => this.preferences()?.widgets.includes('monthly_trend') ?? true
  );
  protected readonly showBudgetUsage = computed(
    () => this.preferences()?.widgets.includes('budget_progress') ?? true
  );

  protected readonly hasData = computed(
    () => this.overview() !== null && this.categoryAnalysis() !== null && this.trends() !== null
  );

  protected readonly summary = computed(() => this.overview()?.summary ?? null);
  protected readonly recentTransactions = computed(() => this.overview()?.recent_transactions ?? []);
  protected readonly budgetProgress = computed(() => this.overview()?.budget_progress ?? []);
  protected readonly breakdown = computed(() => this.categoryAnalysis()?.breakdown ?? []);
  protected readonly categoryList = this.categories.asReadonly();

  protected readonly insights = computed(() => {
    const overview = this.overview();
    const categoryAnalysis = this.categoryAnalysis();
    const trends = this.trends();
    if (!overview || !categoryAnalysis || !trends) {
      return [];
    }
    return this.dynamicWidgetsService.deriveInsights(overview, categoryAnalysis, trends, this.categories());
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);

    forkJoin({
      overview: this.dashboardService.getOverview(),
      categoryAnalysis: this.dashboardService.getCategoryAnalysis(),
      trends: this.dashboardService.getTrends({}, this.granularity()),
      categories: this.categoriesService.list(),
      preferences: this.dashboardService.getPreferences().pipe(catchError(() => of(null)))
    }).subscribe({
      next: ({ overview, categoryAnalysis, trends, categories, preferences }) => {
        this.overview.set(overview);
        this.categoryAnalysis.set(categoryAnalysis);
        this.trends.set(trends);
        this.categories.set(categories);
        this.preferences.set(preferences);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.errorMessage.set(toApiError(error).message);
        this.loading.set(false);
      }
    });
  }

  onGranularityChange(granularity: TrendGranularity): void {
    this.granularity.set(granularity);
    this.dashboardService.getTrends({}, granularity).subscribe((trends) => this.trends.set(trends));
  }
}
