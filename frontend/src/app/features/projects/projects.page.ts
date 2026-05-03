import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { getErrorMessage } from '../../core/error.util';
import { Project } from '../../core/models';
import { ProjectNestApiService } from '../../core/projectnest-api.service';

@Component({
  selector: 'app-projects-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, DatePipe],
  template: `
    <section class="page-section">
      <div class="hero-card">
        <div class="title-row">
          <div>
            <h1>Projects</h1>
            <p class="helper-text">
              Create isolated workspaces for documents, chats, and semantic search.
            </p>
          </div>
          <div class="action-row">
            <a class="primary-button" routerLink="/projects/new">Create project</a>
          </div>
        </div>
      </div>

      <div class="panel">
        <form class="split-grid" [formGroup]="filters">
          <label>
            Search projects
            <input type="text" formControlName="q" placeholder="Search by title" />
          </label>

          <label>
            Order by
            <select formControlName="order">
              <option value="-created_at">Newest first</option>
              <option value="created_at">Oldest first</option>
              <option value="title">Title A-Z</option>
              <option value="-title">Title Z-A</option>
            </select>
          </label>
        </form>
      </div>

      @if (error()) {
        <div class="error-banner">{{ error() }}</div>
      }

      @if (!loading() && projects().length === 0) {
        <div class="empty-state">No projects found yet.</div>
      }

      <div class="list-grid">
        @for (project of projects(); track project.id) {
          <article class="card">
            @if (project.cover_image_url) {
              <img class="project-cover" [src]="project.cover_image_url" [alt]="project.title + ' cover image'" />
            }

            <div class="meta-row">
              <span class="badge info">{{ project.access_role }}</span>
              <span>{{ project.created_at | date: 'mediumDate' }}</span>
            </div>

            <h2>{{ project.title }}</h2>
            <p class="helper-text">{{ project.description || 'No description yet.' }}</p>

            @if (project.tags.length > 0) {
              <div class="badge-row">
                @for (tag of project.tags; track tag.id) {
                  <span class="badge">{{ tag.name }}</span>
                }
              </div>
            }

            <div class="meta-row">
              <span>{{ project.members_count }} collaborators</span>
              <span>{{ project.tags.length }} tags</span>
            </div>

            <div class="action-row">
              <a class="secondary-button" [routerLink]="['/projects', project.id]">Open</a>
              @if (project.access_role === 'owner') {
                <a class="ghost-button" [routerLink]="['/projects', project.id, 'edit']">Edit</a>
                <button class="danger-button" type="button" (click)="deleteProject(project)">Delete</button>
              }
            </div>
          </article>
        }
      </div>
    </section>
  `
})
export class ProjectsPageComponent implements OnInit {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(ProjectNestApiService);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly projects = signal<Project[]>([]);
  readonly filters = this.fb.group({
    q: [''],
    order: ['-created_at']
  });

  ngOnInit(): void {
    this.loadProjects();
    this.filters.valueChanges.subscribe(() => this.loadProjects());
  }

  loadProjects(): void {
    this.loading.set(true);
    this.error.set('');
    const { q, order } = this.filters.getRawValue();
    this.api.listProjects(q, order).subscribe({
      next: ({ projects }) => {
        this.projects.set(projects);
        this.loading.set(false);
      },
      error: (error: unknown) => {
        this.error.set(getErrorMessage(error));
        this.loading.set(false);
      }
    });
  }

  deleteProject(project: Project): void {
    if (!confirm(`Delete "${project.title}" and all nested documents, chunks, embeddings, and query history?`)) {
      return;
    }

    this.api.deleteProject(project.id).subscribe({
      next: () => this.loadProjects(),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }
}
