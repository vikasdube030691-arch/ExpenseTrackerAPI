import { Component, computed, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { LineChartComponent as LineChartData } from '../../models/ui-component.model';

const PALETTE = ['#4287f5', '#f59e42', '#42c785', '#c74dc7', '#e5484d', '#eab308'] as const;

function paletteColor(index: number): string {
  return PALETTE[index % PALETTE.length] ?? PALETTE[0];
}

interface LineSeriesRender {
  readonly name: string;
  readonly color: string;
  readonly points: string;
}

const VIEW_WIDTH = 100;
const VIEW_HEIGHT = 100;
const PADDING = 6;

@Component({
  selector: 'app-ui-line-chart',
  imports: [MatCardModule],
  templateUrl: './line-chart.html',
  styleUrl: './line-chart.scss'
})
export class LineChart {
  readonly data = input.required<LineChartData>();

  protected readonly viewBox = `0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`;

  protected readonly renderedSeries = computed<readonly LineSeriesRender[]>(() => {
    const { categories, series } = this.data();
    const max = Math.max(1, ...series.flatMap((s) => s.data));
    const min = Math.min(0, ...series.flatMap((s) => s.data));
    const range = max - min || 1;
    const stepX = categories.length > 1 ? (VIEW_WIDTH - PADDING * 2) / (categories.length - 1) : 0;

    return series.map((s, seriesIndex) => {
      const points = s.data
        .map((value, pointIndex) => {
          const x = PADDING + stepX * pointIndex;
          const y = VIEW_HEIGHT - PADDING - ((value - min) / range) * (VIEW_HEIGHT - PADDING * 2);
          return `${x.toFixed(2)},${y.toFixed(2)}`;
        })
        .join(' ');
      return { name: s.name, color: s.color ?? paletteColor(seriesIndex), points };
    });
  });
}
