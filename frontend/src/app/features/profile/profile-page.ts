import { DatePipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/components/confirm-dialog/confirm-dialog';
import { ErrorState } from '../../shared/components/error-state/error-state';
import { LoadingState } from '../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../shared/components/page-header/page-header';
import { toApiError } from '../../shared/utils/http-error.util';

@Component({
  selector: 'app-profile-page',
  imports: [DatePipe, MatButtonModule, MatCardModule, MatIconModule, PageHeader, LoadingState, ErrorState],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss'
})
export class ProfilePage {
  private readonly authService = inject(AuthService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);

  protected readonly loading = signal(true);
  protected readonly errorMessage = signal<string | null>(null);
  protected readonly signingOutEverywhere = signal(false);

  protected readonly user = this.authService.currentUser;
  protected readonly userInitial = computed(() => {
    const name = this.user()?.full_name ?? '';
    return name.trim().charAt(0).toUpperCase() || '?';
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.errorMessage.set(null);
    this.authService.fetchCurrentUser().subscribe({
      next: () => this.loading.set(false),
      error: (error: unknown) => {
        this.errorMessage.set(toApiError(error).message);
        this.loading.set(false);
      }
    });
  }

  logoutEverywhere(): void {
    const data: ConfirmDialogData = {
      title: 'Log out of all devices',
      message: 'This ends every active session, including this one. You will need to log in again.',
      confirmLabel: 'Log out everywhere',
      destructive: true
    };

    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed: boolean | undefined) => {
        if (!confirmed) {
          return;
        }
        this.signingOutEverywhere.set(true);
        this.authService.logoutAllDevices().subscribe({
          next: () => this.router.navigate(['/login']),
          error: (error: unknown) => {
            this.signingOutEverywhere.set(false);
            this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
          }
        });
      });
  }
}
