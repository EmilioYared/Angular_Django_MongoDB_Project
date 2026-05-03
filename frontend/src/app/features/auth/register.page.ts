import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { getErrorMessage } from '../../core/error.util';
import { ProjectNestApiService } from '../../core/projectnest-api.service';
import { SessionService } from '../../core/session.service';

@Component({
  selector: 'app-register-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  template: `
    <section class="page-section">
      <div class="hero-card">
        <h1>Create your ProjectNest account</h1>
        <p class="helper-text">Each account can own multiple isolated project workspaces.</p>
      </div>

      <div class="card" style="max-width: 38rem;">
        @if (error()) {
          <div class="error-banner">{{ error() }}</div>
        }

        <form class="field-grid" [formGroup]="form" (ngSubmit)="submit()">
          <div class="split-grid">
            <label>
              Full name
              <input type="text" formControlName="full_name" placeholder="Your name" />
            </label>

            <label>
              Username
              <input type="text" formControlName="username" placeholder="Unique username" />
              @if (form.controls.username.dirty || form.controls.username.touched) {
                @if (form.controls.username.hasError('required')) {
                  <span class="field-error">Username is required.</span>
                } @else if (form.controls.username.hasError('minlength')) {
                  <span class="field-error">Username must be at least 3 characters.</span>
                }
              }
            </label>
          </div>

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
            {{ loading() ? 'Creating account...' : 'Register' }}
          </button>
        </form>

        <p class="helper-text">Already registered? <a routerLink="/login">Sign in</a>.</p>
      </div>
    </section>
  `
})
export class RegisterPageComponent {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(ProjectNestApiService);
  private readonly session = inject(SessionService);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly form = this.fb.group({
    full_name: [''],
    username: ['', [Validators.required, Validators.minLength(3)]],
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
    this.api.register(this.form.getRawValue()).subscribe({
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
