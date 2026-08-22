export interface Environment {
  readonly production: boolean;
  /** Relative so the Angular dev-server proxy (proxy.conf.json) — or, in production,
   * whatever reverse proxy serves this build — can route it without a CORS hop. */
  readonly apiBaseUrl: string;
}

export const environment: Environment = {
  production: true,
  apiBaseUrl: '/api/v1'
};
