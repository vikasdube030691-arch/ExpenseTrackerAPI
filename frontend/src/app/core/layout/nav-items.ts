export interface NavItem {
  readonly path: string;
  readonly label: string;
  readonly icon: string;
}

export const PRIMARY_NAV_ITEMS: readonly NavItem[] = [
  { path: '/dashboard', label: 'Dashboard', icon: 'dashboard' },
  { path: '/transactions', label: 'Transactions', icon: 'receipt_long' },
  { path: '/categories', label: 'Categories', icon: 'category' },
  { path: '/budgets', label: 'Budgets', icon: 'savings' },
  { path: '/reports', label: 'Reports', icon: 'summarize' },
  { path: '/ai-chat', label: 'AI Chat', icon: 'smart_toy' }
];

export const SECONDARY_NAV_ITEMS: readonly NavItem[] = [
  { path: '/profile', label: 'Profile', icon: 'person' },
  { path: '/settings', label: 'Settings', icon: 'settings' }
];
