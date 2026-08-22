import { DecimalPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatButtonToggleModule } from '@angular/material/button-toggle';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar } from '@angular/material/snack-bar';

import { Account } from '../../core/models/account.model';
import { DashboardPreferences } from '../../core/models/dashboard.model';
import { AccountsService } from '../../core/services/accounts.service';
import { DashboardService } from '../../core/services/dashboard.service';
import { ThemeChoice, ThemeService } from '../../core/services/theme.service';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/components/confirm-dialog/confirm-dialog';
import { EmptyState } from '../../shared/components/empty-state/empty-state';
import { ErrorState } from '../../shared/components/error-state/error-state';
import { LoadingState } from '../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../shared/components/page-header/page-header';
import { toApiError } from '../../shared/utils/http-error.util';
import { AccountDialog, AccountDialogData, AccountDialogResult } from './account-dialog/account-dialog';

export interface DashboardWidgetOption {
  readonly key: string;
  readonly label: string;
}

const DASHBOARD_WIDGET_OPTIONS: readonly DashboardWidgetOption[] = [
  { key: 'spending_by_category', label: 'Spending by category' },
  { key: 'monthly_trend', label: 'Monthly trend' },
  { key: 'budget_progress', label: 'Budget progress' }
];

@Component({
  selector: 'app-settings-page',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatButtonToggleModule,
    MatCardModule,
    MatCheckboxModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatSlideToggleModule,
    PageHeader,
    LoadingState,
    ErrorState,
    EmptyState
  ],
  templateUrl: './settings-page.html',
  styleUrl: './settings-page.scss'
})
export class SettingsPage {
  private readonly fb = inject(FormBuilder);
  private readonly themeService = inject(ThemeService);
  private readonly dashboardService = inject(DashboardService);
  private readonly accountsService = inject(AccountsService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly widgetOptions = DASHBOARD_WIDGET_OPTIONS;
  protected readonly theme = this.themeService.theme;

  protected readonly preferencesLoading = signal(true);
  protected readonly preferencesError = signal<string | null>(null);
  protected readonly savingPreferences = signal(false);

  protected readonly accountsLoading = signal(true);
  protected readonly accountsError = signal<string | null>(null);
  protected readonly accounts = signal<readonly Account[]>([]);

  protected readonly preferencesForm = this.fb.nonNullable.group({
    default_currency: ['USD', [Validators.required, Validators.minLength(3), Validators.maxLength(3)]],
    widgets: this.fb.nonNullable.control<readonly string[]>(DASHBOARD_WIDGET_OPTIONS.map((o) => o.key))
  });

  constructor() {
    this.loadPreferences();
    this.loadAccounts();
  }

  setTheme(choice: ThemeChoice): void {
    this.themeService.setTheme(choice);
  }

  loadPreferences(): void {
    this.preferencesLoading.set(true);
    this.preferencesError.set(null);
    this.dashboardService.getPreferences().subscribe({
      next: (preferences) => {
        this.preferencesForm.patchValue({
          default_currency: preferences.default_currency,
          widgets: preferences.widgets
        });
        this.preferencesLoading.set(false);
      },
      error: (error: unknown) => {
        this.preferencesError.set(toApiError(error).message);
        this.preferencesLoading.set(false);
      }
    });
  }

  isWidgetEnabled(key: string): boolean {
    return this.preferencesForm.controls.widgets.value.includes(key);
  }

  toggleWidget(key: string, checked: boolean): void {
    const current = this.preferencesForm.controls.widgets.value;
    const next = checked ? [...current, key] : current.filter((w) => w !== key);
    this.preferencesForm.controls.widgets.setValue(next);
  }

  savePreferences(): void {
    if (this.preferencesForm.invalid || this.savingPreferences()) {
      this.preferencesForm.markAllAsTouched();
      return;
    }

    this.savingPreferences.set(true);
    const raw = this.preferencesForm.getRawValue();
    this.dashboardService
      .updatePreferences({ default_currency: raw.default_currency.toUpperCase(), widgets: raw.widgets })
      .subscribe({
        next: (preferences: DashboardPreferences) => {
          this.savingPreferences.set(false);
          this.preferencesForm.patchValue({
            default_currency: preferences.default_currency,
            widgets: preferences.widgets
          });
          this.snackBar.open('Preferences saved', 'Dismiss', { duration: 3000 });
        },
        error: (error: unknown) => {
          this.savingPreferences.set(false);
          this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
        }
      });
  }

  loadAccounts(): void {
    this.accountsLoading.set(true);
    this.accountsError.set(null);
    this.accountsService.list(true).subscribe({
      next: (accounts) => {
        this.accounts.set(accounts);
        this.accountsLoading.set(false);
      },
      error: (error: unknown) => {
        this.accountsError.set(toApiError(error).message);
        this.accountsLoading.set(false);
      }
    });
  }

  openCreateAccountDialog(): void {
    this.openAccountDialog(null);
  }

  openEditAccountDialog(account: Account): void {
    this.openAccountDialog(account);
  }

  private openAccountDialog(account: Account | null): void {
    const data: AccountDialogData = { account };
    this.dialog
      .open(AccountDialog, { data, width: '420px' })
      .afterClosed()
      .subscribe((result: AccountDialogResult | undefined) => {
        if (!result) {
          return;
        }

        const request$ = account
          ? this.accountsService.update(account.id, {
              name: result.name,
              account_type: result.account_type,
              is_active: result.is_active
            })
          : this.accountsService.create({
              name: result.name,
              account_type: result.account_type,
              currency: result.currency,
              balance: result.balance
            });

        request$.subscribe({
          next: () => {
            this.snackBar.open(account ? 'Account updated' : 'Account created', 'Dismiss', { duration: 3000 });
            this.loadAccounts();
          },
          error: (error: unknown) => {
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }

  deleteAccount(account: Account): void {
    const data: ConfirmDialogData = {
      title: 'Delete account',
      message: `Delete "${account.name}"? This cannot be undone.`,
      confirmLabel: 'Delete',
      destructive: true
    };

    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed: boolean | undefined) => {
        if (!confirmed) {
          return;
        }
        this.accountsService.delete(account.id).subscribe({
          next: () => {
            this.snackBar.open('Account deleted', 'Dismiss', { duration: 3000 });
            this.loadAccounts();
          },
          error: (error: unknown) => {
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }
}
