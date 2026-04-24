import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { SessionService } from './session.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const session = inject(SessionService);
  const token = session.token();
  if (!token) {
    return next(req);
  }

  return next(
    req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    })
  );
};
