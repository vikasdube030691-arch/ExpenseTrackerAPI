import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { DataTableComponent as DataTableData } from '../../models/ui-component.model';

@Component({
  selector: 'app-ui-data-table',
  imports: [MatCardModule],
  templateUrl: './data-table.html',
  styleUrl: './data-table.scss'
})
export class DataTable {
  readonly data = input.required<DataTableData>();

  protected cellText(value: string | number | boolean | null): string {
    if (value === null) return '—';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    return String(value);
  }
}
