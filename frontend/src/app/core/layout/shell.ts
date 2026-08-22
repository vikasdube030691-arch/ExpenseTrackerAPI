import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { Component, computed, effect, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { map } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { LoadingService } from '../services/loading.service';
import { PRIMARY_NAV_ITEMS, SECONDARY_NAV_ITEMS } from './nav-items';

@Component({
  selector: 'app-shell',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule,
    MatMenuModule,
    MatDividerModule,
    MatProgressBarModule
  ],
  templateUrl: './shell.html',
  styleUrl: './shell.scss'
})
export class Shell {
  private readonly authService = inject(AuthService);
  private readonly loadingService = inject(LoadingService);
  private readonly router = inject(Router);
  private readonly breakpointObserver = inject(BreakpointObserver);

  protected readonly primaryNavItems = PRIMARY_NAV_ITEMS;
  protected readonly secondaryNavItems = SECONDARY_NAV_ITEMS;
  protected readonly currentUser = this.authService.currentUser;
  protected readonly isLoading = this.loadingService.isLoading;

  private readonly isHandset = toSignal(
    this.breakpointObserver.observe(Breakpoints.Handset).pipe(map((result) => result.matches)),
    { initialValue: false }
  );

  protected readonly sidenavMode = computed(() => (this.isHandset() ? 'over' : 'side'));
  protected readonly sidenavOpened = signal(!this.isHandset());

  protected readonly userInitial = computed(() => {
    const name = this.currentUser()?.full_name ?? '';
    return name.trim().charAt(0).toUpperCase() || '?';
  });

  constructor() {
    // Auto-open on desktop, auto-close on handset, whenever the breakpoint flips —
    // toggleSidenav() still overrides this until the breakpoint flips again.
    effect(() => this.sidenavOpened.set(!this.isHandset()));
  }

  toggleSidenav(): void {
    this.sidenavOpened.update((opened) => !opened);
  }

  closeSidenavOnMobile(): void {
    if (this.isHandset()) {
      this.sidenavOpened.set(false);
    }
  }

  logout(): void {
    this.authService.logout().subscribe(() => this.router.navigate(['/login']));
  }
}
