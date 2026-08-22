import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';

import { AUTH_API_BASE, AuthService } from '../services/auth.service';

// The refresh cookie is scoped to /api/v1/auth and only /login, /register and
// /refresh legitimately run without a (or with a not-yet-valid) access token, so
// they must never be intercepted into a refresh-and-retry loop on 401.
const NO_INTERCEPT_PATHS = [`${AUTH_API_BASE}/login`, `${AUTH_API_BASE}/register`, `${AUTH_API_BASE}/refresh`];

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const isExemptPath = NO_INTERCEPT_PATHS.some((path) => req.url.includes(path));

  const token = authService.accessToken;
  const authorizedReq = token && !isExemptPath ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(authorizedReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401 || isExemptPath) {
        return throwError(() => error);
      }

      return authService.refreshAccessToken().pipe(
        switchMap((newToken) => {
          const retriedReq = req.clone({ setHeaders: { Authorization: `Bearer ${newToken}` } });
          return next(retriedReq);
        }),
        catchError((refreshError: unknown) => {
          authService.clearSession();
          router.navigate(['/login'], { queryParams: { sessionExpired: 'true' } });
          return throwError(() => refreshError);
        })
      );
    })
  );
};
