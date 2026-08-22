import { Type } from '@angular/core';

import { UIComponentType } from './models/ui-component.model';
import { ActionButton } from './components/action-button/action-button';
import { Alert } from './components/alert/alert';
import { BarChart } from './components/bar-chart/bar-chart';
import { DataTable } from './components/data-table/data-table';
import { InsightCard } from './components/insight-card/insight-card';
import { LineChart } from './components/line-chart/line-chart';
import { MetricCard } from './components/metric-card/metric-card';
import { PieChart } from './components/pie-chart/pie-chart';
import { Recommendation } from './components/recommendation/recommendation';

/** Maps a validated component's discriminant to the Angular component that
 * renders it. Every entry here corresponds 1:1 with a case in
 * `app/schemas/generative_ui.py`'s `_COMPONENT_MODELS` and the frontend's own
 * `ui-component-validator.ts` — a type can only reach this map after both
 * have already accepted it, so `resolveComponent` returning `null` means a
 * renderer was never registered for an otherwise-valid type (a wiring bug to
 * fix, not untrusted input to sanitize), and the caller falls back to
 * `UnknownFallback` either way. */
const COMPONENT_REGISTRY: Readonly<Record<UIComponentType, Type<unknown>>> = {
  metric_card: MetricCard,
  bar_chart: BarChart,
  line_chart: LineChart,
  pie_chart: PieChart,
  data_table: DataTable,
  insight_card: InsightCard,
  recommendation: Recommendation,
  alert: Alert,
  action_button: ActionButton
};

export function resolveComponent(type: UIComponentType): Type<unknown> {
  return COMPONENT_REGISTRY[type];
}
