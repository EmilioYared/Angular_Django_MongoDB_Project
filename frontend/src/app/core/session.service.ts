import { Injectable, computed, signal } from '@angular/core';

import { AuthResponse, User, UserProfile } from './models';

const TOKEN_KEY = 'projectnest.token';
const USER_KEY = 'projectnest.user';
const PROFILE_KEY = 'projectnest.profile';

function readJson<T>(key: string): T | null {
  const raw = localStorage.getItem(key);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

@Injectable({ providedIn: 'root' })
export class SessionService {
  readonly token = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  readonly user = signal<User | null>(readJson<User>(USER_KEY));
  readonly profile = signal<UserProfile | null>(readJson<UserProfile>(PROFILE_KEY));
  readonly isAuthenticated = computed(() => Boolean(this.token()));

  setSession(response: AuthResponse): void {
    this.token.set(response.token);
    this.user.set(response.user);
    this.profile.set(response.profile);
    localStorage.setItem(TOKEN_KEY, response.token);
    localStorage.setItem(USER_KEY, JSON.stringify(response.user));
    localStorage.setItem(PROFILE_KEY, JSON.stringify(response.profile));
  }

  setProfile(user: User, profile: UserProfile | null): void {
    this.user.set(user);
    this.profile.set(profile);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  }

  clear(): void {
    this.token.set(null);
    this.user.set(null);
    this.profile.set(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(PROFILE_KEY);
  }
}
