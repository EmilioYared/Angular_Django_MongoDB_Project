import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { API_BASE_URL } from './api.constants';
import {
  AuthResponse,
  DocumentRecord,
  DocumentsResponse,
  Project,
  ProjectDetailResponse,
  ProjectListResponse,
  ProjectMember,
  QueryHistoryResponse,
  SemanticSearchResponse,
  Tag,
  User,
  UserProfile
} from './models';

@Injectable({ providedIn: 'root' })
export class ProjectNestApiService {
  private readonly http = inject(HttpClient);

  register(payload: { username: string; email: string; password: string; full_name: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${API_BASE_URL}/auth/register/`, payload);
  }

  login(payload: { email: string; password: string }): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${API_BASE_URL}/auth/login/`, payload);
  }

  getProfile(): Observable<{ user: User; profile: UserProfile | null }> {
    return this.http.get<{ user: User; profile: UserProfile | null }>(`${API_BASE_URL}/profile/`);
  }

  updateProfile(payload: FormData): Observable<{ user: User; profile: UserProfile | null }> {
    return this.http.post<{ user: User; profile: UserProfile | null }>(`${API_BASE_URL}/profile/`, payload);
  }

  listProjects(q: string, order: string): Observable<ProjectListResponse> {
    return this.http.get<ProjectListResponse>(`${API_BASE_URL}/projects/`, {
      params: this.buildParams({ q, order })
    });
  }

  createProject(payload: FormData): Observable<{ project: Project }> {
    return this.http.post<{ project: Project }>(`${API_BASE_URL}/projects/`, payload);
  }

  getProject(projectId: string): Observable<ProjectDetailResponse> {
    return this.http.get<ProjectDetailResponse>(`${API_BASE_URL}/projects/${projectId}/`);
  }

  updateProject(projectId: string, payload: FormData): Observable<ProjectDetailResponse> {
    return this.http.post<ProjectDetailResponse>(`${API_BASE_URL}/projects/${projectId}/`, payload);
  }

  deleteProject(projectId: string): Observable<{ deleted: boolean }> {
    return this.http.delete<{ deleted: boolean }>(`${API_BASE_URL}/projects/${projectId}/`);
  }

  addMember(projectId: string, payload: { email: string; role: string }): Observable<{ member: ProjectMember }> {
    return this.http.post<{ member: ProjectMember }>(`${API_BASE_URL}/projects/${projectId}/members/`, payload);
  }

  deleteMember(projectId: string, memberId: string): Observable<{ deleted: boolean }> {
    return this.http.delete<{ deleted: boolean }>(`${API_BASE_URL}/projects/${projectId}/members/${memberId}/`);
  }

  addTag(projectId: string, payload: { name: string }): Observable<{ tag: Tag }> {
    return this.http.post<{ tag: Tag }>(`${API_BASE_URL}/projects/${projectId}/tags/`, payload);
  }

  deleteTag(projectId: string, tagId: string): Observable<{ deleted: boolean }> {
    return this.http.delete<{ deleted: boolean }>(`${API_BASE_URL}/projects/${projectId}/tags/${tagId}/`);
  }

  listDocuments(projectId: string, q: string, order: string): Observable<DocumentsResponse> {
    return this.http.get<DocumentsResponse>(`${API_BASE_URL}/projects/${projectId}/documents/`, {
      params: this.buildParams({ q, order })
    });
  }

  uploadDocument(projectId: string, payload: FormData): Observable<{ document: DocumentRecord }> {
    return this.http.post<{ document: DocumentRecord }>(`${API_BASE_URL}/projects/${projectId}/documents/`, payload);
  }

  deleteDocument(projectId: string, documentId: string): Observable<{ deleted: boolean }> {
    return this.http.delete<{ deleted: boolean }>(`${API_BASE_URL}/projects/${projectId}/documents/${documentId}/`);
  }

  semanticSearch(projectId: string, payload: { question: string; top_k: number }): Observable<SemanticSearchResponse> {
    return this.http.post<SemanticSearchResponse>(`${API_BASE_URL}/projects/${projectId}/semantic-search/`, payload);
  }

  queryHistory(projectId: string): Observable<QueryHistoryResponse> {
    return this.http.get<QueryHistoryResponse>(`${API_BASE_URL}/projects/${projectId}/query-history/`);
  }

  private buildParams(values: Record<string, string | number | null | undefined>): HttpParams {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(values)) {
      if (value !== null && value !== undefined && value !== '') {
        params = params.set(key, String(value));
      }
    }
    return params;
  }
}
