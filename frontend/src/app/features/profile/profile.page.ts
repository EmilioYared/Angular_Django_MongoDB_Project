import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { getErrorMessage } from '../../core/error.util';
import { ProjectNestApiService } from '../../core/projectnest-api.service';
import { SessionService } from '../../core/session.service';

@Component({
  selector: 'app-profile-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="page-section">
      <div class="hero-card">
        <h1>Your profile</h1>
        <p class="helper-text">Update identity details and your profile picture.</p>
      </div>

      <div class="split-grid">
        <div class="card">
          @if (success()) {
            <div class="empty-state">{{ success() }}</div>
          }
          @if (error()) {
            <div class="error-banner">{{ error() }}</div>
          }

          <form class="field-grid" [formGroup]="form" (ngSubmit)="submit()">
            <label>
              Username
              <input type="text" formControlName="username" />
            </label>

            <label>
              Full name
              <input type="text" formControlName="full_name" />
            </label>

            <label>
              Profile email
              <input type="email" formControlName="profile_email" />
            </label>

            <label>
              Profile image
              <input type="file" accept="image/*" (change)="selectImage($event)" />
            </label>

            <button class="primary-button" type="submit" [disabled]="loading() || form.invalid">
              {{ loading() ? 'Saving...' : 'Save profile' }}
            </button>
          </form>
        </div>

        <div class="card">
          <h2>Current preview</h2>
          <div class="stack">
            @if (session.profile()?.profile_image_url) {
              <img
                [src]="session.profile()?.profile_image_url || ''"
                alt="Profile image"
                style="width: 9rem; height: 9rem; border-radius: 1.2rem; object-fit: cover;"
              />
            } @else {
              <div class="empty-state">No profile image uploaded yet.</div>
            }
            <div class="meta-row">
              <span>{{ session.user()?.username }}</span>
              <span>{{ session.profile()?.profile_email }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  `
})
export class ProfilePageComponent implements OnInit {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(ProjectNestApiService);
  protected readonly session = inject(SessionService);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly success = signal('');
  readonly form = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(3)]],
    full_name: [''],
    profile_email: ['', [Validators.required, Validators.email]]
  });

  private selectedImage: File | null = null;

  ngOnInit(): void {
    const user = this.session.user();
    const profile = this.session.profile();
    if (user && profile) {
      this.form.patchValue({
        username: user.username,
        full_name: profile.full_name,
        profile_email: profile.profile_email
      });
      return;
    }

    this.api.getProfile().subscribe({
      next: ({ user: currentUser, profile: currentProfile }) => {
        this.session.setProfile(currentUser, currentProfile);
        this.form.patchValue({
          username: currentUser.username,
          full_name: currentProfile?.full_name ?? '',
          profile_email: currentProfile?.profile_email ?? currentUser.email
        });
      },
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }

  selectImage(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedImage = input.files?.[0] ?? null;
  }

  submit(): void {
    if (this.form.invalid || this.loading()) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = new FormData();
    const values = this.form.getRawValue();
    payload.append('username', values.username);
    payload.append('full_name', values.full_name);
    payload.append('profile_email', values.profile_email);
    if (this.selectedImage) {
      payload.append('profile_image', this.selectedImage);
    }

    this.loading.set(true);
    this.error.set('');
    this.success.set('');
    this.api.updateProfile(payload).subscribe({
      next: ({ user, profile }) => {
        this.session.setProfile(user, profile);
        this.success.set('Profile updated.');
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.error.set(getErrorMessage(error));
        this.loading.set(false);
      }
    });
  }
}
