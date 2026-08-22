import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { PaginatedResponse } from '../models/pagination.model';
import { Report, ReportCreateRequest } from '../models/report.model';

const BASE = `${environment.apiBaseUrl}/reports`;

@Injectable({ providedIn: 'root' })
export class ReportsService {
  private readonly http = inject(HttpClient);

  generate(payload: ReportCreateRequest): Observable<Report> {
    return this.http.post<Report>(`${BASE}/generate`, payload);
  }

  list(page = 1, pageSize = 20): Observable<PaginatedResponse<Report>> {
    return this.http.get<PaginatedResponse<Report>>(`${BASE}/`, {
      params: { page: String(page), page_size: String(pageSize) }
    });
  }

  get(reportId: string): Observable<Report> {
    return this.http.get<Report>(`${BASE}/${reportId}`);
  }
}
