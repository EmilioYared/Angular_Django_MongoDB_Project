import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { getErrorMessage } from '../../core/error.util';
import { ProjectNestApiService } from '../../core/projectnest-api.service';
import { SessionService } from '../../core/session.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <section class="page-section">
      <div class="hero-card">
        <h1>Welcome back</h1>
        <p class="helper-text">Sign in to manage isolated project workspaces and semantic search.</p>
      </div>

      <div class="card" style="max-width: 32rem;">
        @if (error()) {
          <div class="error-banner">{{ error() }}</div>
        }

        <form class="field-grid" [formGroup]="form" (ngSubmit)="submit()">
          <label>
            Email
            <input type="email" formControlName="email" placeholder="name@example.com" />
            @if (form.controls.email.dirty || form.controls.email.touched) {
              @if (form.controls.email.hasError('required')) {
                <span class="field-error">Email is required.</span>
              } @else if (form.controls.email.hasError('email')) {
                <span class="field-error">Enter a valid email address.</span>
              }
            }
          </label>

          <label>
            Password
            <input type="password" formControlName="password" placeholder="At least 8 characters" />
            @if (form.controls.password.dirty || form.controls.password.touched) {
              @if (form.controls.password.hasError('required')) {
                <span class="field-error">Password is required.</span>
              } @else if (form.controls.password.hasError('minlength')) {
                <span class="field-error">Password must be at least 8 characters.</span>
              }
            }
          </label>

          <button class="primary-button" type="submit" [disabled]="loading() || form.invalid">
            {{ loading() ? 'Signing in...' : 'Login' }}
          </button>
        </form>

        <p class="helper-text">No account yet? <a routerLink="/register">Create one</a>.</p>
      </div>
    </section>
  `
})
export class LoginPageComponent {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(ProjectNestApiService);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly form = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', [Validators.required, Validators.minLength(8)]]
  });

  submit(): void {
    if (this.form.invalid || this.loading()) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.error.set('');
    this.api.login(this.form.getRawValue()).subscribe({
      next: (response) => {
        this.session.setSession(response);
        this.loading.set(false);
        void this.router.navigate(['/projects']);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(getErrorMessage(error));
      }
    });
  }
}
