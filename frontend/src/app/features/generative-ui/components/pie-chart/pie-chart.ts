import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { PieChartComponent as PieChartData } from '../../models/ui-component.model';

const PALETTE = ['#4287f5', '#f59e42', '#42c785', '#c74dc7', '#e5484d', '#eab308', '#0ea5e9', '#a855f7'] as const;

function paletteColor(index: number): string {
  return PALETTE[index % PALETTE.length] ?? PALETTE[0];
}

interface RenderedSlice {
  readonly label: string;
  readonly value: number;
  readonly percent: number;
  readonly color: string;
}

@Component({
  selector: 'app-ui-pie-chart',
  imports: [DecimalPipe, MatCardModule],
  templateUrl: './pie-chart.html',
  styleUrl: './pie-chart.scss'
})
export class PieChart {
  readonly data = input.required<PieChartData>();

  protected readonly total = computed(() => this.data().slices.reduce((sum, slice) => sum + slice.value, 0));

  protected readonly renderedSlices = computed<readonly RenderedSlice[]>(() => {
    const total = this.total() || 1;
    return this.data().slices.map((slice, index) => ({
      label: slice.label,
      value: slice.value,
      percent: (slice.value / total) * 100,
      color: slice.color ?? paletteColor(index)
    }));
  });

  protected readonly gradient = computed(() => {
    let cursor = 0;
    const stops = this.renderedSlices().map((slice) => {
      const start = cursor;
      cursor += slice.percent;
      return `${slice.color} ${start.toFixed(2)}% ${cursor.toFixed(2)}%`;
    });
    return stops.length > 0 ? `conic-gradient(${stops.join(', ')})` : 'none';
  });
}
