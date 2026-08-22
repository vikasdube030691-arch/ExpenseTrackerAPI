export interface LoginRequest {
  readonly email: string;
  readonly password: string;
}

export interface RegisterRequest {
  readonly email: string;
  readonly password: string;
  readonly full_name: string;
}

export interface AccessTokenResponse {
  readonly access_token: string;
  readonly token_type: string;
  readonly expires_in: number;
}
