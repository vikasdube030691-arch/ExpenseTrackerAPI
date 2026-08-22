import { ActionKey } from './models/ui-component.model';

/** The only place an `ActionKey` is ever turned into a real destination — a
 * closed, hardcoded map, never a value the AI response supplies directly. */
export const ACTION_ROUTES: Readonly<Record<ActionKey, string>> = {
  navigate_dashboard: '/dashboard',
  navigate_transactions: '/transactions',
  navigate_add_transaction: '/transactions/new',
  navigate_budgets: '/budgets',
  navigate_categories: '/categories',
  navigate_reports: '/reports',
  navigate_settings: '/settings'
};
