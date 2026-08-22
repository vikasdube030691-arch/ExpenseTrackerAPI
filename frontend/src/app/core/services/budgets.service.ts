import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Budget, BudgetCreateRequest, BudgetUpdateRequest } from '../models/budget.model';

const BASE = `${environment.apiBaseUrl}/budgets`;

@Injectable({ providedIn: 'root' })
export class BudgetsService {
  private readonly http = inject(HttpClient);

  list(): Observable<readonly Budget[]> {
    return this.http.get<readonly Budget[]>(`${BASE}/`);
  }

  create(payload: BudgetCreateRequest): Observable<Budget> {
    return this.http.post<Budget>(`${BASE}/`, payload);
  }

  update(budgetId: string, payload: BudgetUpdateRequest): Observable<Budget> {
    return this.http.put<Budget>(`${BASE}/${budgetId}`, payload);
  }

  delete(budgetId: string): Observable<void> {
    return this.http.delete<void>(`${BASE}/${budgetId}`);
  }
}
