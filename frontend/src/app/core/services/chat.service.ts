import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ChatStreamEvent } from '../models/chat-stream-event.model';
import { ChatRequest, ChatResponse, ChatSessionDetail, ChatSession } from '../models/chat.model';
import { PaginatedResponse } from '../models/pagination.model';
import { AuthService } from './auth.service';

const BASE = `${environment.apiBaseUrl}/chat`;

function parseSseBlock(block: string): { event: string; data: string } | null {
  let eventName = 'message';
  const dataLines: string[] = [];
  for (const line of block.split('\n')) {
    if (line.startsWith('event:')) {
      eventName = line.slice('event:'.length).trim();
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice('data:'.length).trim());
    }
  }
  if (dataLines.length === 0) {
    return null;
  }
  return { event: eventName, data: dataLines.join('\n') };
}

function toStreamEvent(event: string, data: string): ChatStreamEvent | null {
  switch (event) {
    case 'session': {
      const parsed = JSON.parse(data) as { session_id: string };
      return { type: 'session', session_id: parsed.session_id };
    }
    case 'delta': {
      const parsed = JSON.parse(data) as { delta: string };
      return { type: 'delta', delta: parsed.delta };
    }
    case 'done':
      return { type: 'done' };
    default:
      return null;
  }
}

/** Chat over plain request/response (`ChatService.send`) and over Server-Sent
 * Events (`ChatService.streamMessage`). SSE needs a readable-stream response body,
 * which the Angular HttpClient doesn't expose — this uses `fetch` directly and
 * therefore attaches the bearer token itself rather than going through
 * `authInterceptor`. It does not attempt an access-token refresh-and-retry the way
 * the interceptor does for ordinary requests; a token that expires mid-stream
 * surfaces as an error on the returned Observable. */
@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly authService = inject(AuthService);

  send(payload: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${BASE}/`, payload);
  }

  listSessions(page = 1, pageSize = 20): Observable<PaginatedResponse<ChatSession>> {
    return this.http.get<PaginatedResponse<ChatSession>>(`${BASE}/sessions`, {
      params: { page: String(page), page_size: String(pageSize) }
    });
  }

  getSession(sessionId: string): Observable<ChatSessionDetail> {
    return this.http.get<ChatSessionDetail>(`${BASE}/sessions/${sessionId}`);
  }

  streamMessage(payload: ChatRequest): Observable<ChatStreamEvent> {
    return new Observable<ChatStreamEvent>((subscriber) => {
      const controller = new AbortController();
      const token = this.authService.accessToken;

      fetch(`${BASE}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        credentials: 'include',
        body: JSON.stringify(payload),
        signal: controller.signal
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            throw new Error(`Chat stream request failed with status ${response.status}`);
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          for (;;) {
            const { done, value } = await reader.read();
            if (done) {
              break;
            }
            buffer += decoder.decode(value, { stream: true });

            let boundary = buffer.indexOf('\n\n');
            while (boundary !== -1) {
              const block = buffer.slice(0, boundary);
              buffer = buffer.slice(boundary + 2);

              const parsed = parseSseBlock(block);
              if (parsed) {
                const streamEvent = toStreamEvent(parsed.event, parsed.data);
                if (streamEvent) {
                  subscriber.next(streamEvent);
                }
              }
              boundary = buffer.indexOf('\n\n');
            }
          }
          subscriber.complete();
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted) {
            subscriber.error(error);
          }
        });

      return () => controller.abort();
    });
  }
}
