import { DatePipe } from '@angular/common';
import { Component, ElementRef, effect, inject, signal, viewChild } from '@angular/core';
import { FormBuilder, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';

import { ChatMessage, ChatSession } from '../../core/models/chat.model';
import { ChatService } from '../../core/services/chat.service';
import { GenerativeUiRenderer } from '../generative-ui/generative-ui-renderer/generative-ui-renderer';
import { EmptyState } from '../../shared/components/empty-state/empty-state';
import { ErrorState } from '../../shared/components/error-state/error-state';
import { LoadingState } from '../../shared/components/loading-state/loading-state';
import { PageHeader } from '../../shared/components/page-header/page-header';
import { toApiError } from '../../shared/utils/http-error.util';

@Component({
  selector: 'app-ai-chat-page',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatIconModule,
    MatProgressSpinnerModule,
    PageHeader,
    LoadingState,
    ErrorState,
    EmptyState,
    GenerativeUiRenderer
  ],
  templateUrl: './ai-chat-page.html',
  styleUrl: './ai-chat-page.scss'
})
export class AiChatPage {
  private readonly fb = inject(FormBuilder);
  private readonly chatService = inject(ChatService);
  private readonly snackBar = inject(MatSnackBar);

  private readonly scrollAnchor = viewChild<ElementRef<HTMLElement>>('scrollAnchor');

  protected readonly sessionsLoading = signal(true);
  protected readonly sessionsError = signal<string | null>(null);
  protected readonly sessions = signal<readonly ChatSession[]>([]);

  protected readonly activeSessionId = signal<string | null>(null);
  protected readonly messagesLoading = signal(false);
  protected readonly messagesError = signal<string | null>(null);
  protected readonly messages = signal<readonly ChatMessage[]>([]);

  protected readonly sending = signal(false);
  protected readonly pendingUserText = signal<string | null>(null);
  protected readonly streamingReply = signal('');

  protected readonly messageControl = this.fb.nonNullable.control('');

  constructor() {
    this.loadSessions();

    effect(() => {
      this.messages();
      this.pendingUserText();
      this.streamingReply();
      queueMicrotask(() => {
        const anchor = this.scrollAnchor()?.nativeElement;
        anchor?.scrollIntoView({ block: 'end' });
      });
    });
  }

  loadSessions(): void {
    this.sessionsLoading.set(true);
    this.sessionsError.set(null);
    this.chatService.listSessions(1, 50).subscribe({
      next: (response) => {
        this.sessions.set(response.items);
        this.sessionsLoading.set(false);
      },
      error: (error: unknown) => {
        this.sessionsError.set(toApiError(error).message);
        this.sessionsLoading.set(false);
      }
    });
  }

  startNewChat(): void {
    this.activeSessionId.set(null);
    this.messages.set([]);
    this.messagesError.set(null);
  }

  selectSession(session: ChatSession): void {
    if (this.sending()) {
      return;
    }
    this.activeSessionId.set(session.id);
    this.loadMessages(session.id);
  }

  private loadMessages(sessionId: string): void {
    this.messagesLoading.set(true);
    this.messagesError.set(null);
    this.chatService.getSession(sessionId).subscribe({
      next: (detail) => {
        this.messages.set(detail.messages);
        this.messagesLoading.set(false);
      },
      error: (error: unknown) => {
        this.messagesError.set(toApiError(error).message);
        this.messagesLoading.set(false);
      }
    });
  }

  send(): void {
    const text = this.messageControl.value.trim();
    if (!text || this.sending()) {
      return;
    }

    this.sending.set(true);
    this.pendingUserText.set(text);
    this.streamingReply.set('');
    this.messageControl.setValue('');

    const sessionIdAtSend = this.activeSessionId();

    this.chatService.streamMessage({ session_id: sessionIdAtSend, message: text }).subscribe({
      next: (event) => {
        if (event.type === 'session' && !this.activeSessionId()) {
          this.activeSessionId.set(event.session_id);
        } else if (event.type === 'delta') {
          this.streamingReply.update((current) => current + event.delta);
        }
      },
      error: (error: unknown) => {
        this.sending.set(false);
        this.pendingUserText.set(null);
        this.streamingReply.set('');
        this.messageControl.setValue(text);
        this.snackBar.open(toApiError(error).message, 'Dismiss', { duration: 5000 });
      },
      complete: () => {
        this.sending.set(false);
        this.pendingUserText.set(null);
        this.streamingReply.set('');
        const sessionId = this.activeSessionId();
        if (sessionId) {
          this.loadMessages(sessionId);
        }
        this.loadSessions();
      }
    });
  }

  onInputKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.send();
    }
  }
}
