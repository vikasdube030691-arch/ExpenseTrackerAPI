export type CategoryType = 'income' | 'expense';

export interface Category {
  readonly id: string;
  readonly user_id: string | null;
  readonly name: string;
  readonly type: CategoryType;
  readonly icon: string | null;
  readonly color: string | null;
  readonly is_system: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface CategoryCreateRequest {
  readonly name: string;
  readonly type: CategoryType;
  readonly icon?: string | null;
  readonly color?: string | null;
}

export interface CategoryUpdateRequest {
  readonly name?: string;
  readonly icon?: string | null;
  readonly color?: string | null;
}
