import { Routes } from '@angular/router';

import { authGuard, guestGuard } from './core/auth.guards';
import { AssistantPageComponent } from './features/assistant/assistant.page';
import { LoginPageComponent } from './features/auth/login.page';
import { RegisterPageComponent } from './features/auth/register.page';
import { DocumentUploadPageComponent } from './features/documents/document-upload.page';
import { ProfilePageComponent } from './features/profile/profile.page';
import { ProjectDetailPageComponent } from './features/projects/project-detail.page';
import { ProjectFormPageComponent } from './features/projects/project-form.page';
import { ProjectsPageComponent } from './features/projects/projects.page';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'projects' },
  { path: 'login', component: LoginPageComponent, canActivate: [guestGuard] },
  { path: 'register', component: RegisterPageComponent, canActivate: [guestGuard] },
  { path: 'profile', component: ProfilePageComponent, canActivate: [authGuard] },
  { path: 'projects', component: ProjectsPageComponent, canActivate: [authGuard] },
  { path: 'projects/new', component: ProjectFormPageComponent, canActivate: [authGuard] },
  { path: 'projects/:id', component: ProjectDetailPageComponent, canActivate: [authGuard] },
  { path: 'projects/:id/edit', component: ProjectFormPageComponent, canActivate: [authGuard] },
  { path: 'projects/:id/documents/upload', component: DocumentUploadPageComponent, canActivate: [authGuard] },
  { path: 'projects/:id/assistant', component: AssistantPageComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'projects' }
];
