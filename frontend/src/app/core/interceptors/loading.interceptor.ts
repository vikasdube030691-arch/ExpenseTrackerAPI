import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { finalize } from 'rxjs';

import { LoadingService } from '../services/loading.service';

/** Drives the global top-of-page progress bar. Skips /chat/stream, which is
 * fetched directly (see ChatService) and never passes through HttpClient. */
export const loadingInterceptor: HttpInterceptorFn = (req, next) => {
  const loadingService = inject(LoadingService);

  loadingService.start();
  return next(req).pipe(finalize(() => loadingService.stop()));
};
