import { HttpErrorResponse } from '@angular/common/http';

import { ApiError, parseApiError } from '../../core/models/api-error.model';

const DEFAULT_MESSAGE = 'Something went wrong. Please try again.';

export function toApiError(error: unknown, fallbackMessage: string = DEFAULT_MESSAGE): ApiError {
  if (error instanceof HttpErrorResponse) {
    return parseApiError(error.status, error.error, fallbackMessage);
  }
  return { status: 0, code: 'unknown_error', message: fallbackMessage, requestId: null };
}
