import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import {
  CategoryAnalysis,
  DashboardOverview,
  DashboardPreferences,
  DashboardPreferencesUpdateRequest,
  DashboardSummary,
  TrendGranularity,
  Trends
} from '../models/dashboard.model';

const BASE = `${environment.apiBaseUrl}/dashboard`;

export interface DashboardRangeParams {
  readonly start_date?: string;
  readonly end_date?: string;
}

function rangeToParams(range: DashboardRangeParams): HttpParams {
  let params = new HttpParams();
  if (range.start_date) {
    params = params.set('start_date', range.start_date);
  }
  if (range.end_date) {
    params = params.set('end_date', range.end_date);
  }
  return params;
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly http = inject(HttpClient);

  getOverview(): Observable<DashboardOverview> {
    return this.http.get<DashboardOverview>(`${BASE}/`);
  }

  getSummary(range: DashboardRangeParams = {}): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${BASE}/summary`, { params: rangeToParams(range) });
  }

  getCategoryAnalysis(range: DashboardRangeParams = {}): Observable<CategoryAnalysis> {
    return this.http.get<CategoryAnalysis>(`${BASE}/category-analysis`, { params: rangeToParams(range) });
  }

  getTrends(range: DashboardRangeParams = {}, granularity: TrendGranularity = 'month'): Observable<Trends> {
    return this.http.get<Trends>(`${BASE}/trends`, {
      params: rangeToParams(range).set('granularity', granularity)
    });
  }

  getPreferences(): Observable<DashboardPreferences> {
    return this.http.get<DashboardPreferences>(`${BASE}/preferences`);
  }

  updatePreferences(payload: DashboardPreferencesUpdateRequest): Observable<DashboardPreferences> {
    return this.http.put<DashboardPreferences>(`${BASE}/preferences`, payload);
  }
}
