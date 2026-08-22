import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { DashboardWidget } from '../models/dashboard-widget.model';

@Component({
  selector: 'app-widget-renderer',
  imports: [MatCardModule, MatIconModule, MatProgressBarModule],
  templateUrl: './widget-renderer.html',
  styleUrl: './widget-renderer.scss'
})
export class WidgetRenderer {
  readonly widget = input.required<DashboardWidget>();

  protected progressBarColor(ratio: number): 'primary' | 'accent' | 'warn' {
    if (ratio >= 1) {
      return 'warn';
    }
    if (ratio >= 0.85) {
      return 'accent';
    }
    return 'primary';
  }
}
