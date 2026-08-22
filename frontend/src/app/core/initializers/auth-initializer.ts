import { firstValueFrom } from 'rxjs';

import { AuthService } from '../services/auth.service';

/** Runs once before the app renders: tries to silently turn the httpOnly
 * refresh cookie (if any) into an access token, so a page reload with a
 * still-valid session doesn't bounce the user to /login. Never rejects —
 * a missing/expired cookie just leaves the user logged out. */
export function initializeAuth(authService: AuthService): () => Promise<boolean> {
  return () => firstValueFrom(authService.restoreSession());
}
