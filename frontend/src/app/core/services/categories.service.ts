import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Category, CategoryCreateRequest, CategoryType, CategoryUpdateRequest } from '../models/category.model';

const BASE = `${environment.apiBaseUrl}/categories`;

@Injectable({ providedIn: 'root' })
export class CategoriesService {
  private readonly http = inject(HttpClient);

  list(categoryType?: CategoryType): Observable<readonly Category[]> {
    return this.http.get<readonly Category[]>(`${BASE}/`, {
      params: categoryType ? { type: categoryType } : {}
    });
  }

  create(payload: CategoryCreateRequest): Observable<Category> {
    return this.http.post<Category>(`${BASE}/`, payload);
  }

  update(categoryId: string, payload: CategoryUpdateRequest): Observable<Category> {
    return this.http.put<Category>(`${BASE}/${categoryId}`, payload);
  }

  delete(categoryId: string): Observable<void> {
    return this.http.delete<void>(`${BASE}/${categoryId}`);
  }
}
