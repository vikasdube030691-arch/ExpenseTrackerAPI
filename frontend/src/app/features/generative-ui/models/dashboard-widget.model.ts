// A small, real (if currently rule-based) generative-UI system: `DynamicWidgetsService`
// derives these from already-fetched dashboard data, and `WidgetRenderer` renders
// whichever shape it's handed. Swapping the rule-based derivation for an actual
// LLM call later doesn't require touching the renderer or the dashboard page —
// only `DynamicWidgetsService`'s internals change.

export type DashboardWidgetKind = 'stat' | 'insight' | 'progress-list';

export type WidgetTone = 'neutral' | 'positive' | 'negative';

export interface StatDashboardWidget {
  readonly kind: 'stat';
  readonly id: string;
  readonly title: string;
  readonly value: string;
  readonly icon: string;
  readonly tone: WidgetTone;
}

export interface InsightDashboardWidget {
  readonly kind: 'insight';
  readonly id: string;
  readonly title: string;
  readonly body: string;
  readonly icon: string;
  readonly tone: WidgetTone;
}

export interface ProgressListItem {
  readonly label: string;
  readonly ratio: number;
  readonly detail: string;
}

export interface ProgressListDashboardWidget {
  readonly kind: 'progress-list';
  readonly id: string;
  readonly title: string;
  readonly items: readonly ProgressListItem[];
}

export type DashboardWidget = StatDashboardWidget | InsightDashboardWidget | ProgressListDashboardWidget;
