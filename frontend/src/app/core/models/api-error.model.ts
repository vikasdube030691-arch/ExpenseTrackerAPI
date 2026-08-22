export interface ApiErrorDetail {
  readonly code: string;
  readonly message: string;
  readonly request_id: string | null;
  readonly details: unknown;
}

export interface ApiErrorResponse {
  readonly error: ApiErrorDetail;
}

/** The shape every error from the backend takes (see backend `app/schemas/error.py`). */
export interface ApiError {
  readonly status: number;
  readonly code: string;
  readonly message: string;
  readonly requestId: string | null;
}

function isApiErrorResponse(value: unknown): value is ApiErrorResponse {
  if (typeof value !== 'object' || value === null || !('error' in value)) {
    return false;
  }
  const candidate = (value as { error: unknown }).error;
  return (
    typeof candidate === 'object' &&
    candidate !== null &&
    'code' in candidate &&
    'message' in candidate
  );
}

export function parseApiError(status: number, body: unknown, fallbackMessage: string): ApiError {
  if (isApiErrorResponse(body)) {
    return {
      status,
      code: body.error.code,
      message: body.error.message,
      requestId: body.error.request_id
    };
  }
  return { status, code: 'unknown_error', message: fallbackMessage, requestId: null };
}
