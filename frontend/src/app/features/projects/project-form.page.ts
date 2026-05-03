import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { getErrorMessage } from '../../core/error.util';
import { ProjectNestApiService } from '../../core/projectnest-api.service';

@Component({
  selector: 'app-project-form-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="page-section">
      <div class="hero-card">
        <h1>{{ editing() ? 'Edit project' : 'Create project' }}</h1>
        <p class="helper-text">Every document, chunk, embedding, and query stays scoped to one project.</p>
      </div>

      <div class="card">
        @if (error()) {
          <div class="error-banner">{{ error() }}</div>
        }

        <form class="field-grid" [formGroup]="form" (ngSubmit)="submit()">
          <label>
            Title
            <input type="text" formControlName="title" placeholder="Project title" />
          </label>

          <label>
            Description
            <textarea formControlName="description" placeholder="What does this project contain?"></textarea>
          </label>

          <label>
            Cover image
            <input type="file" accept="image/*" (change)="selectCover($event)" />
          </label>

          <div class="action-row">
            <button class="primary-button" type="submit" [disabled]="loading() || form.invalid">
              {{ loading() ? 'Saving...' : editing() ? 'Update project' : 'Create project' }}
            </button>
          </div>
        </form>
      </div>
    </section>
  `
})
export class ProjectFormPageComponent implements OnInit {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly api = inject(ProjectNestApiService);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly editing = signal(false);
  readonly form = this.fb.group({
    title: ['', [Validators.required, Validators.maxLength(120)]],
    description: ['']
  });

  private selectedCover: File | null = null;
  private projectId: string | null = null;

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      this.projectId = params.get('id');
      this.editing.set(Boolean(this.projectId));

      if (!this.projectId) {
        this.form.reset({
          title: '',
          description: ''
        });
        return;
      }

      this.api.getProject(this.projectId).subscribe({
        next: ({ project }) => {
          this.form.patchValue({
            title: project.title,
            description: project.description
          });
        },
        error: (error: unknown) => this.error.set(getErrorMessage(error))
      });
    });
  }

  selectCover(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.selectedCover = input.files?.[0] ?? null;
  }

  submit(): void {
    if (this.form.invalid || this.loading()) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = new FormData();
    const values = this.form.getRawValue();
    payload.append('title', values.title);
    payload.append('description', values.description);
    if (this.selectedCover) {
      payload.append('cover_image', this.selectedCover);
    }

    this.loading.set(true);
    this.error.set('');
    const request = this.projectId
      ? this.api.updateProject(this.projectId, payload)
      : this.api.createProject(payload);

    request.subscribe({
      next: ({ project }) => {
        this.loading.set(false);
        void this.router.navigate(['/projects', project.id]);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(getErrorMessage(error));
      }
    });
  }
}
