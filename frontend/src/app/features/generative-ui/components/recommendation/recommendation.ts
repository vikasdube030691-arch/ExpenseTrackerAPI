import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { RecommendationComponent as RecommendationData } from '../../models/ui-component.model';

@Component({
  selector: 'app-ui-recommendation',
  imports: [MatCardModule, MatIconModule],
  templateUrl: './recommendation.html',
  styleUrl: './recommendation.scss'
})
export class Recommendation {
  readonly data = input.required<RecommendationData>();
}
