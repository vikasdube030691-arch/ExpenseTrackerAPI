// Mirrors backend/app/schemas/generative_ui.py field-for-field. That file is
// the single source of truth for what "safe" means (no HTML, no URLs, no
// unknown props) — these types exist so the Angular renderer never has to
// guess a shape, only render one the backend already validated.

export type Tone = 'neutral' | 'positive' | 'negative';
export type TrendDirection = 'up' | 'down' | 'flat';
export type AlertSeverity = 'info' | 'warning' | 'error' | 'success';
export type Priority = 'low' | 'medium' | 'high';

/** The only "links" a generative UI block can carry — symbolic keys the
 * renderer maps to a real Angular route. There is no href/url field anywhere
 * in this model; an AI response can never specify an arbitrary destination. */
export type ActionKey =
  | 'navigate_dashboard'
  | 'navigate_transactions'
  | 'navigate_add_transaction'
  | 'navigate_budgets'
  | 'navigate_categories'
  | 'navigate_reports'
  | 'navigate_settings';

export interface MetricCardComponent {
  readonly component: 'metric_card';
  readonly title: string;
  readonly value: string;
  readonly change_percent: number | null;
  readonly trend: TrendDirection | null;
  readonly tone: Tone;
  readonly icon: string | null;
}

export interface ChartSeries {
  readonly name: string;
  readonly data: readonly number[];
  readonly color: string | null;
}

export interface BarChartComponent {
  readonly component: 'bar_chart';
  readonly title: string;
  readonly categories: readonly string[];
  readonly series: readonly ChartSeries[];
}

export interface LineChartComponent {
  readonly component: 'line_chart';
  readonly title: string;
  readonly categories: readonly string[];
  readonly series: readonly ChartSeries[];
}

export interface PieSlice {
  readonly label: string;
  readonly value: number;
  readonly color: string | null;
}

export interface PieChartComponent {
  readonly component: 'pie_chart';
  readonly title: string;
  readonly slices: readonly PieSlice[];
}

export type TableCell = string | number | boolean | null;

export interface DataTableComponent {
  readonly component: 'data_table';
  readonly title: string;
  readonly columns: readonly string[];
  readonly rows: readonly (readonly TableCell[])[];
}

export interface InsightCardComponent {
  readonly component: 'insight_card';
  readonly title: string;
  readonly body: string;
  readonly icon: string | null;
  readonly tone: Tone;
}

export interface RecommendationComponent {
  readonly component: 'recommendation';
  readonly title: string;
  readonly body: string;
  readonly action_label: string | null;
  readonly priority: Priority;
}

export interface AlertComponent {
  readonly component: 'alert';
  readonly severity: AlertSeverity;
  readonly message: string;
}

export interface ActionButtonComponent {
  readonly component: 'action_button';
  readonly label: string;
  readonly action: ActionKey;
}

export type UIComponent =
  | MetricCardComponent
  | BarChartComponent
  | LineChartComponent
  | PieChartComponent
  | DataTableComponent
  | InsightCardComponent
  | RecommendationComponent
  | AlertComponent
  | ActionButtonComponent;

export type UIComponentType = UIComponent['component'];
