import { Routes } from '@angular/router';

import { authGuard, guestGuard } from './core/guards/auth.guard';
import { Shell } from './core/layout/shell';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login').then((m) => m.Login),
    canActivate: [guestGuard]
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register/register').then((m) => m.Register),
    canActivate: [guestGuard]
  },
  {
    path: '',
    component: Shell,
    canActivate: [authGuard],
    children: [
      {
        path: 'dashboard',
        loadComponent: () => import('./features/dashboard/dashboard-page').then((m) => m.DashboardPage)
      },
      {
        path: 'transactions',
        loadComponent: () =>
          import('./features/transactions/transactions-list/transactions-list').then((m) => m.TransactionsList)
      },
      {
        path: 'transactions/new',
        loadComponent: () =>
          import('./features/transactions/transaction-form/transaction-form').then((m) => m.TransactionForm)
      },
      {
        path: 'transactions/:id/edit',
        loadComponent: () =>
          import('./features/transactions/transaction-form/transaction-form').then((m) => m.TransactionForm)
      },
      {
        path: 'categories',
        loadComponent: () => import('./features/categories/categories-page').then((m) => m.CategoriesPage)
      },
      {
        path: 'budgets',
        loadComponent: () => import('./features/budgets/budgets-page').then((m) => m.BudgetsPage)
      },
      {
        path: 'reports',
        loadComponent: () => import('./features/reports/reports-page').then((m) => m.ReportsPage)
      },
      {
        path: 'ai-chat',
        loadComponent: () => import('./features/ai-chat/ai-chat-page').then((m) => m.AiChatPage)
      },
      {
        path: 'profile',
        loadComponent: () => import('./features/profile/profile-page').then((m) => m.ProfilePage)
      },
      {
        path: 'settings',
        loadComponent: () => import('./features/settings/settings-page').then((m) => m.SettingsPage)
      },
      { path: '', pathMatch: 'full', redirectTo: 'dashboard' }
    ]
  },
  { path: '**', redirectTo: 'dashboard' }
];
