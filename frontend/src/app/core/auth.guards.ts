import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { SessionService } from './session.service';

export const authGuard: CanActivateFn = () => {
  const session = inject(SessionService);
  const router = inject(Router);
  return session.isAuthenticated() ? true : router.createUrlTree(['/login']);
};

export const guestGuard: CanActivateFn = () => {
  const session = inject(SessionService);
  const router = inject(Router);
  return session.isAuthenticated() ? router.createUrlTree(['/projects']) : true;
};
