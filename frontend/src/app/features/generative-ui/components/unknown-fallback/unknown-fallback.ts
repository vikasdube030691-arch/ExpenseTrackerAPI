import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-ui-unknown-fallback',
  imports: [MatIconModule],
  templateUrl: './unknown-fallback.html',
  styleUrl: './unknown-fallback.scss'
})
export class UnknownFallback {
  readonly reason = input<string>('This response included content that could not be safely displayed.');
}
