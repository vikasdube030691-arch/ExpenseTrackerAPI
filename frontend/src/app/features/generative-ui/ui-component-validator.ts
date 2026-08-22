// Defense in depth: `app/schemas/generative_ui.py` already validates every AI
// output before it reaches the API response, but the renderer never assumes
// that guarantee holds — it revalidates against the same rules (no HTML, no
// unknown component names, no unknown props, no unwhitelisted actions)
// before instantiating a single Angular component from this data.

import {
  ActionButtonComponent,
  ActionKey,
  AlertComponent,
  AlertSeverity,
  BarChartComponent,
  ChartSeries,
  DataTableComponent,
  InsightCardComponent,
  LineChartComponent,
  MetricCardComponent,
  PieChartComponent,
  PieSlice,
  Priority,
  RecommendationComponent,
  TableCell,
  Tone,
  TrendDirection,
  UIComponent,
  UIComponentType
} from './models/ui-component.model';

const MAX_TITLE_LENGTH = 240;
const MAX_BODY_LENGTH = 600;
const MAX_CELL_LENGTH = 240;
const MAX_ARRAY_LENGTH = 100;
const MAX_BLOCKS = 12;
const ICON_PATTERN = /^[a-z][a-z0-9_]{1,49}$/;
const COLOR_PATTERN = /^#[0-9A-Fa-f]{6}$/;
const DISALLOWED_CHARS = /[<>]/;

const TONES: readonly Tone[] = ['neutral', 'positive', 'negative'];
const TRENDS: readonly TrendDirection[] = ['up', 'down', 'flat'];
const SEVERITIES: readonly AlertSeverity[] = ['info', 'warning', 'error', 'success'];
const PRIORITIES: readonly Priority[] = ['low', 'medium', 'high'];
const ACTION_KEYS: readonly ActionKey[] = [
  'navigate_dashboard',
  'navigate_transactions',
  'navigate_add_transaction',
  'navigate_budgets',
  'navigate_categories',
  'navigate_reports',
  'navigate_settings'
];

export interface UIBlockRejection {
  readonly index: number;
  readonly reason: string;
}

export interface UIBlockValidationResult {
  readonly blocks: readonly UIComponent[];
  readonly rejected: readonly UIBlockRejection[];
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function hasOnlyKeys(obj: Record<string, unknown>, allowed: readonly string[]): boolean {
  return Object.keys(obj).every((key) => allowed.includes(key));
}

function isOneOf<T extends string>(value: unknown, allowed: readonly T[]): value is T {
  return typeof value === 'string' && (allowed as readonly string[]).includes(value);
}

function isFiniteNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isSafeText(value: unknown, maxLength: number): value is string {
  return typeof value === 'string' && value.trim().length > 0 && value.length <= maxLength && !DISALLOWED_CHARS.test(value);
}

function isSafeCellText(value: unknown, maxLength: number): value is string {
  return typeof value === 'string' && value.length <= maxLength && !DISALLOWED_CHARS.test(value);
}

function isSafeIcon(value: unknown): value is string {
  return typeof value === 'string' && ICON_PATTERN.test(value.toLowerCase());
}

function isSafeColor(value: unknown): value is string {
  return typeof value === 'string' && COLOR_PATTERN.test(value);
}

function isSafeTextArray(value: unknown, maxLength: number): value is readonly string[] {
  return (
    Array.isArray(value) &&
    value.length >= 1 &&
    value.length <= maxLength &&
    value.every((item) => isSafeText(item, MAX_TITLE_LENGTH))
  );
}

function isNumberArray(value: unknown, maxLength: number): value is readonly number[] {
  return Array.isArray(value) && value.length >= 1 && value.length <= maxLength && value.every(isFiniteNumber);
}

function isSafeTableCell(value: unknown): value is TableCell {
  return value === null || typeof value === 'boolean' || isFiniteNumber(value) || isSafeCellText(value, MAX_CELL_LENGTH);
}

function parseChartSeries(value: unknown, expectedLength: number): ChartSeries | null {
  if (!isPlainObject(value) || !hasOnlyKeys(value, ['name', 'color', 'data'])) {
    return null;
  }
  const name = value['name'];
  const data = value['data'];
  const color = value['color'] ?? null;

  if (!isSafeText(name, MAX_TITLE_LENGTH)) return null;
  if (!isNumberArray(data, 50) || data.length !== expectedLength) return null;
  if (color !== null && !isSafeColor(color)) return null;

  return { name, data, color };
}

function parseSeriesList(value: unknown, expectedLength: number, maxSeries: number): readonly ChartSeries[] | null {
  if (!Array.isArray(value) || value.length < 1 || value.length > maxSeries) {
    return null;
  }
  const series: ChartSeries[] = [];
  for (const raw of value) {
    const parsed = parseChartSeries(raw, expectedLength);
    if (parsed === null) return null;
    series.push(parsed);
  }
  return series;
}

function parseMetricCard(obj: Record<string, unknown>): MetricCardComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'title', 'value', 'change_percent', 'trend', 'tone', 'icon'])) return null;

  const title = obj['title'];
  const value = obj['value'];
  const changePercent = obj['change_percent'] ?? null;
  const trend = obj['trend'] ?? null;
  const tone = obj['tone'] ?? 'neutral';
  const icon = obj['icon'] ?? null;

  if (!isSafeText(title, MAX_TITLE_LENGTH)) return null;
  if (!isSafeText(value, MAX_TITLE_LENGTH)) return null;
  if (!(changePercent === null || isFiniteNumber(changePercent))) return null;
  if (!(trend === null || isOneOf(trend, TRENDS))) return null;
  if (!isOneOf(tone, TONES)) return null;
  if (!(icon === null || isSafeIcon(icon))) return null;

  return { component: 'metric_card', title, value, change_percent: changePercent, trend, tone, icon };
}

function parseBarChart(obj: Record<string, unknown>): BarChartComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'title', 'categories', 'series'])) return null;

  const title = obj['title'];
  const categories = obj['categories'];
  if (!isSafeText(title, MAX_TITLE_LENGTH)) return null;
  if (!isSafeTextArray(categories, 50)) return null;

  const series = parseSeriesList(obj['series'], categories.length, 6);
  if (series === null) return null;

  return { component: 'bar_chart', title, categories, series };
}

function parseLineChart(obj: Record<string, unknown>): LineChartComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'title', 'categories', 'series'])) return null;

  const title = obj['title'];
  const categories = obj['categories'];
  if (!isSafeText(title, MAX_TITLE_LENGTH)) return null;
  if (!isSafeTextArray(categories, 100) || categories.length < 2) return null;

  const series = parseSeriesList(obj['series'], categories.length, 6);
  if (series === null) return null;

  return { component: 'line_chart', title, categories, series };
}

function parsePieSlice(value: unknown): PieSlice | null {
  if (!isPlainObject(value) || !hasOnlyKeys(value, ['label', 'value', 'color'])) return null;
  const label = value['label'];
  const sliceValue = value['value'];
  const color = value['color'] ?? null;

  if (!isSafeText(label, MAX_TITLE_LENGTH)) return null;
  if (!isFiniteNumber(sliceValue) || sliceValue < 0) return null;
  if (color !== null && !isSafeColor(color)) return null;

  return { label, value: sliceValue, color };
}

function parsePieChart(obj: Record<string, unknown>): PieChartComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'title', 'slices'])) return null;

  const title = obj['title'];
  const rawSlices = obj['slices'];
  if (!isSafeText(title, MAX_TITLE_LENGTH)) return null;
  if (!Array.isArray(rawSlices) || rawSlices.length < 1 || rawSlices.length > 20) return null;

  const slices: PieSlice[] = [];
  for (const raw of rawSlices) {
    const parsed = parsePieSlice(raw);
    if (parsed === null) return null;
    slices.push(parsed);
  }

  return { component: 'pie_chart', title, slices };
}

function parseDataTable(obj: Record<string, unknown>): DataTableComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'title', 'columns', 'rows'])) return null;

  const title = obj['title'];
  const columns = obj['columns'];
  const rawRows = obj['rows'] ?? [];
  if (!isSafeText(title, MAX_TITLE_LENGTH)) return null;
  if (!isSafeTextArray(columns, 10)) return null;
  if (!Array.isArray(rawRows) || rawRows.length > 100) return null;

  const rows: TableCell[][] = [];
  for (const rawRow of rawRows) {
    if (!Array.isArray(rawRow) || rawRow.length !== columns.length) return null;
    const row: TableCell[] = [];
    for (const cell of rawRow) {
      if (!isSafeTableCell(cell)) return null;
      row.push(cell);
    }
    rows.push(row);
  }

  return { component: 'data_table', title, columns, rows };
}

function parseInsightCard(obj: Record<string, unknown>): InsightCardComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'title', 'body', 'icon', 'tone'])) return null;

  const title = obj['title'];
  const body = obj['body'];
  const icon = obj['icon'] ?? null;
  const tone = obj['tone'] ?? 'neutral';

  if (!isSafeText(title, MAX_TITLE_LENGTH)) return null;
  if (!isSafeText(body, MAX_BODY_LENGTH)) return null;
  if (!(icon === null || isSafeIcon(icon))) return null;
  if (!isOneOf(tone, TONES)) return null;

  return { component: 'insight_card', title, body, icon, tone };
}

function parseRecommendation(obj: Record<string, unknown>): RecommendationComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'title', 'body', 'action_label', 'priority'])) return null;

  const title = obj['title'];
  const body = obj['body'];
  const actionLabel = obj['action_label'] ?? null;
  const priority = obj['priority'] ?? 'medium';

  if (!isSafeText(title, MAX_TITLE_LENGTH)) return null;
  if (!isSafeText(body, MAX_BODY_LENGTH)) return null;
  if (!(actionLabel === null || isSafeText(actionLabel, MAX_TITLE_LENGTH))) return null;
  if (!isOneOf(priority, PRIORITIES)) return null;

  return { component: 'recommendation', title, body, action_label: actionLabel, priority };
}

function parseAlert(obj: Record<string, unknown>): AlertComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'severity', 'message'])) return null;

  const severity = obj['severity'];
  const message = obj['message'];
  if (!isOneOf(severity, SEVERITIES)) return null;
  if (!isSafeText(message, MAX_BODY_LENGTH)) return null;

  return { component: 'alert', severity, message };
}

function parseActionButton(obj: Record<string, unknown>): ActionButtonComponent | null {
  if (!hasOnlyKeys(obj, ['component', 'label', 'action'])) return null;

  const label = obj['label'];
  const action = obj['action'];
  if (!isSafeText(label, MAX_TITLE_LENGTH)) return null;
  if (!isOneOf(action, ACTION_KEYS)) return null;

  return { component: 'action_button', label, action };
}

const PARSERS: Readonly<Record<UIComponentType, (obj: Record<string, unknown>) => UIComponent | null>> = {
  metric_card: parseMetricCard,
  bar_chart: parseBarChart,
  line_chart: parseLineChart,
  pie_chart: parsePieChart,
  data_table: parseDataTable,
  insight_card: parseInsightCard,
  recommendation: parseRecommendation,
  alert: parseAlert,
  action_button: parseActionButton
};

function isKnownComponentType(value: string): value is UIComponentType {
  return value in PARSERS;
}

/** Validates untrusted `unknown` data (e.g. a chat message's `metadata['ui_blocks']`)
 * into safe, typed `UIComponent`s. Never throws — anything that doesn't validate is
 * recorded in `.rejected` and skipped, matching the backend's `validate_ui_blocks`
 * so one malformed block never blocks the rest of a valid response from rendering. */
export function validateUiBlocks(raw: unknown): UIBlockValidationResult {
  if (raw === null || raw === undefined) {
    return { blocks: [], rejected: [] };
  }
  if (!Array.isArray(raw)) {
    return { blocks: [], rejected: [{ index: 0, reason: 'ui_blocks must be an array' }] };
  }

  const blocks: UIComponent[] = [];
  const rejected: UIBlockRejection[] = [];

  raw.forEach((entry: unknown, index: number) => {
    if (index >= MAX_ARRAY_LENGTH || blocks.length + rejected.length >= MAX_BLOCKS) {
      rejected.push({ index, reason: `exceeds max of ${MAX_BLOCKS} blocks` });
      return;
    }
    if (!isPlainObject(entry)) {
      rejected.push({ index, reason: 'block must be an object' });
      return;
    }
    const componentName = entry['component'];
    if (typeof componentName !== 'string' || !isKnownComponentType(componentName)) {
      rejected.push({ index, reason: `unknown component type: ${String(componentName)}` });
      return;
    }
    const parsed = PARSERS[componentName](entry);
    if (parsed === null) {
      rejected.push({ index, reason: `invalid props for component '${componentName}'` });
      return;
    }
    blocks.push(parsed);
  });

  return { blocks, rejected };
}
