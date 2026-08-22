import { Injectable, computed, signal } from '@angular/core';

/** Global in-flight HTTP request counter, driven by `loadingInterceptor`. Used for a
 * top-of-page progress bar; individual pages/components still track their own local
 * loading signals for finer-grained states (e.g. a button spinner). */
@Injectable({ providedIn: 'root' })
export class LoadingService {
  private readonly _activeRequestCount = signal(0);

  readonly isLoading = computed(() => this._activeRequestCount() > 0);

  start(): void {
    this._activeRequestCount.update((count) => count + 1);
  }

  stop(): void {
    this._activeRequestCount.update((count) => Math.max(0, count - 1));
  }
}
