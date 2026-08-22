import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { InsightCardComponent as InsightCardData } from '../../models/ui-component.model';

@Component({
  selector: 'app-ui-insight-card',
  imports: [MatCardModule, MatIconModule],
  templateUrl: './insight-card.html',
  styleUrl: './insight-card.scss'
})
export class InsightCard {
  readonly data = input.required<InsightCardData>();
}
