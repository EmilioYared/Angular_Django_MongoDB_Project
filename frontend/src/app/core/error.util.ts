import { HttpErrorResponse } from '@angular/common/http';

export function getErrorMessage(error: unknown): string {
  if (error instanceof HttpErrorResponse) {
    const apiMessage = (error.error as { error?: string } | null)?.error;
    return apiMessage || error.message || 'Request failed.';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Something went wrong.';
}
