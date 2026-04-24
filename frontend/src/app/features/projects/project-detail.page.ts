import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { DocumentRecord, ProjectDetail } from '../../core/models';
import { getErrorMessage } from '../../core/error.util';
import { ProjectNestApiService } from '../../core/projectnest-api.service';

@Component({
  selector: 'app-project-detail-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <section class="page-section">
      @if (project(); as currentProject) {
        <div class="hero-card">
          <div class="title-row">
            <div class="stack">
              <div class="badge-row">
                <span class="badge info">{{ currentProject.access_role }}</span>
                <span class="badge success">Project isolation active</span>
              </div>
              <h1>{{ currentProject.title }}</h1>
              <p class="helper-text">{{ currentProject.description || 'No description yet.' }}</p>
              <div class="meta-row">
                <span>Owner: {{ currentProject.owner_email }}</span>
                <span>Created: {{ currentProject.created_at | date: 'medium' }}</span>
              </div>
            </div>

            <div class="action-row">
              <a class="secondary-button" [routerLink]="['/projects', currentProject.id, 'assistant']">Open assistant</a>
              <a class="primary-button" [routerLink]="['/projects', currentProject.id, 'documents', 'upload']">Upload document</a>
            </div>
          </div>

          <p class="empty-state">Searching inside this project only.</p>
        </div>

        @if (error()) {
          <div class="error-banner">{{ error() }}</div>
        }

        <div class="split-grid">
          <div class="panel">
            <h2>Tags</h2>
            @if (currentProject.tags.length > 0) {
              <div class="badge-row">
                @for (tag of currentProject.tags; track tag.id) {
                  <span class="badge">
                    {{ tag.name }}
                    @if (currentProject.access_role === 'owner') {
                      <button class="ghost-button" type="button" (click)="removeTag(tag.id)">×</button>
                    }
                  </span>
                }
              </div>
            } @else {
              <div class="empty-state">No tags attached yet.</div>
            }

            @if (currentProject.access_role === 'owner') {
              <form class="inline-form" [formGroup]="tagForm" (ngSubmit)="addTag()">
                <label>
                  Add tag
                  <input type="text" formControlName="name" placeholder="research" />
                </label>
                <button class="secondary-button" type="submit" [disabled]="tagForm.invalid">Add tag</button>
              </form>
            }
          </div>

          <div class="panel">
            <h2>Members</h2>
            @if (currentProject.members.length > 0) {
              <div class="stack">
                @for (member of currentProject.members; track member.id) {
                  <div class="card">
                    <div class="meta-row">
                      <strong>{{ member.username || member.email || 'Pending member' }}</strong>
                      <span class="badge">{{ member.role }}</span>
                    </div>
                    <div class="action-row">
                      <span class="helper-text">{{ member.email }}</span>
                      @if (currentProject.access_role === 'owner') {
                        <button class="danger-button" type="button" (click)="removeMember(member.id)">Remove</button>
                      }
                    </div>
                  </div>
                }
              </div>
            } @else {
              <div class="empty-state">No collaborators added yet.</div>
            }

            @if (currentProject.access_role === 'owner') {
              <form class="inline-form" [formGroup]="memberForm" (ngSubmit)="addMember()">
                <label>
                  Member email
                  <input type="email" formControlName="email" placeholder="member@example.com" />
                </label>
                <label>
                  Role
                  <select formControlName="role">
                    <option value="collaborator">Collaborator</option>
                    <option value="editor">Editor</option>
                  </select>
                </label>
                <button class="secondary-button" type="submit" [disabled]="memberForm.invalid">Add member</button>
              </form>
            }
          </div>
        </div>

        <div class="panel">
          <div class="title-row">
            <div>
              <h2>Documents</h2>
              <p class="helper-text">Uploaded files, extracted text, and semantic chunk status.</p>
            </div>
          </div>

          <form class="split-grid" [formGroup]="documentFilters">
            <label>
              Search documents
              <input type="text" formControlName="q" placeholder="Search by title" />
            </label>

            <label>
              Order
              <select formControlName="order">
                <option value="-uploaded_at">Newest upload</option>
                <option value="uploaded_at">Oldest upload</option>
                <option value="title">Title A-Z</option>
                <option value="-title">Title Z-A</option>
              </select>
            </label>
          </form>

          @if (documents().length === 0) {
            <div class="empty-state">No documents uploaded to this project yet.</div>
          } @else {
            <div class="stack">
              @for (document of documents(); track document.id) {
                <article class="card">
                  <div class="title-row">
                    <div class="stack">
                      <h3>{{ document.title }}</h3>
                      <div class="meta-row">
                        <span>{{ document.original_filename }}</span>
                        <span>{{ document.uploaded_at | date: 'medium' }}</span>
                        <span class="badge warn">{{ document.indexing_status }}</span>
                        <span class="badge info">{{ document.chunk_count }} chunks</span>
                      </div>
                    </div>
                    <div class="action-row">
                      @if (document.file_url) {
                        <a class="ghost-button" [href]="document.file_url" target="_blank" rel="noopener">Open file</a>
                      }
                      @if (currentProject.access_role === 'owner' || currentProject.access_role === 'editor') {
                        <button class="danger-button" type="button" (click)="deleteDocument(document)">Delete</button>
                      }
                    </div>
                  </div>
                  <p class="snippet">{{ document.excerpt || 'No preview available.' }}</p>
                </article>
              }
            </div>
          }
        </div>
      } @else {
        <div class="empty-state">Loading project...</div>
      }
    </section>
  `
})
export class ProjectDetailPageComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly api = inject(ProjectNestApiService);
  private readonly fb = inject(NonNullableFormBuilder);

  readonly project = signal<ProjectDetail | null>(null);
  readonly documents = signal<DocumentRecord[]>([]);
  readonly error = signal('');
  readonly memberForm = this.fb.group({
    email: ['', [Validators.required, Validators.email]],
    role: ['collaborator']
  });
  readonly tagForm = this.fb.group({
    name: ['', [Validators.required, Validators.maxLength(32)]]
  });
  readonly documentFilters = this.fb.group({
    q: [''],
    order: ['-uploaded_at']
  });

  private projectId = '';

  ngOnInit(): void {
    this.projectId = this.route.snapshot.paramMap.get('id') ?? '';
    this.loadProject();
    this.loadDocuments();
    this.documentFilters.valueChanges.subscribe(() => this.loadDocuments());
  }

  loadProject(): void {
    this.api.getProject(this.projectId).subscribe({
      next: ({ project }) => this.project.set(project),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }

  loadDocuments(): void {
    const { q, order } = this.documentFilters.getRawValue();
    this.api.listDocuments(this.projectId, q, order).subscribe({
      next: ({ documents }) => this.documents.set(documents),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }

  addMember(): void {
    if (this.memberForm.invalid) {
      this.memberForm.markAllAsTouched();
      return;
    }

    this.api.addMember(this.projectId, this.memberForm.getRawValue()).subscribe({
      next: () => {
        this.memberForm.reset({ email: '', role: 'collaborator' });
        this.loadProject();
      },
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }

  removeMember(memberId: string): void {
    this.api.deleteMember(this.projectId, memberId).subscribe({
      next: () => this.loadProject(),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }

  addTag(): void {
    if (this.tagForm.invalid) {
      this.tagForm.markAllAsTouched();
      return;
    }

    this.api.addTag(this.projectId, this.tagForm.getRawValue()).subscribe({
      next: () => {
        this.tagForm.reset({ name: '' });
        this.loadProject();
      },
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }

  removeTag(tagId: string): void {
    this.api.deleteTag(this.projectId, tagId).subscribe({
      next: () => this.loadProject(),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }

  deleteDocument(document: DocumentRecord): void {
    if (!confirm(`Delete "${document.title}" and all of its chunks and embeddings?`)) {
      return;
    }

    this.api.deleteDocument(this.projectId, document.id).subscribe({
      next: () => this.loadDocuments(),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }
}
