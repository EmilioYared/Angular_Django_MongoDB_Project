# ProjectNest

Angular frontend + Django backend for an isolated-project knowledge helper.

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

## Unit tests

Run backend unit tests:

```powershell
.venv\Scripts\python backend\manage.py test api
```

Run frontend unit tests:

```powershell
cd frontend
npm test -- --watch=false
```

Optional sanity checks:

```powershell
.venv\Scripts\python backend\manage.py check
cd frontend
npm run build
```
