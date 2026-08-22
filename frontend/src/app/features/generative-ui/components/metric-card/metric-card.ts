import { Component, computed, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { MetricCardComponent as MetricCardData } from '../../models/ui-component.model';

@Component({
  selector: 'app-ui-metric-card',
  imports: [MatCardModule, MatIconModule],
  templateUrl: './metric-card.html',
  styleUrl: './metric-card.scss'
})
export class MetricCard {
  readonly data = input.required<MetricCardData>();

  protected readonly trendIcon = computed<string | null>(() => {
    const trend = this.data().trend;
    if (trend === 'up') return 'arrow_upward';
    if (trend === 'down') return 'arrow_downward';
    return null;
  });
}
