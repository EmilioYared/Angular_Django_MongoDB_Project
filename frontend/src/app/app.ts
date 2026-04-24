import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { ProjectNestApiService } from './core/projectnest-api.service';
import { SessionService } from './core/session.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  protected readonly session = inject(SessionService);
  private readonly api = inject(ProjectNestApiService);
  private readonly router = inject(Router);

  ngOnInit(): void {
    if (this.session.token() && !this.session.user()) {
      this.api.getProfile().subscribe({
        next: ({ user, profile }) => this.session.setProfile(user, profile),
        error: () => this.session.clear()
      });
    }
  }

  protected logout(): void {
    this.session.clear();
    void this.router.navigate(['/login']);
  }
}
