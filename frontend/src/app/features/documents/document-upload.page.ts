import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { getErrorMessage } from '../../core/error.util';
import { ProjectNestApiService } from '../../core/projectnest-api.service';

@Component({
  selector: 'app-document-upload-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <section class="page-section">
      <div class="hero-card">
        <h1>Upload document</h1>
        <p class="helper-text">The uploaded content will be chunked, embedded, and indexed only inside this project.</p>
      </div>

      <div class="card">
        @if (error()) {
          <div class="error-banner">{{ error() }}</div>
        }

        <form class="field-grid" [formGroup]="form" (ngSubmit)="submit()">
          <label>
            Title
            <input type="text" formControlName="title" placeholder="Lecture notes" />
          </label>

          <label>
            Document type
            <select formControlName="document_type">
              <option value="pdf">PDF</option>
              <option value="text">Text</option>
            </select>
          </label>

          <label>
            Document file
            <input type="file" accept=".pdf,.txt,text/plain,application/pdf" (change)="selectDocument($event)" />
          </label>

          <label>
            Optional thumbnail image
            <input type="file" accept="image/*" (change)="selectThumbnail($event)" />
          </label>

          <button class="primary-button" type="submit" [disabled]="loading() || form.invalid || !documentFile">
            {{ loading() ? 'Uploading...' : 'Upload and index' }}
          </button>
        </form>
      </div>
    </section>
  `
})
export class DocumentUploadPageComponent implements OnInit {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(ProjectNestApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly form = this.fb.group({
    title: ['', [Validators.required, Validators.maxLength(120)]],
    document_type: ['pdf']
  });

  protected documentFile: File | null = null;
  private thumbnailFile: File | null = null;
  private projectId = '';

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      this.projectId = params.get('id') ?? '';
    });
  }

  selectDocument(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.documentFile = input.files?.[0] ?? null;
    if (this.documentFile && !this.form.getRawValue().title) {
      this.form.patchValue({ title: this.documentFile.name });
    }
  }

  selectThumbnail(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.thumbnailFile = input.files?.[0] ?? null;
  }

  submit(): void {
    if (this.form.invalid || !this.documentFile || this.loading() || !this.projectId) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = new FormData();
    const values = this.form.getRawValue();
    payload.append('title', values.title);
    payload.append('document_type', values.document_type);
    payload.append('document', this.documentFile);
    if (this.thumbnailFile) {
      payload.append('thumbnail_image', this.thumbnailFile);
    }

    this.loading.set(true);
    this.error.set('');
    this.api.uploadDocument(this.projectId, payload).subscribe({
      next: () => {
        this.loading.set(false);
        void this.router.navigate(['/projects', this.projectId]);
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(getErrorMessage(error));
      }
    });
  }
}
