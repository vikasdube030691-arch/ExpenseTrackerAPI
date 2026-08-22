import { HttpClient } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, catchError, finalize, map, of, shareReplay, switchMap, tap, throwError } from 'rxjs';

import { environment } from '../../../environments/environment';
import { AccessTokenResponse, LoginRequest, RegisterRequest } from '../models/auth.model';
import { User } from '../models/user.model';

export const AUTH_API_BASE = `${environment.apiBaseUrl}/auth`;

/**
 * Owns the in-memory access token and current user. The access token is
 * intentionally never persisted to localStorage/sessionStorage (an XSS bug
 * would be able to read it there); it lives only in this signal and is lost
 * on a full page reload, which is why `restoreSession()` exists — it silently
 * exchanges the httpOnly refresh cookie for a fresh access token on app boot.
 */
@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly _accessToken = signal<string | null>(null);
  private readonly _currentUser = signal<User | null>(null);
  private refreshInFlight$: Observable<string> | null = null;

  readonly currentUser = this._currentUser.asReadonly();
  readonly isAuthenticated = computed(() => this._accessToken() !== null);

  get accessToken(): string | null {
    return this._accessToken();
  }

  register(payload: RegisterRequest): Observable<User> {
    return this.http.post<User>(`${AUTH_API_BASE}/register`, payload);
  }

  login(payload: LoginRequest): Observable<User> {
    return this.http
      .post<AccessTokenResponse>(`${AUTH_API_BASE}/login`, payload, { withCredentials: true })
      .pipe(
        tap((response) => this._accessToken.set(response.access_token)),
        switchMap(() => this.fetchCurrentUser())
      );
  }

  /** Exchanges the httpOnly refresh cookie for a new access token. Concurrent
   * callers (e.g. several requests 401-ing at once) share one in-flight call. */
  refreshAccessToken(): Observable<string> {
    if (this.refreshInFlight$) {
      return this.refreshInFlight$;
    }
    this.refreshInFlight$ = this.http
      .post<AccessTokenResponse>(`${AUTH_API_BASE}/refresh`, {}, { withCredentials: true })
      .pipe(
        map((response) => response.access_token),
        tap((token) => this._accessToken.set(token)),
        shareReplay(1),
        finalize(() => (this.refreshInFlight$ = null))
      );
    return this.refreshInFlight$;
  }

  fetchCurrentUser(): Observable<User> {
    return this.http.get<User>(`${AUTH_API_BASE}/me`).pipe(tap((user) => this._currentUser.set(user)));
  }

  /** Call once at app bootstrap so a page reload with a still-valid session
   * doesn't get treated as logged out just because the in-memory token is gone. */
  restoreSession(): Observable<boolean> {
    return this.refreshAccessToken().pipe(
      switchMap(() => this.fetchCurrentUser()),
      map(() => true),
      catchError(() => {
        this.clearSession();
        return of(false);
      })
    );
  }

  logout(): Observable<void> {
    return this.http.post<void>(`${AUTH_API_BASE}/logout`, {}, { withCredentials: true }).pipe(
      map(() => void 0),
      catchError(() => of(void 0)),
      tap(() => this.clearSession())
    );
  }

  logoutAllDevices(): Observable<void> {
    return this.http.post<void>(`${AUTH_API_BASE}/logout-all`, {}, { withCredentials: true }).pipe(
      map(() => void 0),
      tap(() => this.clearSession()),
      catchError((error: unknown) => {
        this.clearSession();
        return throwError(() => error);
      })
    );
  }

  clearSession(): void {
    this._accessToken.set(null);
    this._currentUser.set(null);
  }
}
