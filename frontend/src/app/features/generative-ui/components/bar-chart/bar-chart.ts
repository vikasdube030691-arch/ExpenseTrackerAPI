import { DecimalPipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { BarChartComponent as BarChartData } from '../../models/ui-component.model';

const PALETTE = ['#4287f5', '#f59e42', '#42c785', '#c74dc7', '#e5484d', '#eab308'] as const;

function paletteColor(index: number): string {
  return PALETTE[index % PALETTE.length] ?? PALETTE[0];
}

interface BarSegment {
  readonly seriesName: string;
  readonly percent: number;
  readonly value: number;
  readonly color: string;
}

interface BarGroup {
  readonly category: string;
  readonly bars: readonly BarSegment[];
}

@Component({
  selector: 'app-ui-bar-chart',
  imports: [DecimalPipe, MatCardModule],
  templateUrl: './bar-chart.html',
  styleUrl: './bar-chart.scss'
})
export class BarChart {
  readonly data = input.required<BarChartData>();

  protected readonly legend = computed(() =>
    this.data().series.map((series, index) => ({ name: series.name, color: series.color ?? paletteColor(index) }))
  );

  protected readonly groups = computed<readonly BarGroup[]>(() => {
    const { categories, series } = this.data();
    const max = Math.max(1, ...series.flatMap((s) => s.data));

    return categories.map((category, categoryIndex) => ({
      category,
      bars: series.map((s, seriesIndex) => {
        const value = s.data[categoryIndex] ?? 0;
        return {
          seriesName: s.name,
          percent: (value / max) * 100,
          value,
          color: s.color ?? paletteColor(seriesIndex)
        };
      })
    }));
  });
}
