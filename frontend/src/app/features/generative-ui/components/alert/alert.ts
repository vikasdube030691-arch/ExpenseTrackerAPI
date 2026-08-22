import { Component, computed, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';

import { AlertComponent as AlertData } from '../../models/ui-component.model';

@Component({
  selector: 'app-ui-alert',
  imports: [MatIconModule],
  templateUrl: './alert.html',
  styleUrl: './alert.scss'
})
export class Alert {
  readonly data = input.required<AlertData>();

  protected readonly icon = computed(() => {
    switch (this.data().severity) {
      case 'error':
        return 'error';
      case 'warning':
        return 'warning';
      case 'success':
        return 'check_circle';
      default:
        return 'info';
    }
  });
}
