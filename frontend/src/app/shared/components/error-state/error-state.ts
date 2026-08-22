import { Component, input, output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-error-state',
  imports: [MatButtonModule, MatIconModule],
  templateUrl: './error-state.html',
  styleUrl: './error-state.scss'
})
export class ErrorState {
  readonly message = input('Something went wrong. Please try again.');
  readonly retryLabel = input('Retry');
  readonly retry = output<void>();
}
