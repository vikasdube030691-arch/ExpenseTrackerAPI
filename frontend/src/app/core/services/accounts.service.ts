import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Account, AccountCreateRequest, AccountUpdateRequest } from '../models/account.model';

const BASE = `${environment.apiBaseUrl}/accounts`;

@Injectable({ providedIn: 'root' })
export class AccountsService {
  private readonly http = inject(HttpClient);

  list(includeInactive = false): Observable<readonly Account[]> {
    return this.http.get<readonly Account[]>(`${BASE}/`, {
      params: { include_inactive: String(includeInactive) }
    });
  }

  create(payload: AccountCreateRequest): Observable<Account> {
    return this.http.post<Account>(`${BASE}/`, payload);
  }

  update(accountId: string, payload: AccountUpdateRequest): Observable<Account> {
    return this.http.put<Account>(`${BASE}/${accountId}`, payload);
  }

  delete(accountId: string): Observable<void> {
    return this.http.delete<void>(`${BASE}/${accountId}`);
  }
}
