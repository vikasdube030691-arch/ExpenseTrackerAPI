import { Injectable, signal } from '@angular/core';

export type ThemeChoice = 'system' | 'light' | 'dark';

const STORAGE_KEY = 'expense-tracker-theme';
const THEME_CLASSES: Readonly<Record<ThemeChoice, string | null>> = {
  system: null,
  light: 'app-theme-light',
  dark: 'app-theme-dark'
};

function isThemeChoice(value: string | null): value is ThemeChoice {
  return value === 'system' || value === 'light' || value === 'dark';
}

/** Applies the light/dark override class from `styles.scss` to <html>. Not
 * security-sensitive, so — unlike the access token — this is fine to keep in
 * localStorage for an instant, no-flash choice before the backend preference
 * (the source of truth) loads. */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly _theme = signal<ThemeChoice>(this.readStoredTheme());

  readonly theme = this._theme.asReadonly();

  constructor() {
    this.applyToDocument(this._theme());
  }

  setTheme(theme: ThemeChoice): void {
    this._theme.set(theme);
    localStorage.setItem(STORAGE_KEY, theme);
    this.applyToDocument(theme);
  }

  private readStoredTheme(): ThemeChoice {
    const stored = localStorage.getItem(STORAGE_KEY);
    return isThemeChoice(stored) ? stored : 'system';
  }

  private applyToDocument(theme: ThemeChoice): void {
    const root = document.documentElement;
    for (const className of Object.values(THEME_CLASSES)) {
      if (className) {
        root.classList.remove(className);
      }
    }
    const className = THEME_CLASSES[theme];
    if (className) {
      root.classList.add(className);
    }
  }
}
