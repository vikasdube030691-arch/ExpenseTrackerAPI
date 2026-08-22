export interface PaginatedResponse<T> {
  readonly items: readonly T[];
  readonly total: number;
  readonly page: number;
  readonly page_size: number;
}

export function totalPages(response: Pick<PaginatedResponse<unknown>, 'total' | 'page_size'>): number {
  if (response.page_size === 0) {
    return 0;
  }
  return Math.ceil(response.total / response.page_size);
}

export interface SortSpec {
  readonly field: string;
  readonly direction: 'asc' | 'desc';
}

export function sortSpecToQueryParam(sorts: readonly SortSpec[]): string {
  return sorts.map((s) => (s.direction === 'desc' ? `-${s.field}` : s.field)).join(',');
}
