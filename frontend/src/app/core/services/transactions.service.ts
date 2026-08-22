import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { PaginatedResponse } from '../models/pagination.model';
import {
  Transaction,
  TransactionCreateRequest,
  TransactionFilter,
  TransactionUpdateRequest
} from '../models/transaction.model';

const BASE = `${environment.apiBaseUrl}/transactions`;

export interface TransactionListParams extends TransactionFilter {
  readonly page?: number;
  readonly page_size?: number;
  readonly sort?: string;
}

function buildParams(params: TransactionListParams): HttpParams {
  let httpParams = new HttpParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      httpParams = httpParams.set(key, String(value));
    }
  }
  return httpParams;
}

@Injectable({ providedIn: 'root' })
export class TransactionsService {
  private readonly http = inject(HttpClient);

  list(params: TransactionListParams): Observable<PaginatedResponse<Transaction>> {
    return this.http.get<PaginatedResponse<Transaction>>(`${BASE}/`, { params: buildParams(params) });
  }

  get(transactionId: string): Observable<Transaction> {
    return this.http.get<Transaction>(`${BASE}/${transactionId}`);
  }

  create(payload: TransactionCreateRequest): Observable<Transaction> {
    return this.http.post<Transaction>(`${BASE}/`, payload);
  }

  update(transactionId: string, payload: TransactionUpdateRequest): Observable<Transaction> {
    return this.http.put<Transaction>(`${BASE}/${transactionId}`, payload);
  }

  delete(transactionId: string): Observable<void> {
    return this.http.delete<void>(`${BASE}/${transactionId}`);
  }
}
