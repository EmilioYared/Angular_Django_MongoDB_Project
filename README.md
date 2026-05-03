# ProjectNest

Angular frontend + Django backend for an isolated-project knowledge helper.

## Core architecture

- Every project is its own workspace.
- Documents, chunks, embeddings, semantic queries, members, and conversations all carry `project_id`.
- Semantic search always filters by `project_id` before scoring.
- Deleting a document removes its chunks and embeddings.
- Deleting a project removes nested documents, chunks, embeddings, query logs, members, and conversations.

## Stack

- Frontend: Angular standalone app with routing and reactive forms
- Backend: Django API with JWT auth and MongoDB Atlas via `pymongo`
- Semantic search: chunk embeddings stored in MongoDB and scored per project
- File handling: MongoDB Atlas GridFS storage for profile images, project covers, thumbnails, and uploaded files

## Local run

Backend:

```powershell
.venv\Scripts\python backend\manage.py runserver
```

Frontend:

```powershell
cd frontend
npm start
```

Frontend default URL: `http://localhost:4200`

Backend default URL: `http://localhost:8000`

LAN testing with another device:

```powershell
.venv\Scripts\python backend\manage.py runserver 0.0.0.0:8000
```

```powershell
cd frontend
npm start -- --host 0.0.0.0
```

Then open `http://YOUR_COMPUTER_IP:4200` on the other device. Do not use `localhost` from the other device, because that points to the other device itself.

## Verified

- `python backend/manage.py check`
- `npm run build` inside `frontend`
- Backend smoke path:
  - health
  - register
  - create project
  - project-scoped semantic search

## Key API routes

- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `GET|POST /api/profile/`
- `GET|POST /api/projects/`
- `GET|POST|DELETE /api/projects/:projectId/`
- `GET|POST /api/projects/:projectId/members/`
- `GET|POST /api/projects/:projectId/tags/`
- `GET|POST /api/projects/:projectId/documents/`
- `POST /api/projects/:projectId/semantic-search/`
- `GET /api/projects/:projectId/query-history/`
- `GET /api/files/:fileId/`
