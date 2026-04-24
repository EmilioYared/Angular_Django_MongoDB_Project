import { CommonModule, DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';

import { ProjectDetail, QueryLog, SemanticMatch } from '../../core/models';
import { getErrorMessage } from '../../core/error.util';
import { ProjectNestApiService } from '../../core/projectnest-api.service';

@Component({
  selector: 'app-assistant-page',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, DatePipe],
  template: `
    <section class="page-section">
      <div class="hero-card">
        <h1>Project assistant</h1>
        <p class="helper-text">
          @if (project()) {
            Searching inside <strong>{{ project()?.title }}</strong> only.
          } @else {
            Searching inside this project only.
          }
        </p>
      </div>

      <div class="split-grid">
        <div class="card">
          @if (error()) {
            <div class="error-banner">{{ error() }}</div>
          }

          <form class="field-grid" [formGroup]="form" (ngSubmit)="submit()">
            <label>
              Question
              <textarea formControlName="question" placeholder="What does this project say about semantic isolation?"></textarea>
            </label>

            <label>
              Top matches
              <select formControlName="top_k">
                <option [value]="3">3</option>
                <option [value]="5">5</option>
                <option [value]="8">8</option>
              </select>
            </label>

            <button class="primary-button" type="submit" [disabled]="loading() || form.invalid">
              {{ loading() ? 'Searching...' : 'Run semantic search' }}
            </button>
          </form>
        </div>

        <div class="card">
          <h2>Recent project queries</h2>
          @if (history().length === 0) {
            <div class="empty-state">No semantic queries logged for this project yet.</div>
          } @else {
            <div class="stack">
              @for (entry of history(); track entry.id) {
                <div class="card">
                  <strong>{{ entry.query_text }}</strong>
                  <div class="meta-row">
                    <span>top {{ entry.top_k }}</span>
                    <span>{{ entry.created_at | date: 'short' }}</span>
                  </div>
                </div>
              }
            </div>
          }
        </div>
      </div>

      <div class="panel">
        <h2>Results</h2>
        @if (info()) {
          <div class="empty-state">{{ info() }}</div>
        }
        @if (answer()) {
          <div class="card">
            <h3>Grounded answer</h3>
            <p class="snippet">{{ answer() }}</p>
          </div>
        }
        @if (matches().length === 0) {
          <p class="helper-text">Ask a question to retrieve the most relevant project chunks.</p>
        } @else {
          <div class="stack">
            @for (match of matches(); track match.chunk_id) {
              <article class="card">
                <div class="title-row">
                  <div class="stack">
                    <strong>{{ match.document_title }}</strong>
                    <div class="meta-row">
                      <span class="score-pill">Score {{ match.score }}</span>
                      <span>Chunk {{ match.chunk_index }}</span>
                      <span>{{ match.model_name }}</span>
                    </div>
                  </div>
                </div>
                <p class="snippet">{{ match.snippet }}</p>
              </article>
            }
          </div>
        }
      </div>
    </section>
  `
})
export class AssistantPageComponent implements OnInit {
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly api = inject(ProjectNestApiService);
  private readonly route = inject(ActivatedRoute);

  readonly loading = signal(false);
  readonly error = signal('');
  readonly info = signal('Searching inside this project only.');
  readonly answer = signal('');
  readonly matches = signal<SemanticMatch[]>([]);
  readonly history = signal<QueryLog[]>([]);
  readonly project = signal<ProjectDetail | null>(null);
  readonly form = this.fb.group({
    question: ['', [Validators.required, Validators.minLength(4)]],
    top_k: [5]
  });

  private readonly projectId = this.route.snapshot.paramMap.get('id') ?? '';

  ngOnInit(): void {
    this.api.getProject(this.projectId).subscribe({
      next: ({ project }) => this.project.set(project),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
    this.refreshHistory();
  }

  submit(): void {
    if (this.form.invalid || this.loading()) {
      this.form.markAllAsTouched();
      return;
    }

    this.loading.set(true);
    this.error.set('');
    this.info.set('Searching inside this project only.');
    this.answer.set('');
    this.api.semanticSearch(this.projectId, this.form.getRawValue()).subscribe({
      next: (response) => {
        this.matches.set(response.matches);
        this.answer.set(response.generated_answer ?? '');
        this.info.set(response.message);
        this.loading.set(false);
        this.refreshHistory();
      },
      error: (error: unknown) => {
        this.loading.set(false);
        this.error.set(getErrorMessage(error));
      }
    });
  }

  private refreshHistory(): void {
    this.api.queryHistory(this.projectId).subscribe({
      next: ({ queries }) => this.history.set(queries),
      error: (error: unknown) => this.error.set(getErrorMessage(error))
    });
  }
}
