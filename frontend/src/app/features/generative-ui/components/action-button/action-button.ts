import { Component, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { Router } from '@angular/router';

import { ActionButtonComponent as ActionButtonData } from '../../models/ui-component.model';
import { ACTION_ROUTES } from '../../action-routes';

@Component({
  selector: 'app-ui-action-button',
  imports: [MatButtonModule],
  templateUrl: './action-button.html',
  styleUrl: './action-button.scss'
})
export class ActionButton {
  private readonly router = inject(Router);

  readonly data = input.required<ActionButtonData>();

  navigate(): void {
    this.router.navigate([ACTION_ROUTES[this.data().action]]);
  }
}
